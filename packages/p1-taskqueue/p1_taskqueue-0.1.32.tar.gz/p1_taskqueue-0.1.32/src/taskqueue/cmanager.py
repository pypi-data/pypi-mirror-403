import base64
import logging
import pickle
import uuid
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from celery import shared_task
from celery.exceptions import Reject
from taskqueue.slack_notifier import SlackbotManager

# Setup logger
logger = logging.getLogger(__name__)

# Enqueue operation type constants
K_ENQUEUE_OP_TYPE_ENQUEUE = 'enqueue'
K_ENQUEUE_OP_TYPE_ENQUEUE_AT = 'enqueue_at'
K_ENQUEUE_OP_TYPE_ENQUEUE_IN = 'enqueue_in'

K_MAX_RETRY_COUNT = 2
K_DEFAULT_RETRY_COUNTDOWN = 3600
K_TASK_STATUS_REPUBLISHED = 'FAILURE - REPUBLISHED'
K_TASK_STATUS_FAILURE = 'FAILURE'
K_TASK_STATUS_PENDING = 'PENDING'
K_TASK_QUEUE_NAME_DEFAULT = 'default'
K_CELERY_OPTION_TIME_LIMIT = 'time_limit'


def taskqueue_class(cls):
    """Decorator to automatically capture init arguments for taskqueue."""
    original_init = cls.__init__

    def wrapped_init(self, *args, **kwargs):
        self._taskqueue_init_args = list(args)
        self._taskqueue_init_kwargs = dict(kwargs)
        original_init(self, *args, **kwargs)

    cls.__init__ = wrapped_init
    return cls


def _split_function_and_queue_kwargs(kwargs: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # To prevent confusion whether a kwargs is for function or queue kwargs(i.e celery options and on_commit),
    # ignore confusing kwargs while give warning
    supported_queue_keys = {"channel", "retry",
                            "on_commit", "job_timeout", "use_legacy_executor"}
    ignored_non_function_keys = {
        "queue", "countdown", "eta", "expires", "priority", "task_id", "routing_key",
        "serializer", "compression", "headers", "link", "link_error", "retry_policy",
        "shadow", "time_limit", "soft_time_limit", "reply_to", "group_id", "chord", "chain",
        "result_ttl", "failure_ttl", "ttl", "depends_on", "at_front", "meta", "retry_count",
    }

    queue_kwargs: Dict[str, Any] = {}
    func_kwargs: Dict[str, Any] = {}

    for key, value in kwargs.items():
        if key in supported_queue_keys:
            queue_kwargs[key] = value
        elif key in ignored_non_function_keys:
            logger.warning(
                f"[CManager] Unsupported celery args detected: {key}. Ignored.")
            continue
        else:
            func_kwargs[key] = value

    return func_kwargs, queue_kwargs


def _build_callable_task_call(func: Any, func_args: tuple, func_kwargs: dict) -> Tuple[str, list, dict]:
    task_name = "taskqueue.cmanager.callable_executor"
    task_args = []
    task_kwargs = {
        "callable_obj": func,
        "args": list(func_args),
        "kwargs": dict(func_kwargs),
    }
    return task_name, task_args, task_kwargs


class CManager:

    def __init__(self) -> None:
        pass

    def republish_task(self, task_id: str, force: bool = False) -> str:
        from django.db import transaction
        from taskqueue.models import TaskReconstruction
        try:
            task_recon = TaskReconstruction.objects.get(task_id=task_id)
        except TaskReconstruction.DoesNotExist:
            raise ValueError(f"Task with ID {task_id} not found")

        if not force:
            self._validate_task_for_republish(task_id)

        task_name = task_recon.task_name
        task_args = self._unpickle_data(task_recon.task_args)
        task_kwargs = self._unpickle_data(task_recon.task_kwargs)

        queue_name, job_timeout, retry_policy, countdown, eta = self._prepare_queue_options_from_reconstruction(
            task_recon)
        queue_options = task_recon.queue_options

        with transaction.atomic():
            new_task_id = self._create_task_result(task_name, task_args, task_kwargs,
                                                   queue_name, job_timeout, retry_policy, countdown, eta)

            return self._send_task(task_name, task_args, task_kwargs, queue_options, new_task_id)

    def enqueue(self, *args: Any, **kwargs: Any) -> None:
        self._enqueue_op(
            *args, enqueue_op_type=K_ENQUEUE_OP_TYPE_ENQUEUE, **kwargs)

    def enqueue_at(self, *args: Any, **kwargs: Any) -> None:
        self._enqueue_op(
            *args, enqueue_op_type=K_ENQUEUE_OP_TYPE_ENQUEUE_AT, **kwargs)

    def enqueue_in(self, *args: Any, **kwargs: Any) -> None:
        self._enqueue_op(
            *args, enqueue_op_type=K_ENQUEUE_OP_TYPE_ENQUEUE_IN, **kwargs)

    def _get_celery_app(self) -> Any:
        """Get the auto-configured Celery app instance."""
        from .celery_app import celery_app
        return celery_app

    def _validate_task_for_republish(self, task_id: str) -> Any:
        try:
            from django_celery_results.models import TaskResult
            from django.utils import timezone
            task_result = TaskResult.objects.filter(task_id=task_id).first()
            if not task_result:
                raise ValueError(
                    f"Task with ID {task_id} not found in TaskResult. Cannot republish task without TaskResult.")
            if task_result.status != K_TASK_STATUS_FAILURE:
                raise ValueError(
                    f"Task with ID {task_id} cannot be republished. Only tasks with status '{K_TASK_STATUS_FAILURE}' can be republished. Current status: {task_result.status}")

            TaskResult.objects.filter(task_id=task_id).update(
                status=K_TASK_STATUS_REPUBLISHED,
                date_done=timezone.now(),
            )
            return task_result
        except ImportError:
            raise ImportError(
                "django_celery_results is required for republishing tasks")
        except Exception as e:
            logger.warning(f"[CManager] Failed to update old task status: {e}")
            raise

    def _prepare_queue_options_from_reconstruction(self, task_recon: Any) -> Tuple[str, Optional[int], Optional[dict], Optional[int], Optional[datetime]]:

        queue_options = task_recon.queue_options.copy()

        eta = queue_options.get("eta")
        if eta and isinstance(eta, str):
            queue_options["eta"] = datetime.fromisoformat(
                eta.replace('Z', '+00:00'))
            eta = queue_options["eta"]

        queue_name = queue_options.get("channel")
        job_timeout = queue_options.get("job_timeout")
        retry_policy = queue_options.get("retry")
        countdown = queue_options.get("countdown")

        return queue_name, job_timeout, retry_policy, countdown, eta

    def _enqueue_op(self, *args: Any, **kwargs: Any) -> None:
        on_commit = kwargs.pop('on_commit', False)
        if on_commit:
            try:
                from django.db import transaction
                transaction.on_commit(
                    lambda: self._enqueue_op_base(*args, **kwargs))
            except ImportError:
                raise RuntimeError(
                    "Django is not installed. Please install Django to use on_commit.")
        else:
            self._enqueue_op_base(*args, **kwargs)

    def _enqueue_op_base(self, *args: Any, **kwargs: Any) -> None:
        enqueue_op_type = kwargs.pop(
            'enqueue_op_type', K_ENQUEUE_OP_TYPE_ENQUEUE)

        try:
            func, func_args, func_kwargs, queue_options = self._parse_enqueue_args(
                enqueue_op_type, args, kwargs)

            task_name, task_args, task_kwargs = _build_callable_task_call(
                func, func_args, func_kwargs)

            queue_name = queue_options.get(
                "channel", K_TASK_QUEUE_NAME_DEFAULT)
            job_timeout = queue_options.get("job_timeout")
            retry_policy = queue_options.get("retry")
            countdown = queue_options.get("countdown")
            eta = queue_options.get("eta")

            from django.db import transaction
            with transaction.atomic():
                task_id = self._create_task_result(task_name, task_args, task_kwargs,
                                                   queue_name, job_timeout, retry_policy, countdown, eta)

                task_id = self._send_task(task_name, task_args,
                                          task_kwargs, queue_options, task_id)

            logger.info(
                f'[_enqueue_op_base {enqueue_op_type}] Submit Celery Task SUCCESS, task_name: {task_name} args: {task_args}, kwargs: {task_kwargs}, task_id: {task_id}')

        except Exception as e:
            logger.exception(
                f'[_enqueue_op_base {enqueue_op_type}] Submit Celery Task FAILED, error: {str(e)}, args: {args}, kwargs: {kwargs}')
            raise e

    def _parse_enqueue_args(self, enqueue_op_type: str, args: tuple, kwargs: dict) -> Tuple[Any, tuple, dict, dict]:
        """Parse enqueue arguments and return func, func_args, func_kwargs, and queue_options."""
        if enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE:
            if not args:
                raise ValueError(
                    "enqueue requires a callable as the first positional argument")
            func = args[0]
            func_args = args[1:]
            eta, delta = None, None

        elif enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE_AT:
            if len(args) < 2:
                raise ValueError(
                    "enqueue_at requires (eta_datetime, func, *func_args)")
            eta = args[0]
            func = args[1]
            func_args = args[2:]
            delta = None

        elif enqueue_op_type == K_ENQUEUE_OP_TYPE_ENQUEUE_IN:
            if len(args) < 2:
                raise ValueError(
                    "enqueue_in requires (countdown_delta, func, *func_args)")
            delta = args[0]
            func = args[1]
            func_args = args[2:]
            eta = None
        else:
            raise ValueError(
                f"Unknown enqueue operation type: {enqueue_op_type}")

        func_kwargs, queue_options = _split_function_and_queue_kwargs(kwargs)

        if eta is not None:
            queue_options["eta"] = eta
        elif delta is not None:
            queue_options["countdown"] = int(delta.total_seconds())

        return func, func_args, func_kwargs, queue_options

    def _pickle_data(self, data: Any) -> str:
        """Pickle data and return as base64-encoded string."""
        pickled = pickle.dumps(data)
        return base64.b64encode(pickled).decode('utf-8')

    def _unpickle_data(self, data: str) -> Any:
        """Unpickle base64-encoded pickled string."""
        pickled = base64.b64decode(data.encode('utf-8'))
        return pickle.loads(pickled)

    def _create_task_result(self, task_name: str, task_args: list, task_kwargs: dict,
                            queue_name: str, job_timeout: Optional[int] = None, retry_policy: Optional[dict] = None, countdown: Optional[int] = None, eta: Optional[datetime] = None) -> str:

        callable_obj = task_kwargs["callable_obj"]
        callable_name_meta = getattr(
            callable_obj, '__name__', str(callable_obj))

        task_id = str(uuid.uuid4())

        task_result_obj = None
        try:
            from django_celery_results.models import TaskResult
            from django.utils import timezone

            task_result_obj = TaskResult.objects.create(
                task_id=task_id,
                task_name=task_name,
                status=K_TASK_STATUS_PENDING,
                date_created=timezone.now(),
                date_done=timezone.now(),
            )
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"[CManager] Failed to create TaskResult: {e}")

        try:
            from taskqueue.models import TaskReconstruction

            pickled_task_args = self._pickle_data(task_args)
            pickled_task_kwargs = self._pickle_data(task_kwargs)

            if task_result_obj is None:
                raise ValueError(
                    f"Failed to create TaskResult for task id: {task_id}")

            TaskReconstruction.objects.create(
                task_result=task_result_obj,
                task_id=task_id,
                task_name=task_name,
                task_args=pickled_task_args,
                task_kwargs=pickled_task_kwargs,
                queue_options={
                    "channel": queue_name,
                    "job_timeout": job_timeout,
                    "retry": retry_policy,
                    "countdown": countdown,
                    "eta": eta.isoformat() if eta else None,
                },
                channel=queue_name,
                callable_name_meta=callable_name_meta,
            )
        except ImportError:
            pass
        except Exception as e:
            logger.warning(
                f"[CManager] Failed to create TaskReconstruction: {e}")

        return task_id

    def _send_task(self, task_name: str, task_args: list, task_kwargs: dict, queue_kwargs: Dict[str, Any], task_id: str = None) -> str:
        celery_app = self._get_celery_app()

        queue_name = queue_kwargs.pop("channel", None)
        job_timeout = queue_kwargs.pop("job_timeout", None)
        retry_policy = queue_kwargs.pop("retry", None)
        countdown = queue_kwargs.pop("countdown", None)
        eta = queue_kwargs.pop("eta", None)

        created_at = datetime.now().isoformat()

        send_opts: Dict[str, Any] = {
            "headers": {
                "created_at": created_at
            }
        }
        if queue_name:
            send_opts["queue"] = queue_name
        if job_timeout is not None:
            send_opts[K_CELERY_OPTION_TIME_LIMIT] = job_timeout
        if countdown is not None:
            send_opts["countdown"] = countdown
        if eta is not None:
            send_opts["eta"] = eta

        task_kwargs_with_retry = dict(task_kwargs)
        if retry_policy is None:
            task_kwargs_with_retry["retry"] = {
                "max_retries": K_MAX_RETRY_COUNT, "countdown": K_DEFAULT_RETRY_COUNTDOWN}
        else:
            task_kwargs_with_retry["retry"] = retry_policy

        if task_id:
            send_opts["task_id"] = task_id

        task = celery_app.send_task(task_name, args=task_args,
                                    kwargs=task_kwargs_with_retry, **send_opts)

        return str(task.id)


cm = CManager()


@shared_task(bind=True, max_retries=K_MAX_RETRY_COUNT, acks_late=True, reject_on_worker_lost=True)
def callable_executor(self, callable_obj: Optional[Any] = None, args: Optional[list] = None, kwargs: Optional[dict] = None, retry: Optional[dict] = None) -> None:
    job_id = self.request.id
    try:
        args = args or []
        kwargs = kwargs or {}
        callable_name = getattr(callable_obj, '__name__', str(callable_obj))

        logger.info(
            f"[TaskQueue] Executing callable: {callable_name} with args: {args} and kwargs: {kwargs}, job_id: {job_id}")

        callable_obj(*args, **kwargs)

        logger.info(
            f"[TaskQueue] Callable execution completed successfully, callable: {callable_name}, args: {args}, kwargs: {kwargs}, job_id: {job_id}")
        return None
    except Exception as e:
        logger.exception(
            f"[TaskQueue] Error executing callable: {callable_name}, args: {args}, kwargs: {kwargs}, error_class: {e.__class__.__name__}, error: {e}, job_id: {job_id}")

        current_retries = getattr(self.request, 'retries', 0) or 0
        max_retries = self.max_retries or K_MAX_RETRY_COUNT
        if isinstance(retry, dict) and 'max_retries' in retry:
            max_retries = retry['max_retries']

        if current_retries >= max_retries:
            logger.error(
                f"[TaskQueue] Max retries ({max_retries}) reached for callable: {callable_name}, job_id: {job_id}")
            self.update_state(state='FAILURE', meta={
                              'exc_type': type(e).__name__, 'exc_message': str(e)})

            SlackbotManager.send_message(
                f"Job Failed Too Many Times - Moving back to dlq.\n"
                f"function name: {callable_name}\n"
                f"args: {args}\n"
                f"kwargs: {kwargs}"
            )

            raise Reject(reason=str(e), requeue=False)

        countdown = K_DEFAULT_RETRY_COUNTDOWN
        if isinstance(retry, dict) and 'countdown' in retry:
            countdown = retry['countdown']

        raise self.retry(exc=e, countdown=countdown, max_retries=max_retries)

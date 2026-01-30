from django.db import models


class TaskReconstruction(models.Model):
    id = models.BigAutoField(primary_key=True)
    task_result = models.OneToOneField(
        'django_celery_results.TaskResult',
        on_delete=models.CASCADE,
    )
    # @note(chalvin): same as task_result.task_id. Saved for performance.
    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    task_name = models.CharField(max_length=255)
    task_args = models.TextField()
    task_kwargs = models.TextField()
    queue_options = models.JSONField(default=dict)
    # @note(chalvin): same as queue_options['channel].
    # Saved for performance on admin page.
    channel = models.CharField(max_length=255, null=True, blank=True)
    # Saved for performance on admin page.
    callable_name_meta = models.CharField(
        max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'taskqueue_task_reconstruction'
        app_label = 'taskqueue'

    def __str__(self):
        return f"TaskReconstruction({self.task_id})"

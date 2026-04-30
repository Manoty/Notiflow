import uuid
from django.db import models


class Notification(models.Model):

    class Channel(models.TextChoices):
        EMAIL  = 'email',  'Email'
        SMS    = 'sms',    'SMS'
        IN_APP = 'in_app', 'In-App'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT    = 'sent',    'Sent'
        FAILED  = 'failed',  'Failed'
        READ    = 'read',    'Read'   # used by in-app only

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id     = models.CharField(max_length=255)          # external reference — no FK to a User model
    app_id      = models.CharField(max_length=100, default='default')  # multi-tenant: 'tixora', 'scott'
    channel     = models.CharField(max_length=20, choices=Channel.choices)
    title       = models.CharField(max_length=255)
    message     = models.TextField()
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    scheduled_at = models.DateTimeField(null=True, blank=True)  # future: scheduled sends
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'app_id']),
            models.Index(fields=['status']),
            models.Index(fields=['channel']),
            models.Index(fields=['channel', 'user_id', 'status']),
        ]

    def __str__(self):
        return f"[{self.channel.upper()}] {self.title} → {self.user_id} ({self.status})"

    @property
    def can_retry(self):
        return self.status == self.Status.FAILED and self.retry_count < self.max_retries


class NotificationLog(models.Model):

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification     = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    attempt_number   = models.PositiveIntegerField(default=1)
    status           = models.CharField(max_length=20, choices=Status.choices)
    response_data    = models.TextField(blank=True, null=True)   # raw API response or SMTP success info
    error_message    = models.TextField(blank=True, null=True)   # exception message on failure
    attempted_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"Log #{self.attempt_number} for {self.notification_id} — {self.status}"
from django.contrib import admin
from .models import Notification, NotificationLog


class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0
    readonly_fields = ('attempt_number', 'status', 'response_data', 'error_message', 'attempted_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user_id', 'app_id', 'channel', 'status', 'retry_count', 'created_at')
    list_filter   = ('status', 'channel', 'app_id')
    search_fields = ('user_id', 'title', 'message')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines       = [NotificationLogInline]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display  = ('notification', 'attempt_number', 'status', 'attempted_at')
    list_filter   = ('status',)
    readonly_fields = ('id', 'attempted_at')
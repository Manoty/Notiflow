from rest_framework import serializers
from .models import Notification, NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NotificationLog
        fields = [
            'id', 'attempt_number', 'status',
            'response_data', 'error_message', 'attempted_at',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    logs = NotificationLogSerializer(many=True, read_only=True)

    class Meta:
        model  = Notification
        fields = [
            'id', 'user_id', 'app_id', 'channel', 'title',
            'message', 'status', 'retry_count', 'max_retries',
            'scheduled_at', 'created_at', 'updated_at', 'logs',
        ]
        read_only_fields = [
            'id', 'status', 'retry_count',
            'created_at', 'updated_at', 'logs',
        ]


class SendNotificationSerializer(serializers.Serializer):
    """
    Thin input-only serializer for POST /notifications/send.
    Separate from NotificationSerializer so input validation
    stays decoupled from the full model representation.
    """
    user_id = serializers.CharField(max_length=255)
    app_id  = serializers.CharField(max_length=100, default='default')
    channel = serializers.ChoiceField(choices=Notification.Channel.choices)
    title   = serializers.CharField(max_length=255)
    message = serializers.CharField()
    max_retries  = serializers.IntegerField(default=3, min_value=0, max_value=10)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)

    def create(self, validated_data):
        return Notification.objects.create(**validated_data)
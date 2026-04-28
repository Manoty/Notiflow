import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Notification
from .serializers import SendNotificationSerializer, NotificationSerializer

logger = logging.getLogger(__name__)


class SendNotificationView(APIView):
    """
    POST /notifications/send
    Accepts a notification payload, persists it, and enqueues delivery.
    Returns 202 immediately — delivery happens asynchronously.
    """

    def post(self, request):
        serializer = SendNotificationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification = serializer.save()
        logger.info(
            f"Notification created: {notification.id} | "
            f"channel={notification.channel} | app={notification.app_id}"
        )

        # Dispatch to background — implemented in Phase 7
        # dispatch_notification(notification.id)

        return Response(
            {
                'success': True,
                'message': 'Notification accepted and queued for delivery.',
                'notification_id': str(notification.id),
                'channel': notification.channel,
                'status': notification.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class NotificationListView(APIView):
    """
    GET /notifications/
    Supports filtering by: status, channel, app_id, user_id
    """

    def get(self, request):
        queryset = Notification.objects.prefetch_related('logs').all()

        # Apply filters from query params
        filters = {}
        for field in ('status', 'channel', 'app_id', 'user_id'):
            value = request.query_params.get(field)
            if value:
                filters[field] = value

        queryset = queryset.filter(**filters)

        serializer = NotificationSerializer(queryset, many=True)
        return Response(
            {
                'count': queryset.count(),
                'results': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class NotificationDetailView(APIView):
    """
    GET /notifications/<id>/
    Returns a single notification with its full log history.
    """

    def get(self, request, notification_id):
        try:
            notification = (
                Notification.objects
                .prefetch_related('logs')
                .get(id=notification_id)
            )
        except Notification.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Notification not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkAsReadView(APIView):
    """
    PATCH /notifications/<id>/read/
    Marks an in-app notification as read.
    """

    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                channel=Notification.Channel.IN_APP,
            )
        except Notification.DoesNotExist:
            return Response(
                {'success': False, 'error': 'In-app notification not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if notification.status == Notification.Status.READ:
            return Response(
                {'success': False, 'message': 'Already marked as read.'},
                status=status.HTTP_200_OK,
            )

        notification.status = Notification.Status.READ
        notification.save(update_fields=['status', 'updated_at'])

        return Response(
            {'success': True, 'message': 'Notification marked as read.'},
            status=status.HTTP_200_OK,
        )
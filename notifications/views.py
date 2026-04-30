import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .tasks import enqueue_notification
from .tasks import get_queue_stats
from .services.retry_manager import RetryManager

from django.utils import timezone

from .models import Notification
from .serializers import SendNotificationSerializer, NotificationSerializer

from django.db.models import Count, Q
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)


class SendNotificationView(APIView):

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

        # Honour scheduled_at if provided, otherwise run immediately
        delay = 0
        if notification.scheduled_at:
            from django.utils import timezone
            delta = notification.scheduled_at - timezone.now()
            delay = max(0, int(delta.total_seconds()))

        enqueue_notification(notification.id, delay_seconds=delay)

        return Response(
            {
                'success':         True,
                'message':         'Notification accepted and queued for delivery.',
                'notification_id': str(notification.id),
                'channel':         notification.channel,
                'status':          notification.status,  # 'pending' until worker runs
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
        
class InboxPagination(PageNumberPagination):
    """
    Paginate inbox results so the frontend doesn't
    receive thousands of notifications in one response.
    """
    page_size            = 20
    page_size_query_param = 'page_size'
    max_page_size        = 100


class InboxView(APIView):
    """
    GET /notifications/inbox/?user_id=123&app_id=tixora

    Returns paginated in-app notifications for a specific user.
    Ordered newest-first (model Meta already handles this).
    Supports optional ?unread_only=true filter.
    """

    def get(self, request):
        user_id = request.query_params.get('user_id')
        app_id  = request.query_params.get('app_id')

        if not user_id:
            return Response(
                {'success': False, 'error': 'user_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Notification.objects.filter(
            channel = Notification.Channel.IN_APP,
            user_id = user_id,
        )

        if app_id:
            queryset = queryset.filter(app_id=app_id)

        # Optional: only return unread
        unread_only = request.query_params.get('unread_only', '').lower() == 'true'
        if unread_only:
            queryset = queryset.exclude(status=Notification.Status.READ)

        paginator   = InboxPagination()
        page        = paginator.paginate_queryset(queryset, request)
        serializer  = NotificationSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class UnreadCountView(APIView):
    """
    GET /notifications/unread-count/?user_id=123&app_id=tixora

    Lightweight endpoint — returns only the unread count.
    The frontend polls this every N seconds to update the
    notification bell badge without fetching full payloads.
    """

    def get(self, request):
        user_id = request.query_params.get('user_id')
        app_id  = request.query_params.get('app_id')

        if not user_id:
            return Response(
                {'success': False, 'error': 'user_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filters = {
            'channel': Notification.Channel.IN_APP,
            'user_id': user_id,
        }
        if app_id:
            filters['app_id'] = app_id

        unread_count = Notification.objects.filter(
            **filters
        ).exclude(
            status=Notification.Status.READ
        ).count()

        return Response(
            {
                'user_id':      user_id,
                'app_id':       app_id or 'all',
                'unread_count': unread_count,
            },
            status=status.HTTP_200_OK,
        )


class MarkAllReadView(APIView):
    """
    POST /notifications/mark-all-read/

    Body: { "user_id": "123", "app_id": "tixora" }

    Bulk-marks all unread in-app notifications as read.
    Uses queryset update() — one SQL query regardless of count.
    """

    def post(self, request):
        user_id = request.data.get('user_id')
        app_id  = request.data.get('app_id')

        if not user_id:
            return Response(
                {'success': False, 'error': 'user_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filters = {
            'channel': Notification.Channel.IN_APP,
            'user_id': user_id,
        }
        if app_id:
            filters['app_id'] = app_id

        updated = Notification.objects.filter(
            **filters
        ).exclude(
            status=Notification.Status.READ
        ).update(
            status     = Notification.Status.READ,
            updated_at = timezone.now(),
        )

        logger.info(f"Marked {updated} notifications as read for user={user_id} app={app_id}")

        return Response(
            {
                'success':       True,
                'marked_read':   updated,
                'user_id':       user_id,
                'app_id':        app_id or 'all',
            },
            status=status.HTTP_200_OK,
        )        
        
class QueueStatsView(APIView):
    """
    GET /notifications/queue-stats/
    Returns a snapshot of the background task queue.
    """

    def get(self, request):
        stats = get_queue_stats()
        return Response(stats, status=status.HTTP_200_OK)       
    
class RetryNotificationView(APIView):
    """
    POST /notifications/<id>/retry/

    Manually triggers a retry for a failed notification.
    Useful after fixing a config issue (e.g. wrong SMTP password).
    Only works on notifications in FAILED status.
    """

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Notification not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if notification.status != Notification.Status.FAILED:
            return Response(
                {
                    'success': False,
                    'error':   f"Cannot retry a notification with status '{notification.status}'. "
                               "Only FAILED notifications can be retried.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not notification.can_retry:
            # Allow override via request body: {"force": true}
            force = request.data.get('force', False)
            if not force:
                return Response(
                    {
                        'success': False,
                        'error':   (
                            f"Max retries reached "
                            f"({notification.retry_count}/{notification.max_retries}). "
                            "Pass {\"force\": true} to override."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Force retry: reset counter to allow one more attempt
            notification.retry_count = 0
            notification.save(update_fields=['retry_count', 'updated_at'])
            logger.warning(f"[Retry] Forced retry for {notification_id} by API request.")

        # Reset to pending so the task doesn't skip it
        notification.status = Notification.Status.PENDING
        notification.save(update_fields=['status', 'updated_at'])

        enqueue_notification(notification.id, delay_seconds=0)

        return Response(
            {
                'success':         True,
                'message':         'Notification re-queued for immediate delivery.',
                'notification_id': str(notification.id),
                'retry_count':     notification.retry_count,
                'max_retries':     notification.max_retries,
            },
            status=status.HTTP_202_ACCEPTED,
        )    
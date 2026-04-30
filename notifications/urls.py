from django.urls import path
from . import views

urlpatterns = [
    
    # Core notification endpoints
    path('send/',              views.SendNotificationView.as_view(),    name='notification-send'),
    path('',                   views.NotificationListView.as_view(),    name='notification-list'),
    path('<uuid:notification_id>/',      views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<uuid:notification_id>/read/', views.MarkAsReadView.as_view(),         name='notification-read'),
    
    # In-app inbox endpoints
    path('inbox/',                         views.InboxView.as_view(),             name='notification-inbox'),
    path('unread-count/',                  views.UnreadCountView.as_view(),       name='notification-unread-count'),
    path('mark-all-read/',                 views.MarkAllReadView.as_view(),       name='notification-mark-all-read'),
    
    path('queue-stats/', views.QueueStatsView.as_view(), name='queue-stats',  name='queue-stats'),
]
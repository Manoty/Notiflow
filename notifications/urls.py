from django.urls import path
from . import views

urlpatterns = [
    path('send/',              views.SendNotificationView.as_view(),    name='notification-send'),
    path('',                   views.NotificationListView.as_view(),    name='notification-list'),
    path('<uuid:notification_id>/',      views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<uuid:notification_id>/read/', views.MarkAsReadView.as_view(),         name='notification-read'),
]
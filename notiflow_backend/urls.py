from django.contrib import admin
from django.urls import path, include
from notifications.views import HealthView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('notifications/',  include('notifications.urls')),
    path('health/',        HealthView.as_view(), name='health'),
]

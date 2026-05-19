from django.urls import path
from . import views

urlpatterns = [
    # Analytics
    path('stats/',                              views.get_stats,           name='admin-stats'),

    # Fraud alerts
    path('fraud-alerts/',                       views.get_fraud_alerts,    name='fraud-alerts-list'),
    path('fraud-alerts/create/',                views.create_fraud_alert,  name='fraud-alerts-create'),
    path('fraud-alerts/<str:alert_id>/update/', views.update_fraud_alert,  name='fraud-alerts-update'),

    # Activity logs
    path('activity/',                           views.get_activity_logs,   name='activity-list'),
    path('activity/create/',                    views.create_activity_log, name='activity-create'),

    # Health check
    path('health/',                             views.health_check,        name='admin-health'),
]
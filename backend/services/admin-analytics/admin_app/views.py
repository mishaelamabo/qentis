from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import FraudAlert, ActivityLog
from .serializers import (
    FraudAlertSerializer,
    FraudAlertCreateSerializer,
    FraudAlertUpdateSerializer,
    ActivityLogSerializer,
    ActivityLogCreateSerializer,
)


# ── Analytics ─────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def get_stats(request):
    """
    Returns platform statistics for the admin dashboard.
    GET /api/admin/stats/
    """
    stats = {
        'total_fraud_alerts':   FraudAlert.objects.count(),
        'open_fraud_alerts':    FraudAlert.objects.filter(status=FraudAlert.Status.OPEN).count(),
        'total_activity_logs':  ActivityLog.objects.count(),
        'recent_registrations': ActivityLog.objects.filter(event_type=ActivityLog.EventType.REGISTRATION).count(),
        'recent_verifications': ActivityLog.objects.filter(event_type=ActivityLog.EventType.VERIFICATION).count(),
        'recent_revocations':   ActivityLog.objects.filter(event_type=ActivityLog.EventType.REVOCATION).count(),
    }
    return Response(stats, status=status.HTTP_200_OK)


# ── Fraud Alerts ──────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def get_fraud_alerts(request):
    """
    Returns all fraud alerts.
    GET /api/admin/fraud-alerts/
    Optional query param: ?status=OPEN
    """
    status_filter = request.query_params.get('status', None)

    if status_filter:
        alerts = FraudAlert.objects.filter(status=status_filter)
    else:
        alerts = FraudAlert.objects.all()

    return Response(
        FraudAlertSerializer(alerts, many=True).data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_fraud_alert(request):
    """
    Creates a new fraud alert.
    POST /api/admin/fraud-alerts/create/
    Called by the Verification Service when fraud threshold is exceeded.
    """
    serializer = FraudAlertCreateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data  = serializer.validated_data
    alert = FraudAlert.objects.create(
        item_hash          = data['item_hash'],
        item_id            = data.get('item_id', ''),
        issuer_id          = data.get('issuer_id', ''),
        verification_count = data['verification_count'],
    )

    return Response(
        FraudAlertSerializer(alert).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_fraud_alert(request, alert_id):
    """
    Updates a fraud alert status.
    PATCH /api/admin/fraud-alerts/{alert_id}/update/
    Called by Admin to resolve or dismiss an alert.
    """
    try:
        alert = FraudAlert.objects.get(id=alert_id)
    except (FraudAlert.DoesNotExist, Exception):
        return Response(
            {'error': 'Fraud alert not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = FraudAlertUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    alert.status = serializer.validated_data['status']
    alert.notes  = serializer.validated_data.get('notes', '')
    alert.save()

    return Response(
        FraudAlertSerializer(alert).data,
        status=status.HTTP_200_OK
    )


# ── Activity Log ──────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def get_activity_logs(request):
    """
    Returns all activity logs.
    GET /api/admin/activity/
    Optional query param: ?event_type=REGISTRATION
    """
    event_filter = request.query_params.get('event_type', None)

    if event_filter:
        logs = ActivityLog.objects.filter(event_type=event_filter)
    else:
        logs = ActivityLog.objects.all()[:100]

    return Response(
        ActivityLogSerializer(logs, many=True).data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_activity_log(request):
    """
    Creates a new activity log entry.
    POST /api/admin/activity/create/
    Called by other services to log significant events.
    """
    serializer = ActivityLogCreateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    log  = ActivityLog.objects.create(
        event_type  = data['event_type'],
        description = data['description'],
        actor_id    = data.get('actor_id', ''),
        item_hash   = data.get('item_hash', ''),
    )

    return Response(
        ActivityLogSerializer(log).data,
        status=status.HTTP_201_CREATED
    )


# ── Health Check ──────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    GET /api/admin/health/
    """
    return Response(
        {
            'service':      'admin-analytics',
            'status':       'ok',
            'total_alerts': FraudAlert.objects.count(),
            'total_logs':   ActivityLog.objects.count(),
        },
        status=status.HTTP_200_OK
    )
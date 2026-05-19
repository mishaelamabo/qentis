from rest_framework import serializers
from .models import FraudAlert, ActivityLog


class FraudAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FraudAlert
        fields = [
            'id',
            'item_hash',
            'item_id',
            'issuer_id',
            'verification_count',
            'status',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FraudAlertCreateSerializer(serializers.Serializer):
    """Called by Verification Service to raise a fraud alert."""
    item_hash          = serializers.CharField(max_length=64)
    item_id            = serializers.CharField(max_length=255, required=False, default='')
    issuer_id          = serializers.CharField(max_length=255, required=False, default='')
    verification_count = serializers.IntegerField()


class FraudAlertUpdateSerializer(serializers.Serializer):
    """Called by Admin to resolve or dismiss a fraud alert."""
    status = serializers.ChoiceField(choices=FraudAlert.Status.choices)
    notes  = serializers.CharField(required=False, default='')


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ActivityLog
        fields = [
            'id',
            'event_type',
            'description',
            'actor_id',
            'item_hash',
            'created_at',
        ]
        read_only_fields = fields


class ActivityLogCreateSerializer(serializers.Serializer):
    """Called by other services to log an event."""
    event_type  = serializers.ChoiceField(choices=ActivityLog.EventType.choices)
    description = serializers.CharField()
    actor_id    = serializers.CharField(required=False, default='')
    item_hash   = serializers.CharField(required=False, default='')
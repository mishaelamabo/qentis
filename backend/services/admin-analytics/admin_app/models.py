import uuid
from django.db import models


class FraudAlert(models.Model):
    """
    Stores fraud alerts generated when an item is verified
    more than FRAUD_THRESHOLD times in one hour.
    """

    class Status(models.TextChoices):
        OPEN     = 'OPEN',     'Open — under review'
        RESOLVED = 'RESOLVED', 'Resolved'
        DISMISSED = 'DISMISSED', 'Dismissed — false positive'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    item_hash = models.CharField(
        max_length=64,
        help_text="Hash of the suspicious item"
    )
    item_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID of the item from Item Registration Service"
    )
    issuer_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID of the issuer who registered the item"
    )
    verification_count = models.IntegerField(
        default=0,
        help_text="Number of verifications that triggered this alert"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN
    )
    notes = models.TextField(
        blank=True,
        help_text="Admin notes on this alert"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fraud_alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Alert {self.item_hash[:16]}... — {self.status}"


class ActivityLog(models.Model):
    """
    Logs all significant platform events for the admin dashboard.
    """

    class EventType(models.TextChoices):
        REGISTRATION  = 'REGISTRATION',  'Item registered'
        VERIFICATION  = 'VERIFICATION',  'Item verified'
        REVOCATION    = 'REVOCATION',    'Item revoked'
        ISSUER_APPROVED = 'ISSUER_APPROVED', 'Issuer approved'
        ISSUER_REJECTED = 'ISSUER_REJECTED', 'Issuer rejected'
        FRAUD_FLAGGED = 'FRAUD_FLAGGED', 'Fraud alert raised'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices
    )
    description = models.TextField()
    actor_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID of the user who triggered this event"
    )
    item_hash = models.CharField(
        max_length=64,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} — {self.created_at}"
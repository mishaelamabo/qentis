import uuid
from django.db import models


class GeneratedOutput(models.Model):

    class OutputType(models.TextChoices):
        QR_CODE   = 'QR_CODE',   'QR Code'
        SERIAL    = 'SERIAL',    'Serial Number'
        SIGNATURE = 'SIGNATURE', 'Digital Signature'
        WATERMARK = 'WATERMARK', 'Watermark'

    class Category(models.TextChoices):
        ACADEMIC  = 'ACADEMIC',  'Academic Certificate'
        PHARMA    = 'PHARMA',    'Pharmaceutical Product'
        DOCUMENT  = 'DOCUMENT',  'Official Document'
        CURRENCY  = 'CURRENCY',  'Currency / Banknote'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    item_id = models.CharField(
        max_length=255,
        help_text="ID of the item from Item Registration Service"
    )
    item_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of the item"
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )
    issuer_id = models.CharField(
        max_length=255,
        help_text="ID of the issuer from Auth Service"
    )
    output_type = models.CharField(
        max_length=20,
        choices=OutputType.choices
    )
    serial_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Generated serial number e.g. QNT-2026-ACAD-00123"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to generated file (QR image, signed PDF, watermarked image)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'generated_outputs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.output_type} — {self.item_hash[:16]}... ({self.category})"
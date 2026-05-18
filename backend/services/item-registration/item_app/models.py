import uuid
from django.db import models


class Item(models.Model):

    class Category(models.TextChoices):
        CERTIFICATE = 'CERTIFICATE', 'Academic Certificate'
        PHARMACEUTICAL = 'PHARMACEUTICAL', 'Pharmaceutical Product'
        DOCUMENT = 'DOCUMENT', 'Official Document'
        BANKNOTE = 'BANKNOTE', 'Currency / Banknote'

    class Status(models.TextChoices):
        REGISTERED = 'REGISTERED', 'Registered'
        REVOKED = 'REVOKED', 'Revoked'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    institution_id = models.UUIDField(
        help_text="ID of the institution from Institution Management Service"
    )
    issuer_id = models.UUIDField(
        help_text="ID of the issuer user from User & Auth Service"
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.REGISTERED
    )
    blockchain_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="SHA-256 hash stored on blockchain"
    )
    transaction_hash = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Ethereum transaction hash"
    )
    qr_code_url = models.URLField(blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'items'
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.category} - {self.id}"


class CertificateDetail(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name='certificate_detail'
    )
    student_name = models.CharField(max_length=255)
    matricule = models.CharField(max_length=100)
    degree = models.CharField(max_length=255)
    institution_name = models.CharField(max_length=255)
    graduation_date = models.DateField()
    grade = models.CharField(max_length=100)

    class Meta:
        db_table = 'certificate_details'

    def __str__(self):
        return f"{self.student_name} - {self.degree}"

    def get_hash_fields(self):
        """Returns concatenated fields for SHA-256 hashing"""
        return f"{self.student_name}{self.matricule}{self.degree}{self.institution_name}{self.graduation_date}{self.grade}"


class PharmaceuticalDetail(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name='pharmaceutical_detail'
    )
    drug_name = models.CharField(max_length=255)
    batch_number = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=255)
    production_date = models.DateField()
    expiry_date = models.DateField()
    factory_location = models.CharField(max_length=255)

    class Meta:
        db_table = 'pharmaceutical_details'

    def __str__(self):
        return f"{self.drug_name} - {self.batch_number}"

    def get_hash_fields(self):
        return f"{self.drug_name}{self.batch_number}{self.manufacturer}{self.production_date}{self.expiry_date}{self.factory_location}"


class DocumentDetail(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name='document_detail'
    )
    document_type = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=255)
    issuing_authority = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    issue_date = models.DateField()

    class Meta:
        db_table = 'document_details'

    def __str__(self):
        return f"{self.document_type} - {self.owner_name}"

    def get_hash_fields(self):
        return f"{self.document_type}{self.owner_name}{self.issuing_authority}{self.reference_number}{self.location}{self.issue_date}"


class BanknoteDetail(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name='banknote_detail'
    )
    currency = models.CharField(max_length=10)
    denomination = models.DecimalField(max_digits=15, decimal_places=2)
    serial_number = models.CharField(max_length=100)
    series = models.CharField(max_length=100)
    issue_date = models.DateField()
    issuing_bank = models.CharField(max_length=255)

    class Meta:
        db_table = 'banknote_details'

    def __str__(self):
        return f"{self.currency} {self.denomination} - {self.serial_number}"

    def get_hash_fields(self):
        return f"{self.currency}{self.denomination}{self.serial_number}{self.series}{self.issue_date}{self.issuing_bank}"
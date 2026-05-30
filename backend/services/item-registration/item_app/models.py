import uuid
from django.db import models


class Item(models.Model):

    class Category(models.TextChoices):
        CERTIFICATE    = 'CERTIFICATE',    'Academic Certificate'
        PHARMACEUTICAL = 'PHARMACEUTICAL', 'Pharmaceutical Product'
        DOCUMENT       = 'DOCUMENT',       'Official Document'
        BANKNOTE       = 'BANKNOTE',       'Currency / Banknote'

    class Status(models.TextChoices):
        PENDING    = 'PENDING',    'Pending Approval'
        REGISTERED = 'REGISTERED', 'Registered'
        REJECTED   = 'REJECTED',   'Rejected'
        REVOKED    = 'REVOKED',    'Revoked'

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
        default=Status.PENDING
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
    qr_code_url    = models.URLField(blank=True, null=True)
    serial_number  = models.CharField(max_length=100, blank=True, null=True)
    registered_at  = models.DateTimeField(auto_now_add=True)
    revoked_at     = models.DateTimeField(null=True, blank=True)
    revoke_reason  = models.TextField(null=True, blank=True)
    rejected_at    = models.DateTimeField(null=True, blank=True)
    reject_reason  = models.TextField(null=True, blank=True)
    approved_at    = models.DateTimeField(null=True, blank=True)
    approved_by    = models.UUIDField(null=True, blank=True)
    updated_at     = models.DateTimeField(auto_now=True)

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
    student_name     = models.CharField(max_length=255)
    matricule        = models.CharField(max_length=100)
    degree           = models.CharField(max_length=255)
    institution_name = models.CharField(max_length=255)
    graduation_date  = models.DateField()
    grade            = models.CharField(max_length=100)

    class Meta:
        db_table = 'certificate_details'

    def __str__(self):
        return f"{self.student_name} - {self.degree}"

    def get_hash_fields(self):
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
    drug_name        = models.CharField(max_length=255)
    batch_number     = models.CharField(max_length=100)
    manufacturer     = models.CharField(max_length=255)
    production_date  = models.DateField()
    expiry_date      = models.DateField()
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
    # Common fields
    document_type     = models.CharField(max_length=100)
    owner_name        = models.CharField(max_length=255)
    issuing_authority = models.CharField(max_length=255)
    reference_number  = models.CharField(max_length=100)  # NIC Number
    card_number       = models.CharField(max_length=100, blank=True, null=True)
    location          = models.CharField(max_length=255)
    issue_date        = models.DateField()

    # New CNI specific fields
    owner_surname     = models.CharField(max_length=255, blank=True, null=True)
    owner_given_names = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth     = models.DateField(blank=True, null=True)
    date_of_expiry    = models.DateField(blank=True, null=True)
    sex               = models.CharField(max_length=1, blank=True, null=True)
    father_name       = models.CharField(max_length=255, blank=True, null=True)
    mother_name       = models.CharField(max_length=255, blank=True, null=True)
    place_of_birth    = models.CharField(max_length=255, blank=True, null=True)
    occupation        = models.CharField(max_length=255, blank=True, null=True)
    height            = models.CharField(max_length=10, blank=True, null=True)
    mrz_line1         = models.CharField(max_length=255, blank=True, null=True)
    mrz_line2         = models.CharField(max_length=255, blank=True, null=True)
    mrz_line3         = models.CharField(max_length=255, blank=True, null=True)

    # Biometric
    fingerprint_hash  = models.CharField(max_length=255, blank=True, null=True)
    credential_id     = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'document_details'

    def __str__(self):
        return f"{self.document_type} - {self.owner_name}"

    def get_hash_fields(self):
        base = f"{self.document_type}{self.owner_name}{self.issuing_authority}{self.reference_number}{self.location}{self.issue_date}"
        if self.card_number:
            base += self.card_number
        if self.date_of_birth:
            base += str(self.date_of_birth)
        if self.fingerprint_hash:
            base += self.fingerprint_hash
        return base


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
    currency      = models.CharField(max_length=10)
    denomination  = models.DecimalField(max_digits=15, decimal_places=2)
    serial_number = models.CharField(max_length=100)
    series        = models.CharField(max_length=100)
    issue_date    = models.DateField()
    issuing_bank  = models.CharField(max_length=255)

    class Meta:
        db_table = 'banknote_details'

    def __str__(self):
        return f"{self.currency} {self.denomination} - {self.serial_number}"

    def get_hash_fields(self):
        return f"{self.currency}{self.denomination}{self.serial_number}{self.series}{self.issue_date}{self.issuing_bank}"
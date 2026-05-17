import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        ISSUER = 'ISSUER', 'Issuer'
        VERIFIER = 'VERIFIER', 'Verifier'
        ADMIN = 'ADMIN', 'Administrator'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VERIFIER
    )
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.role})"


class Issuer(models.Model):

    class InstitutionType(models.TextChoices):
        UNIVERSITY = 'UNIVERSITY', 'University'
        HOSPITAL = 'HOSPITAL', 'Hospital'
        NOTARY = 'NOTARY', 'Notary'
        BANK = 'BANK', 'Bank'
        MANUFACTURER = 'MANUFACTURER', 'Manufacturer'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='issuer_profile'
    )
    institution_name = models.CharField(max_length=255, blank=True)
    institution_type = models.CharField(
        max_length=20,
        choices=InstitutionType.choices,
        blank=True
    )
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)

    class Meta:
        db_table = 'issuers'

    def __str__(self):
        return f"{self.institution_name} ({self.user.email})"


class Verifier(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='verifier_profile'
    )

    class Meta:
        db_table = 'verifiers'

    def __str__(self):
        return f"Verifier: {self.user.email}"


class Administrator(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )
    can_approve_issuers = models.BooleanField(default=True)
    can_revoke_issuers = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)
    can_resolve_flags = models.BooleanField(default=True)

    class Meta:
        db_table = 'administrators'

    def __str__(self):
        return f"Admin: {self.user.email}"
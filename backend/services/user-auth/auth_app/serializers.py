from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Issuer, Verifier, Administrator


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'role',
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        role = validated_data.get('role', User.Role.VERIFIER)

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        # Create role-specific profile
        if role == User.Role.ISSUER:
            Issuer.objects.create(user=user)
        elif role == User.Role.VERIFIER:
            Verifier.objects.create(user=user)
        elif role == User.Role.ADMIN:
            Administrator.objects.create(user=user)

        return user


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'is_verified',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'is_verified',
            'is_active',
            'created_at',
            'updated_at',
        ]


class IssuerProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Issuer
        fields = [
            'institution_name',
            'institution_type',
            'country',
            'city',
            'contact_email',
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    issuer_profile = IssuerProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email',
            'issuer_profile',
        ]

    def update(self, instance, validated_data):
        issuer_data = validated_data.pop('issuer_profile', None)

        instance.email = validated_data.get('email', instance.email)
        instance.save()

        if issuer_data and hasattr(instance, 'issuer_profile'):
            issuer = instance.issuer_profile
            for attr, value in issuer_data.items():
                setattr(issuer, attr, value)
            issuer.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "New passwords do not match."}
            )
        return attrs
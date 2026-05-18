from rest_framework import serializers
from .models import (
    Item,
    CertificateDetail,
    PharmaceuticalDetail,
    DocumentDetail,
    BanknoteDetail,
)


class CertificateDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateDetail
        fields = [
            'id',
            'student_name',
            'matricule',
            'degree',
            'institution_name',
            'graduation_date',
            'grade',
        ]
        read_only_fields = ['id']


class PharmaceuticalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmaceuticalDetail
        fields = [
            'id',
            'drug_name',
            'batch_number',
            'manufacturer',
            'production_date',
            'expiry_date',
            'factory_location',
        ]
        read_only_fields = ['id']


class DocumentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentDetail
        fields = [
            'id',
            'document_type',
            'owner_name',
            'issuing_authority',
            'reference_number',
            'location',
            'issue_date',
        ]
        read_only_fields = ['id']


class BanknoteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanknoteDetail
        fields = [
            'id',
            'currency',
            'denomination',
            'serial_number',
            'series',
            'issue_date',
            'issuing_bank',
        ]
        read_only_fields = ['id']


class ItemSerializer(serializers.ModelSerializer):
    certificate_detail = CertificateDetailSerializer(read_only=True)
    pharmaceutical_detail = PharmaceuticalDetailSerializer(read_only=True)
    document_detail = DocumentDetailSerializer(read_only=True)
    banknote_detail = BanknoteDetailSerializer(read_only=True)

    class Meta:
        model = Item
        fields = [
            'id',
            'institution_id',
            'issuer_id',
            'category',
            'status',
            'blockchain_hash',
            'transaction_hash',
            'qr_code_url',
            'serial_number',
            'registered_at',
            'revoked_at',
            'revoke_reason',
            'updated_at',
            'certificate_detail',
            'pharmaceutical_detail',
            'document_detail',
            'banknote_detail',
        ]
        read_only_fields = [
            'id',
            'status',
            'blockchain_hash',
            'transaction_hash',
            'qr_code_url',
            'serial_number',
            'registered_at',
            'revoked_at',
            'updated_at',
        ]


class RegisterItemSerializer(serializers.Serializer):
    """
    Used when an issuer registers a new item.
    Accepts category and category-specific fields.
    """
    category = serializers.ChoiceField(choices=Item.Category.choices)

    # Certificate fields
    student_name = serializers.CharField(required=False)
    matricule = serializers.CharField(required=False)
    degree = serializers.CharField(required=False)
    institution_name = serializers.CharField(required=False)
    graduation_date = serializers.DateField(required=False)
    grade = serializers.CharField(required=False)

    # Pharmaceutical fields
    drug_name = serializers.CharField(required=False)
    batch_number = serializers.CharField(required=False)
    manufacturer = serializers.CharField(required=False)
    production_date = serializers.DateField(required=False)
    expiry_date = serializers.DateField(required=False)
    factory_location = serializers.CharField(required=False)

    # Document fields
    document_type = serializers.CharField(required=False)
    owner_name = serializers.CharField(required=False)
    issuing_authority = serializers.CharField(required=False)
    reference_number = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    issue_date = serializers.DateField(required=False)

    # Banknote fields
    currency = serializers.CharField(required=False)
    denomination = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    serial_number = serializers.CharField(required=False)
    series = serializers.CharField(required=False)
    issuing_bank = serializers.CharField(required=False)

    def validate(self, attrs):
        category = attrs.get('category')

        if category == Item.Category.CERTIFICATE:
            required = [
                'student_name', 'matricule', 'degree',
                'institution_name', 'graduation_date', 'grade'
            ]
        elif category == Item.Category.PHARMACEUTICAL:
            required = [
                'drug_name', 'batch_number', 'manufacturer',
                'production_date', 'expiry_date', 'factory_location'
            ]
        elif category == Item.Category.DOCUMENT:
            required = [
                'document_type', 'owner_name', 'issuing_authority',
                'reference_number', 'location', 'issue_date'
            ]
        elif category == Item.Category.BANKNOTE:
            required = [
                'currency', 'denomination', 'serial_number',
                'series', 'issue_date', 'issuing_bank'
            ]
        else:
            required = []

        missing = [f for f in required if not attrs.get(f)]
        if missing:
            raise serializers.ValidationError(
                {f: f"This field is required for {category}." for f in missing}
            )

        return attrs


class RevokeItemSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)

    def validate_reason(self, value):
        if len(value) < 10:
            raise serializers.ValidationError(
                "Revocation reason must be at least 10 characters."
            )
        return value
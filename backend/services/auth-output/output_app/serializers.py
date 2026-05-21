from rest_framework import serializers
from .models import GeneratedOutput


class GenerateOutputSerializer(serializers.Serializer):
    """
    Validates incoming request to generate outputs for a registered item.
    Called by the Item Registration Service after an item is registered.
    """
    item_id   = serializers.CharField(max_length=255)
    item_hash = serializers.CharField(max_length=64)
    category  = serializers.ChoiceField(choices=GeneratedOutput.Category.choices)
    issuer_id = serializers.CharField(max_length=255)
    item_name = serializers.CharField(max_length=255, required=False, default='')


class VerifySignatureSerializer(serializers.Serializer):
    """
    Validates incoming request to verify a digital signature.
    Called by the Verification Service.
    """
    file      = serializers.FileField()
    item_hash = serializers.CharField(max_length=64)


class VerifyWatermarkSerializer(serializers.Serializer):
    """
    Validates incoming request to verify a watermark.
    Called by the Verification Service.
    """
    image     = serializers.ImageField()
    item_hash = serializers.CharField(max_length=64)


class GeneratedOutputSerializer(serializers.ModelSerializer):
    """
    Serializes a GeneratedOutput record for display.
    """
    class Meta:
        model  = GeneratedOutput
        fields = [
            'id',
            'item_id',
            'item_hash',
            'category',
            'issuer_id',
            'output_type',
            'serial_number',
            'file_path',
            'created_at',
        ]
        read_only_fields = fields
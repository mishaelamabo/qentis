import os
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import GeneratedOutput
from .serializers import (
    GenerateOutputSerializer,
    VerifySignatureSerializer,
    VerifyWatermarkSerializer,
    GeneratedOutputSerializer,
)
from .generators import (
    generate_serial_number,
    generate_qr_code,
    generate_digital_signature,
    verify_digital_signature,
    embed_watermark,
    extract_watermark,
)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def generate_outputs(request):
    """
    Generate all authentication outputs for a registered item.
    POST /api/output/generate/
    Called by Item Registration Service after an item is registered.

    Always generates: QR code + serial number
    Category-specific: digital signature (ACADEMIC, DOCUMENT)
                       watermark (ACADEMIC, DOCUMENT, CURRENCY)
    """
    serializer = GenerateOutputSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data      = serializer.validated_data
    item_id   = data['item_id']
    item_hash = data['item_hash']
    category  = data['category']
    issuer_id = data['issuer_id']

    results = {}

    try:
        # 1. Always generate serial number
        serial = generate_serial_number(category)
        GeneratedOutput.objects.create(
            item_id     = item_id,
            item_hash   = item_hash,
            category    = category,
            issuer_id   = issuer_id,
            output_type = GeneratedOutput.OutputType.SERIAL,
            serial_number = serial,
        )
        results['serial_number'] = serial

        # 2. Always generate QR code
        qr_path = generate_qr_code(item_hash, serial, item_id)
        GeneratedOutput.objects.create(
            item_id     = item_id,
            item_hash   = item_hash,
            category    = category,
            issuer_id   = issuer_id,
            output_type = GeneratedOutput.OutputType.QR_CODE,
            file_path   = qr_path,
        )
        results['qr_code_path'] = qr_path

        # 3. Digital signature — ACADEMIC and DOCUMENT only
        if category in ['ACADEMIC', 'DOCUMENT']:
            sig_path, pub_path = generate_digital_signature(item_hash, item_id)
            GeneratedOutput.objects.create(
                item_id     = item_id,
                item_hash   = item_hash,
                category    = category,
                issuer_id   = issuer_id,
                output_type = GeneratedOutput.OutputType.SIGNATURE,
                file_path   = sig_path,
            )
            results['signature_path']   = sig_path
            results['public_key_path']  = pub_path

        return Response(
            {
                'message': 'Outputs generated successfully.',
                'item_id': item_id,
                'outputs': results,
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {'error': f'Output generation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_outputs(request, item_id):
    """
    Get all generated outputs for a specific item.
    GET /api/output/item/{item_id}/
    Called by the Issuer dashboard to show download links.
    """
    outputs = GeneratedOutput.objects.filter(item_id=item_id)

    if not outputs.exists():
        return Response(
            {'error': 'No outputs found for this item.'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        GeneratedOutputSerializer(outputs, many=True).data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def verify_signature(request):
    """
    Verify a digital signature uploaded by a verifier.
    POST /api/output/verify/signature/
    Called by the Verification Service.
    """
    serializer = VerifySignatureSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item_hash      = serializer.validated_data['item_hash']
    uploaded_file  = serializer.validated_data['file']

    try:
        # Get the stored public key for this item
        record = GeneratedOutput.objects.filter(
            item_hash   = item_hash,
            output_type = GeneratedOutput.OutputType.SIGNATURE,
        ).first()

        if not record:
            return Response(
                {'status': 'NOT_AUTHENTIC', 'message': 'No signature record found.'},
                status=status.HTTP_200_OK
            )

        # Read the public key file
        pub_key_path = record.file_path.replace('/sig_', '/pub_').replace('.bin', '.pem')
        if not os.path.exists(pub_key_path):
            return Response(
                {'status': 'NOT_AUTHENTIC', 'message': 'Public key not found.'},
                status=status.HTTP_200_OK
            )

        with open(pub_key_path, 'rb') as f:
            public_key_bytes = f.read()

        signature_bytes = uploaded_file.read()
        is_valid = verify_digital_signature(item_hash, signature_bytes, public_key_bytes)

        if is_valid:
            return Response({'status': 'AUTHENTIC'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'NOT_AUTHENTIC'}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Signature verification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def verify_watermark(request):
    """
    Verify a watermark from an uploaded image.
    POST /api/output/verify/watermark/
    Called by the Verification Service.
    """
    serializer = VerifyWatermarkSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item_hash    = serializer.validated_data['item_hash']
    uploaded_img = serializer.validated_data['image']

    try:
        # Save uploaded image temporarily
        temp_path = f"/tmp/verify_{item_hash[:8]}.png"
        with open(temp_path, 'wb') as f:
            for chunk in uploaded_img.chunks():
                f.write(chunk)

        extracted_hash = extract_watermark(temp_path)

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if extracted_hash and extracted_hash == item_hash:
            return Response({'status': 'AUTHENTIC'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'NOT_AUTHENTIC'}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Watermark verification failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.
    GET /api/output/health/
    """
    return Response(
        {
            'service':       'auth-output',
            'status':        'ok',
            'total_outputs': GeneratedOutput.objects.count(),
        },
        status=status.HTTP_200_OK
    )
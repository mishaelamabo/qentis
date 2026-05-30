import uuid
import json
import hashlib
import redis
import requests
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import VerificationLog, FraudFlag
from .serializers import (
    VerifyQRSerializer,
    VerifySerialSerializer,
    VerifySignatureSerializer,
    VerifyOCRSerializer,
    VerifyWatermarkSerializer,
    VerificationLogSerializer,
    FraudFlagSerializer,
    ReportItemSerializer,
)
from .auth_helper import require_role


def get_redis_client():
    return redis.from_url(settings.REDIS_URL)


def get_verifier_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_item_hash(item_id):
    try:
        response = requests.get(
            f"{settings.ITEM_SERVICE_URL}/api/items/{item_id}/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get('blockchain_hash')
    except Exception:
        pass
    return None


def get_item_by_serial(serial_number):
    try:
        response = requests.get(
            f"{settings.ITEM_SERVICE_URL}/api/items/serial/{serial_number}/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def get_item_by_reference(reference_number):
    """
    Get DOCUMENT item by reference number (Identifiant Unique).
    """
    try:
        response = requests.get(
            f"{settings.ITEM_SERVICE_URL}/api/items/reference/{reference_number}/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def check_blockchain(blockchain_hash):
    try:
        response = requests.post(
            f"{settings.BLOCKCHAIN_SERVICE_URL}/api/blockchain/verify/",
            json={'item_hash': blockchain_hash},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'AUTHENTIC':
                return {
                    'exists': True,
                    'timestamp': data.get('timestamp'),
                    'item_details': {
                        'category':      data.get('category'),
                        'issuer':        data.get('issuer_name'),
                        'issuer_id':     data.get('issuer_id'),
                        'registered_at': data.get('timestamp'),
                    }
                }
            else:
                return {'exists': False}
    except Exception:
        pass
    return {'exists': False}


def get_cached_result(key):
    try:
        r = get_redis_client()
        cached = r.get(f'verify:{key}')
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    return None


def cache_result(key, result):
    try:
        r = get_redis_client()
        r.setex(
            f'verify:{key}',
            settings.CACHE_TTL,
            json.dumps(result)
        )
    except Exception:
        pass


def check_fraud_pattern(item_id, issuer_id=None):
    window_start = timezone.now() - timedelta(hours=1)
    window_end   = timezone.now()

    count = VerificationLog.objects.filter(
        item_id=item_id,
        verified_at__gte=window_start,
        result=VerificationLog.Result.AUTHENTIC
    ).count()

    if count >= settings.FRAUD_THRESHOLD:
        existing_flag = FraudFlag.objects.filter(
            item_id=item_id,
            status=FraudFlag.FlagStatus.OPEN,
            window_start__gte=window_start
        ).first()

        if not existing_flag:
            FraudFlag.objects.create(
                item_id=item_id,
                issuer_id=issuer_id,
                verification_count=count,
                window_start=window_start,
                window_end=window_end,
            )


def log_verification(item_id, issuer_id, method, result, input_data, verifier_ip):
    return VerificationLog.objects.create(
        item_id=item_id,
        issuer_id=issuer_id,
        method=method,
        result=result,
        input_data=str(input_data),
        verifier_ip=verifier_ip,
    )


def build_result(result, item_id, method, message, item_details=None):
    return {
        'result':       result,
        'item_id':      str(item_id) if item_id else None,
        'method':       method,
        'message':      message,
        'item_details': item_details,
        'verified_at':  timezone.now().isoformat(),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_hash(request):
    item_hash   = request.data.get('item_hash')
    verifier_ip = get_verifier_ip(request)

    if not item_hash:
        return Response({'error': 'item_hash is required.'}, status=status.HTTP_400_BAD_REQUEST)

    cached = get_cached_result(f'hash:{item_hash}')
    if cached:
        return Response(cached, status=status.HTTP_200_OK)

    blockchain_response = check_blockchain(item_hash)

    if blockchain_response.get('exists'):
        result       = VerificationLog.Result.AUTHENTIC
        message      = 'This item is AUTHENTIC. Hash verified on blockchain.'
        item_details = blockchain_response.get('item_details')
    else:
        result       = VerificationLog.Result.NOT_AUTHENTIC
        message      = 'Hash NOT found on blockchain. This item could not be verified.'
        item_details = None

    response_data = build_result(result, item_hash, 'HASH', message, item_details)
    cache_result(f'hash:{item_hash}', response_data)
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_qr(request):
    serializer = VerifyQRSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    qr_data     = serializer.validated_data['qr_data']
    verifier_ip = get_verifier_ip(request)
    item_id     = None
    blockchain_hash = None

    try:
        item_id         = uuid.UUID(qr_data)
        blockchain_hash = get_item_hash(item_id)
    except ValueError:
        blockchain_hash = qr_data

    if not blockchain_hash:
        log_verification(item_id, None, VerificationLog.Method.QR,
                         VerificationLog.Result.NOT_AUTHENTIC, qr_data, verifier_ip)
        return Response(build_result(VerificationLog.Result.NOT_AUTHENTIC, item_id,
                                     VerificationLog.Method.QR,
                                     'Could not retrieve item details for verification.'),
                        status=status.HTTP_200_OK)

    cached = get_cached_result(f'qr:{blockchain_hash}')
    if cached:
        return Response(cached, status=status.HTTP_200_OK)

    blockchain_response = check_blockchain(blockchain_hash)

    if blockchain_response.get('exists'):
        result       = VerificationLog.Result.AUTHENTIC
        message      = 'This item is AUTHENTIC. Verified on blockchain.'
        item_details = blockchain_response.get('item_details')
    else:
        result       = VerificationLog.Result.NOT_AUTHENTIC
        message      = 'This item could NOT be verified.'
        item_details = None

    log_verification(item_id, None, VerificationLog.Method.QR, result, qr_data, verifier_ip)
    response_data = build_result(result, item_id, VerificationLog.Method.QR, message, item_details)
    cache_result(f'qr:{blockchain_hash}', response_data)

    if result == VerificationLog.Result.AUTHENTIC:
        check_fraud_pattern(item_id)

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_serial(request):
    serializer = VerifySerialSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serial_number = serializer.validated_data['serial_number']
    verifier_ip   = get_verifier_ip(request)

    cached = get_cached_result(f'serial:{serial_number}')
    if cached:
        return Response(cached, status=status.HTTP_200_OK)

    item_data = get_item_by_serial(serial_number)

    if not item_data:
        log_verification(None, None, VerificationLog.Method.SERIAL,
                         VerificationLog.Result.NOT_AUTHENTIC, serial_number, verifier_ip)
        return Response(build_result(VerificationLog.Result.NOT_AUTHENTIC, None,
                                     VerificationLog.Method.SERIAL,
                                     'Serial number not found in our records.'),
                        status=status.HTTP_200_OK)

    blockchain_hash = item_data.get('blockchain_hash')
    item_id         = item_data.get('id')

    blockchain_response = check_blockchain(blockchain_hash)

    if blockchain_response.get('exists'):
        result       = VerificationLog.Result.AUTHENTIC
        message      = 'Serial number verified. Item is AUTHENTIC.'
        item_details = blockchain_response.get('item_details')
    else:
        result       = VerificationLog.Result.NOT_AUTHENTIC
        message      = 'Serial number found but blockchain verification failed.'
        item_details = None

    log_verification(item_id, None, VerificationLog.Method.SERIAL, result, serial_number, verifier_ip)
    response_data = build_result(result, item_id, VerificationLog.Method.SERIAL, message, item_details)
    cache_result(f'serial:{serial_number}', response_data)

    if result == VerificationLog.Result.AUTHENTIC:
        check_fraud_pattern(item_id)

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def verify_signature(request):
    serializer = VerifySignatureSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    document    = serializer.validated_data['document']
    verifier_ip = get_verifier_ip(request)

    try:
        document_bytes    = document.read()
        document_hash     = hashlib.sha256(document_bytes).hexdigest()
        blockchain_response = check_blockchain(document_hash)

        if blockchain_response.get('exists'):
            result       = VerificationLog.Result.AUTHENTIC
            message      = 'Digital signature VERIFIED. Document is authentic.'
            item_details = blockchain_response.get('item_details')
        else:
            result       = VerificationLog.Result.NOT_AUTHENTIC
            message      = 'Digital signature could not be verified.'
            item_details = None
    except Exception:
        result       = VerificationLog.Result.UNVERIFIABLE
        message      = 'Could not process the document.'
        item_details = None

    log_verification(None, None, VerificationLog.Method.SIGNATURE, result, document.name, verifier_ip)
    return Response(build_result(result, None, VerificationLog.Method.SIGNATURE, message, item_details),
                    status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def verify_ocr(request):
    serializer = VerifyOCRSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    image       = serializer.validated_data['image']
    verifier_ip = get_verifier_ip(request)

    try:
        import cv2
        import pytesseract
        import numpy as np
        from PIL import Image
        import io

        image_bytes    = image.read()
        pil_image      = Image.open(io.BytesIO(image_bytes))
        cv_image       = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        gray           = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        gray           = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        extracted_text = pytesseract.image_to_string(gray)
        serial_number  = extracted_text.strip().replace(' ', '').replace('\n', '')

        if not serial_number:
            return Response(build_result(VerificationLog.Result.UNVERIFIABLE, None,
                                         VerificationLog.Method.OCR,
                                         'Could not extract serial number from image.'),
                            status=status.HTTP_200_OK)

        item_data = get_item_by_serial(serial_number)
        if item_data:
            blockchain_hash     = item_data.get('blockchain_hash')
            item_id             = item_data.get('id')
            blockchain_response = check_blockchain(blockchain_hash)
        else:
            blockchain_response = {'exists': False}
            item_id             = None

        if blockchain_response.get('exists'):
            result       = VerificationLog.Result.AUTHENTIC
            message      = f'Banknote is AUTHENTIC. Serial {serial_number} verified.'
            item_details = blockchain_response.get('item_details')
        else:
            result       = VerificationLog.Result.NOT_AUTHENTIC
            message      = f'Serial number {serial_number} not found.'
            item_details = None
            item_id      = None

    except Exception:
        result        = VerificationLog.Result.UNVERIFIABLE
        message       = 'Error processing image.'
        item_details  = None
        item_id       = None
        serial_number = ''

    log_verification(item_id if 'item_id' in locals() else None, None,
                     VerificationLog.Method.OCR, result, serial_number, verifier_ip)
    return Response(build_result(result, item_id if 'item_id' in locals() else None,
                                 VerificationLog.Method.OCR, message, item_details),
                    status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def verify_watermark(request):
    serializer = VerifyWatermarkSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    image       = serializer.validated_data['image']
    verifier_ip = get_verifier_ip(request)

    try:
        from stegano import lsb
        from PIL import Image
        import io

        image_bytes    = image.read()
        pil_image      = Image.open(io.BytesIO(image_bytes))
        hidden_message = lsb.reveal(pil_image)

        if not hidden_message:
            return Response(build_result(VerificationLog.Result.NOT_AUTHENTIC, None,
                                         VerificationLog.Method.WATERMARK,
                                         'No watermark detected.'),
                            status=status.HTTP_200_OK)

        item_id         = uuid.UUID(hidden_message)
        blockchain_hash = get_item_hash(item_id)

        if not blockchain_hash:
            return Response(build_result(VerificationLog.Result.NOT_AUTHENTIC, item_id,
                                         VerificationLog.Method.WATERMARK,
                                         'Watermark found but item not found in records.'),
                            status=status.HTTP_200_OK)

        blockchain_response = check_blockchain(blockchain_hash)

        if blockchain_response.get('exists'):
            result       = VerificationLog.Result.AUTHENTIC
            message      = 'Watermark verified. Document is AUTHENTIC.'
            item_details = blockchain_response.get('item_details')
        else:
            result       = VerificationLog.Result.NOT_AUTHENTIC
            message      = 'Watermark found but blockchain verification failed.'
            item_details = None

    except Exception:
        result       = VerificationLog.Result.UNVERIFIABLE
        message      = 'Could not process watermark.'
        item_details = None
        item_id      = None

    log_verification(item_id if 'item_id' in locals() else None, None,
                     VerificationLog.Method.WATERMARK, result, image.name, verifier_ip)
    return Response(build_result(result, item_id if 'item_id' in locals() else None,
                                 VerificationLog.Method.WATERMARK, message, item_details),
                    status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_document(request):
    """
    Verify official document via Identifiant Unique + Card Number + Fingerprint.
    POST /api/verify/document/
    No authentication required.
    """
    reference_number = request.data.get('reference_number', '').strip()
    card_number      = request.data.get('card_number', '').strip()
    fingerprint_hash = request.data.get('fingerprint_hash', '').strip()
    verifier_ip      = get_verifier_ip(request)

    if not reference_number:
        return Response({'error': 'reference_number is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not card_number:
        return Response({'error': 'card_number is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not fingerprint_hash:
        return Response({'error': 'fingerprint_hash is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Look up item by reference number from item service
    item_data = get_item_by_reference(reference_number)

    if not item_data:
        return Response(build_result(
            VerificationLog.Result.NOT_AUTHENTIC, None, 'DOCUMENT',
            'Identifiant Unique not found in our records.'
        ), status=status.HTTP_200_OK)

    item_id  = item_data.get('id')
    doc_detail = item_data.get('document_detail', {})

    if not doc_detail:
        return Response(build_result(
            VerificationLog.Result.NOT_AUTHENTIC, item_id, 'DOCUMENT',
            'Document details not found.'
        ), status=status.HTTP_200_OK)

    # ── Check card number ──
    stored_card = doc_detail.get('card_number', '')
    if stored_card != card_number:
        log_verification(item_id, None, 'DOCUMENT',
                         VerificationLog.Result.NOT_AUTHENTIC,
                         f'Card number mismatch', verifier_ip)
        return Response(build_result(
            VerificationLog.Result.NOT_AUTHENTIC, item_id, 'DOCUMENT',
            'Card number does not match our records.'
        ), status=status.HTTP_200_OK)

    # ── Check fingerprint ──
    stored_fingerprint = doc_detail.get('fingerprint_hash', '')
    if stored_fingerprint != fingerprint_hash:
        log_verification(item_id, None, 'DOCUMENT',
                         VerificationLog.Result.NOT_AUTHENTIC,
                         f'Fingerprint mismatch', verifier_ip)
        return Response(build_result(
            VerificationLog.Result.NOT_AUTHENTIC, item_id, 'DOCUMENT',
            'Fingerprint does not match. Identity could not be confirmed.'
        ), status=status.HTTP_200_OK)

    # ── All checks passed — verify on blockchain ──
    blockchain_hash     = item_data.get('blockchain_hash')
    blockchain_response = check_blockchain(blockchain_hash)

    if blockchain_response.get('exists'):
        result       = VerificationLog.Result.AUTHENTIC
        message      = 'Document AUTHENTIC. Identity verified on blockchain.'
        item_details = blockchain_response.get('item_details')
    else:
        result       = VerificationLog.Result.NOT_AUTHENTIC
        message      = 'Document found but blockchain verification failed.'
        item_details = None

    log_verification(item_id, None, 'DOCUMENT', result,
                     f'ref:{reference_number}', verifier_ip)

    if result == VerificationLog.Result.AUTHENTIC:
        check_fraud_pattern(item_id)

    return Response(build_result(result, item_id, 'DOCUMENT', message, item_details),
                    status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def verification_history(request, item_id):
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    logs       = VerificationLog.objects.filter(item_id=item_id)
    serializer = VerificationLogSerializer(logs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def report_item(request):
    serializer = ReportItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item_id     = serializer.validated_data['item_id']
    reason      = serializer.validated_data['reason']
    verifier_ip = get_verifier_ip(request)

    FraudFlag.objects.create(
        item_id=item_id,
        verification_count=0,
        window_start=timezone.now(),
        window_end=timezone.now(),
    )

    log_verification(item_id, None, VerificationLog.Method.QR,
                     VerificationLog.Result.NOT_AUTHENTIC,
                     f'Reported by verifier: {reason}', verifier_ip)

    return Response({'message': 'Item reported successfully.'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def fraud_flags(request):
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    flags      = FraudFlag.objects.all()
    serializer = FraudFlagSerializer(flags, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
import os
import uuid
import hashlib
import requests
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Item,
    CertificateDetail,
    PharmaceuticalDetail,
    DocumentDetail,
    BanknoteDetail,
)
from .serializers import (
    ItemSerializer,
    RegisterItemSerializer,
    RevokeItemSerializer,
)
from .auth_helper import require_auth, require_role


# ── Institution type → allowed item category mapping ──
INSTITUTION_CATEGORY_MAP = {
    'UNIVERSITY':   'CERTIFICATE',
    'HOSPITAL':     'PHARMACEUTICAL',
    'MANUFACTURER': 'PHARMACEUTICAL',
    'BANK':         'BANKNOTE',
    'NOTARY':       'DOCUMENT',
}


def generate_hash(field_values):
    return hashlib.sha256(field_values.encode()).hexdigest()


def get_blockchain_category(category):
    mapping = {
        'CERTIFICATE':    'ACADEMIC',
        'PHARMACEUTICAL': 'PHARMA',
        'DOCUMENT':       'DOCUMENT',
        'BANKNOTE':       'CURRENCY',
    }
    return mapping.get(category, category)


def get_allowed_category(institution_id):
    try:
        response = requests.get(
            f"{settings.INSTITUTION_SERVICE_URL}/api/institution/{institution_id}/",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            institution_type = data.get('institution_type')
            return INSTITUTION_CATEGORY_MAP.get(institution_type)
    except Exception:
        pass
    return None


def call_blockchain_service(item_id, category, hash_fields, issuer_id=None, issuer_name=None):
    item_hash = generate_hash(hash_fields)
    blockchain_category = get_blockchain_category(category)

    try:
        response = requests.post(
            f"{settings.BLOCKCHAIN_SERVICE_URL}/api/blockchain/store/",
            json={
                'item_hash':   item_hash,
                'category':    blockchain_category,
                'issuer_id':   str(issuer_id) if issuer_id else 'unknown',
                'issuer_name': issuer_name or 'Unknown Institution',
            },
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            return {
                'hash': item_hash,
                'transaction_hash': data.get('tx_hash', ''),
            }
    except Exception:
        pass

    return {
        'hash': item_hash,
        'transaction_hash': f'mock-tx-{str(item_id)[:8]}',
    }


def call_output_service(item_id, category, item_hash, issuer_id):
    try:
        response = requests.post(
            f"{settings.OUTPUT_SERVICE_URL}/api/output/generate/",
            json={
                'item_id':   str(item_id),
                'item_hash': item_hash,
                'category':  get_blockchain_category(category),
                'issuer_id': str(issuer_id),
            },
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            qr_path = data.get('outputs', {}).get('qr_code_path', '')
            if qr_path and qr_path.startswith('/app/media/'):
                qr_filename = os.path.basename(qr_path)
                qr_url = f"{settings.OUTPUT_SERVICE_URL}/media/qrcodes/{qr_filename}"
            else:
                qr_url = qr_path
            return {
                'qr_code_url':   qr_url,
                'serial_number': data.get('outputs', {}).get('serial_number', ''),
            }
    except Exception:
        pass

    return {
        'qr_code_url':   f'http://localhost:8005/media/qr/{item_id}.png',
        'serial_number': f'QNT-{timezone.now().year}-{category[:4]}-{str(item_id)[:8].upper()}',
    }


def create_detail(item, category, data):
    if category == Item.Category.CERTIFICATE:
        return CertificateDetail.objects.create(
            item=item,
            student_name=data['student_name'],
            matricule=data['matricule'],
            degree=data['degree'],
            institution_name=data['institution_name'],
            graduation_date=data['graduation_date'],
            grade=data['grade'],
        )
    elif category == Item.Category.PHARMACEUTICAL:
        return PharmaceuticalDetail.objects.create(
            item=item,
            drug_name=data['drug_name'],
            batch_number=data['batch_number'],
            manufacturer=data['manufacturer'],
            production_date=data['production_date'],
            expiry_date=data['expiry_date'],
            factory_location=data['factory_location'],
        )
    elif category == Item.Category.DOCUMENT:
        return DocumentDetail.objects.create(
           item=item,
           document_type=data['document_type'],
           owner_name=data['owner_name'],
           issuing_authority=data['issuing_authority'],
           reference_number=data['reference_number'],
           card_number=data.get('card_number', ''),
           location=data['location'],
           issue_date=data['issue_date'],
           fingerprint_hash=data.get('fingerprint_hash', ''),
           credential_id=data.get('credential_id', ''),
           owner_surname=data.get('owner_surname', ''),
           owner_given_names=data.get('owner_given_names', ''),
           date_of_birth=data.get('date_of_birth'),
           date_of_expiry=data.get('date_of_expiry'),
           sex=data.get('sex', ''),
           father_name=data.get('father_name', ''),
           mother_name=data.get('mother_name', ''),
           place_of_birth=data.get('place_of_birth', ''),
           occupation=data.get('occupation', ''),
           height=data.get('height', ''),
           mrz_line1=data.get('mrz_line1', ''),
           mrz_line2=data.get('mrz_line2', ''),
           mrz_line3=data.get('mrz_line3', ''),
        )
    elif category == Item.Category.BANKNOTE:
        return BanknoteDetail.objects.create(
            item=item,
            currency=data['currency'],
            denomination=data['denomination'],
            serial_number=data['serial_number'],
            series=data['series'],
            issue_date=data['issue_date'],
            issuing_bank=data['issuing_bank'],
        )


@swagger_auto_schema(
    method='post',
    request_body=RegisterItemSerializer,
    responses={201: 'Item submitted for approval'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_item(request):
    user, error = require_role(request, 'ISSUER')
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    issuer_id = user.get('user_id')

    serializer = RegisterItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    category = data['category']

    institution_id_str = request.data.get('institution_id')
    if institution_id_str:
        allowed_category = get_allowed_category(institution_id_str)
        if allowed_category and category != allowed_category:
            return Response(
                {'error': f'Your institution can only register {allowed_category} items, not {category}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    item = Item.objects.create(
        issuer_id=uuid.UUID(issuer_id),
        institution_id=uuid.UUID(institution_id_str or str(uuid.uuid4())),
        category=category,
        status=Item.Status.PENDING,
    )

    create_detail(item, category, data)

    serializer = ItemSerializer(item)
    return Response(
        {
            'message': 'Item submitted for approval. An admin will review it shortly.',
            'item': serializer.data,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['PUT'])
@permission_classes([AllowAny])
def approve_item(request, item_id):
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    admin_id = user.get('user_id')

    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

    if item.status != Item.Status.PENDING:
        return Response(
            {'error': f'Item is {item.status}, not PENDING.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    detail = (
        item.certificate_detail if hasattr(item, 'certificate_detail') else
        item.pharmaceutical_detail if hasattr(item, 'pharmaceutical_detail') else
        item.document_detail if hasattr(item, 'document_detail') else
        item.banknote_detail if hasattr(item, 'banknote_detail') else None
    )

    if not detail:
        return Response({'error': 'Item detail not found.'}, status=status.HTTP_400_BAD_REQUEST)

    hash_fields = detail.get_hash_fields()

    # ── Look up institution name ──
    institution_name = 'Unknown Institution'
    try:
        inst_response = requests.get(
            f"{settings.INSTITUTION_SERVICE_URL}/api/institution/{item.institution_id}/",
            timeout=5
        )
        if inst_response.status_code == 200:
            institution_name = inst_response.json().get('name', 'Unknown Institution')
    except Exception:
        pass

    blockchain_response = call_blockchain_service(
        item.id, item.category, hash_fields,
        issuer_id=str(item.issuer_id),
        issuer_name=institution_name
    )

    output_response = call_output_service(
        item.id, item.category,
        blockchain_response.get('hash'),
        str(item.issuer_id)
    )

    item.status           = Item.Status.REGISTERED
    item.blockchain_hash  = blockchain_response.get('hash')
    item.transaction_hash = blockchain_response.get('transaction_hash')
    item.qr_code_url      = output_response.get('qr_code_url')
    item.serial_number    = output_response.get('serial_number')
    item.approved_at      = timezone.now()
    item.approved_by      = uuid.UUID(admin_id)
    item.save()

    serializer = ItemSerializer(item)
    return Response(
        {
            'message': 'Item approved and registered on blockchain.',
            'item': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['PUT'])
@permission_classes([AllowAny])
def reject_item(request, item_id):
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

    if item.status != Item.Status.PENDING:
        return Response(
            {'error': f'Item is {item.status}, not PENDING.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reason = request.data.get('reason', '')
    if not reason:
        return Response({'error': 'Rejection reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

    item.status        = Item.Status.REJECTED
    item.rejected_at   = timezone.now()
    item.reject_reason = reason
    item.save()

    serializer = ItemSerializer(item)
    return Response(
        {
            'message': 'Item rejected.',
            'item': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def pending_items(request):
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    items = Item.objects.filter(status=Item.Status.PENDING)
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def my_items(request):
    user, error = require_auth(request)
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    issuer_id = user.get('user_id')
    items = Item.objects.filter(issuer_id=issuer_id)
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def item_detail(request, item_id):
    token = request.META.get('HTTP_AUTHORIZATION', '')

    if token:
        user, error = require_auth(request)
        if error:
            return Response(error, status=status.HTTP_401_UNAUTHORIZED)
        role = user.get('role')
        issuer_id = user.get('user_id')
        try:
            if role == 'ADMIN':
                item = Item.objects.get(id=item_id)
            else:
                item = Item.objects.get(id=item_id, issuer_id=issuer_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='put',
    request_body=RevokeItemSerializer,
    responses={200: 'Item revoked successfully'}
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def revoke_item(request, item_id):
    user, error = require_role(request, 'ISSUER')
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    issuer_id = user.get('user_id')

    try:
        item = Item.objects.get(id=item_id, issuer_id=issuer_id)
    except Item.DoesNotExist:
        return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

    if item.status != Item.Status.REGISTERED:
        return Response(
            {'error': 'Only registered items can be revoked.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = RevokeItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item.status        = Item.Status.REVOKED
    item.revoked_at    = timezone.now()
    item.revoke_reason = serializer.validated_data['reason']
    item.save()

    return Response(
        {
            'message': 'Item revoked successfully.',
            'item_id': str(item.id),
            'status':  item.status,
            'revoked_at': item.revoked_at,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def all_items(request):
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    category      = request.query_params.get('category')
    status_filter = request.query_params.get('status')

    items = Item.objects.all()
    if category:
        items = items.filter(category=category)
    if status_filter:
        items = items.filter(status=status_filter)

    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def item_by_serial(request, serial_number):
    try:
        item = Item.objects.get(serial_number=serial_number)
    except Item.DoesNotExist:
        return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def item_by_reference(request, reference_number):
    """
    Get DOCUMENT item by reference number (Identifiant Unique).
    GET /api/items/reference/{reference_number}/
    No authentication required — used by verification service.
    """
    try:
        item = Item.objects.get(
            document_detail__reference_number=reference_number,
            category=Item.Category.DOCUMENT,
            status=Item.Status.REGISTERED,
        )
    except Item.DoesNotExist:
        return Response({'error': 'Document not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)
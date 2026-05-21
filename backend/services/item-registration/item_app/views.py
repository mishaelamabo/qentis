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


def generate_hash(field_values):
    """Generate SHA-256 hash from concatenated field values."""
    return hashlib.sha256(field_values.encode()).hexdigest()


def get_blockchain_category(category):
    """Map item registration categories to blockchain categories."""
    mapping = {
        'CERTIFICATE':    'ACADEMIC',
        'PHARMACEUTICAL': 'PHARMA',
        'DOCUMENT':       'DOCUMENT',
        'BANKNOTE':       'CURRENCY',
    }
    return mapping.get(category, category)


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
                'category':  category,
                'issuer_id': str(issuer_id),
            },
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            return {
                'qr_code_url':   data.get('outputs', {}).get('qr_code_path', ''),
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
            location=data['location'],
            issue_date=data['issue_date'],
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
    responses={201: 'Item registered successfully'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_item(request):
    """
    Issuer registers a new item for authentication.
    POST /api/items/register/
    JWT required — must be ISSUER role.
    """
    user, error = require_role(request, 'ISSUER')
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    issuer_id = user.get('user_id')

    serializer = RegisterItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    data = serializer.validated_data
    category = data['category']

    item = Item.objects.create(
        issuer_id=uuid.UUID(issuer_id),
        institution_id=uuid.UUID(
            request.data.get('institution_id', str(uuid.uuid4()))
        ),
        category=category,
        status=Item.Status.REGISTERED,
    )

    detail = create_detail(item, category, data)
    hash_fields = detail.get_hash_fields()

    blockchain_response = call_blockchain_service(
        item.id, category, hash_fields,
        issuer_id=issuer_id,
        issuer_name=request.data.get('institution_name', 'Unknown Institution')
    )

    output_response = call_output_service(
        item.id, category,
        blockchain_response.get('hash'),
        issuer_id
    )

    item.blockchain_hash = blockchain_response.get('hash')
    item.transaction_hash = blockchain_response.get('transaction_hash')
    item.qr_code_url = output_response.get('qr_code_url')
    item.serial_number = output_response.get('serial_number')
    item.save()

    serializer = ItemSerializer(item)
    return Response(
        {
            'message': 'Item registered successfully.',
            'item': serializer.data,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def my_items(request):
    """
    Issuer views all their registered items.
    GET /api/items/my-items/
    JWT required.
    """
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
    """
    Get full details of one item.
    GET /api/items/{item_id}/
    JWT optional — internal service calls work without token.
    """
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
            return Response(
                {'error': 'Item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Internal service call — no token, return item freely
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response(
                {'error': 'Item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

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
    """
    Issuer revokes a registered item.
    PUT /api/items/{item_id}/revoke/
    JWT required.
    """
    user, error = require_role(request, 'ISSUER')
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    issuer_id = user.get('user_id')

    try:
        item = Item.objects.get(id=item_id, issuer_id=issuer_id)
    except Item.DoesNotExist:
        return Response(
            {'error': 'Item not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if item.status == Item.Status.REVOKED:
        return Response(
            {'error': 'Item is already revoked.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = RevokeItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    item.status = Item.Status.REVOKED
    item.revoked_at = timezone.now()
    item.revoke_reason = serializer.validated_data['reason']
    item.save()

    return Response(
        {
            'message': 'Item revoked successfully.',
            'item_id': str(item.id),
            'status': item.status,
            'revoked_at': item.revoked_at,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def all_items(request):
    """
    Admin views all registered items.
    GET /api/items/all/
    Admin JWT required.
    """
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    category = request.query_params.get('category')
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
    """
    Get item details by serial number.
    GET /api/items/serial/{serial_number}/
    Called by Verification Service for serial/QR verification.
    No authentication required.
    """
    try:
        item = Item.objects.get(serial_number=serial_number)
    except Item.DoesNotExist:
        return Response(
            {'error': 'Item not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ItemSerializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)
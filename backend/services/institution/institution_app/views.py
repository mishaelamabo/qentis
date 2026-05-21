import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Institution, InstitutionDocument
from .serializers import (
    InstitutionSerializer,
    InstitutionApplySerializer,
    AdminInstitutionSerializer,
)
from .auth_helper import require_auth, require_role


@swagger_auto_schema(
    method='post',
    request_body=InstitutionApplySerializer,
    responses={201: 'Application submitted successfully'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def apply(request):
    """
    Issuer submits institution application.
    POST /api/institution/apply/
    JWT token required.
    """
    user, error = require_role(request, 'ISSUER')
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    user_id = user.get('user_id')

    existing = Institution.objects.filter(user_id=user_id).first()
    if existing:
        return Response(
            {
                'error': 'You already have an application.',
                'status': existing.status,
                'application_id': str(existing.id)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = InstitutionApplySerializer(data=request.data)
    if serializer.is_valid():
        institution = serializer.save(
            user_id=uuid.UUID(user_id),
            status=Institution.Status.PENDING
        )

        documents = request.FILES.getlist('documents')
        doc_type = request.data.get('document_type', 'OTHER')
        for doc in documents:
            InstitutionDocument.objects.create(
                institution=institution,
                file_path=doc,
                document_type=doc_type
            )

        return Response(
            {
                'message': 'Application submitted successfully.',
                'application_id': str(institution.id),
                'status': institution.status,
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def application_status(request):
    """
    Issuer checks their own application status.
    GET /api/institution/status/
    JWT token required.
    """
    user, error = require_auth(request)
    if error:
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    user_id = user.get('user_id')

    institution = Institution.objects.filter(user_id=user_id).first()

    if not institution:
        return Response(
            {'error': 'No application found for this user.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = InstitutionSerializer(institution)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def pending_applications(request):
    """
    Admin views all pending applications.
    GET /api/institution/pending/
    Admin JWT required.
    """
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    institutions = Institution.objects.filter(
        status=Institution.Status.PENDING
    )
    serializer = AdminInstitutionSerializer(institutions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def all_institutions(request):
    """
    Admin views all institutions.
    GET /api/institution/all/
    Admin JWT required.
    """
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    institutions = Institution.objects.all()
    serializer = AdminInstitutionSerializer(institutions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='put',
    responses={200: 'Institution approved successfully'}
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def approve_institution(request, institution_id):
    """
    Admin approves an institution application.
    PUT /api/institution/{id}/approve/
    Admin JWT required.
    """
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    try:
        institution = Institution.objects.get(id=institution_id)
    except Institution.DoesNotExist:
        return Response(
            {'error': 'Institution not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if institution.status != Institution.Status.PENDING:
        return Response(
            {'error': f'Institution is already {institution.status}.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    institution.status = Institution.Status.APPROVED
    institution.approved_by = uuid.UUID(user.get('user_id'))
    institution.approved_at = timezone.now()
    institution.save()

    serializer = InstitutionSerializer(institution)
    return Response(
        {
            'message': 'Institution approved successfully.',
            'institution': serializer.data
        },
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['reason'],
        properties={
            'reason': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={200: 'Institution rejected'}
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def reject_institution(request, institution_id):
    """
    Admin rejects an institution application.
    PUT /api/institution/{id}/reject/
    Admin JWT required.
    """
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    try:
        institution = Institution.objects.get(id=institution_id)
    except Institution.DoesNotExist:
        return Response(
            {'error': 'Institution not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    reason = request.data.get('reason')
    if not reason:
        return Response(
            {'error': 'Rejection reason is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    institution.status = Institution.Status.REJECTED
    institution.approved_by = uuid.UUID(user.get('user_id'))
    institution.approved_at = timezone.now()
    institution.rejection_reason = reason
    institution.save()

    serializer = InstitutionSerializer(institution)
    return Response(
        {
            'message': 'Institution rejected.',
            'institution': serializer.data
        },
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['reason'],
        properties={
            'reason': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={200: 'Institution revoked'}
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def revoke_institution(request, institution_id):
    """
    Admin revokes an approved institution.
    PUT /api/institution/{id}/revoke/
    Admin JWT required.
    """
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    try:
        institution = Institution.objects.get(id=institution_id)
    except Institution.DoesNotExist:
        return Response(
            {'error': 'Institution not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if institution.status != Institution.Status.APPROVED:
        return Response(
            {'error': 'Only approved institutions can be revoked.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reason = request.data.get('reason')
    if not reason:
        return Response(
            {'error': 'Revocation reason is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    institution.status = Institution.Status.REVOKED
    institution.approved_by = uuid.UUID(user.get('user_id'))
    institution.rejection_reason = reason
    institution.save()

    serializer = InstitutionSerializer(institution)
    return Response(
        {
            'message': 'Institution revoked.',
            'institution': serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def institution_detail(request, institution_id):
    """
    Get full details of one institution.
    GET /api/institution/{id}/
    Admin JWT required.
    """
    user, error = require_role(request, 'ADMIN')
    if error:
        return Response(error, status=status.HTTP_403_FORBIDDEN)

    try:
        institution = Institution.objects.get(id=institution_id)
    except Institution.DoesNotExist:
        return Response(
            {'error': 'Institution not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = AdminInstitutionSerializer(institution)
    return Response(serializer.data, status=status.HTTP_200_OK)
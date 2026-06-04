import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from item_app.models import (
    Item, CertificateDetail, PharmaceuticalDetail, DocumentDetail, BanknoteDetail
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def issuer_headers(user_id=None):
    return {
        'HTTP_X_USER_ID':   str(user_id or uuid.uuid4()),
        'HTTP_X_USER_ROLE': 'ISSUER',
    }

def admin_headers(user_id=None):
    return {
        'HTTP_X_USER_ID':   str(user_id or uuid.uuid4()),
        'HTTP_X_USER_ROLE': 'ADMIN',
    }


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestItemModel(TestCase):

    def setUp(self):
        self.issuer_id = uuid.uuid4()
        self.institution_id = uuid.uuid4()
        self.item = Item.objects.create(
            issuer_id=self.issuer_id,
            institution_id=self.institution_id,
            category=Item.Category.CERTIFICATE,
            status=Item.Status.REGISTERED,
        )

    def test_item_created_successfully(self):
        self.assertIsNotNone(self.item.id)
        self.assertEqual(self.item.category, Item.Category.CERTIFICATE)

    def test_item_default_status_is_pending(self):
        item = Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
        )
        self.assertEqual(item.status, Item.Status.PENDING)

    def test_item_str_representation(self):
        self.assertIn('CERTIFICATE', str(self.item))

    def test_item_str_contains_category(self):
        item = Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=Item.Category.PHARMACEUTICAL,
        )
        self.assertIn('PHARMACEUTICAL', str(item))

    def test_item_has_registered_at_timestamp(self):
        self.assertIsNotNone(self.item.registered_at)

    def test_item_revoked_at_is_none_by_default(self):
        item = Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=Item.Category.BANKNOTE,
        )
        self.assertIsNone(item.revoked_at)

    def test_certificate_detail_cascade_delete(self):
        CertificateDetail.objects.create(
            item=self.item,
            student_name='John Doe',
            matricule='MAT001',
            degree='BSc Computer Science',
            institution_name='ICT University',
            graduation_date='2024-06-15',
            grade='First Class',
        )
        self.assertEqual(CertificateDetail.objects.filter(item=self.item).count(), 1)
        self.item.delete()
        self.assertEqual(CertificateDetail.objects.count(), 0)

    def test_certificate_get_hash_fields(self):
        detail = CertificateDetail.objects.create(
            item=self.item,
            student_name='John Doe',
            matricule='MAT001',
            degree='BSc',
            institution_name='ICT University',
            graduation_date='2024-06-15',
            grade='First Class',
        )
        h = detail.get_hash_fields()
        self.assertIn('John Doe', h)
        self.assertIn('MAT001', h)
        self.assertIn('ICT University', h)

    def test_pharmaceutical_get_hash_fields(self):
        item = Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=Item.Category.PHARMACEUTICAL,
        )
        detail = PharmaceuticalDetail.objects.create(
            item=item,
            drug_name='Paracetamol',
            batch_number='BATCH001',
            manufacturer='PharmaLab',
            production_date='2024-01-01',
            expiry_date='2026-01-01',
            factory_location='Yaounde',
        )
        h = detail.get_hash_fields()
        self.assertIn('Paracetamol', h)
        self.assertIn('BATCH001', h)

    def test_document_get_hash_fields(self):
        item = Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=Item.Category.DOCUMENT,
        )
        detail = DocumentDetail.objects.create(
            item=item,
            document_type='Passport',
            owner_name='Jane Smith',
            issuing_authority='Ministry',
            reference_number='REF001',
            location='Yaounde',
            issue_date='2024-01-15',
        )
        h = detail.get_hash_fields()
        self.assertIn('Jane Smith', h)
        self.assertIn('REF001', h)

    def test_banknote_get_hash_fields(self):
        item = Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=Item.Category.BANKNOTE,
        )
        detail = BanknoteDetail.objects.create(
            item=item,
            currency='XAF',
            denomination='5000.00',
            serial_number='BN001',
            series='2024',
            issue_date='2024-01-01',
            issuing_bank='BEAC',
        )
        h = detail.get_hash_fields()
        self.assertIn('XAF', h)
        self.assertIn('BN001', h)


# ---------------------------------------------------------------------------
# Detail __str__ tests
# ---------------------------------------------------------------------------

class TestDetailStrRepresentations(TestCase):

    def _make_item(self, category):
        return Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=category,
        )

    def test_certificate_detail_str(self):
        item = self._make_item(Item.Category.CERTIFICATE)
        detail = CertificateDetail.objects.create(
            item=item, student_name='Alice Smith', matricule='M001',
            degree='BSc CS', institution_name='ICT',
            graduation_date='2024-06-01', grade='First',
        )
        self.assertIn('Alice Smith', str(detail))

    def test_pharmaceutical_detail_str(self):
        item = self._make_item(Item.Category.PHARMACEUTICAL)
        detail = PharmaceuticalDetail.objects.create(
            item=item, drug_name='Aspirin', batch_number='B001',
            manufacturer='Lab', production_date='2024-01-01',
            expiry_date='2026-01-01', factory_location='Douala',
        )
        self.assertIn('Aspirin', str(detail))

    def test_document_detail_str(self):
        item = self._make_item(Item.Category.DOCUMENT)
        detail = DocumentDetail.objects.create(
            item=item, document_type='Passport', owner_name='Bob Jones',
            issuing_authority='Ministry', reference_number='R001',
            location='Yaounde', issue_date='2024-01-01',
        )
        self.assertIn('Passport', str(detail))

    def test_banknote_detail_str(self):
        item = self._make_item(Item.Category.BANKNOTE)
        detail = BanknoteDetail.objects.create(
            item=item, currency='XAF', denomination='5000.00',
            serial_number='BN999', series='2024',
            issue_date='2024-01-01', issuing_bank='BEAC',
        )
        self.assertIn('XAF', str(detail))


# ---------------------------------------------------------------------------
# Register item endpoint
# ---------------------------------------------------------------------------

class TestRegisterItemEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.issuer_id = str(uuid.uuid4())
        self.institution_id = str(uuid.uuid4())
        self.certificate_data = {
            'category': 'CERTIFICATE',
            'institution_id': self.institution_id,
            'student_name': 'John Doe',
            'matricule': 'MAT001',
            'degree': 'BSc Computer Science',
            'institution_name': 'ICT University',
            'graduation_date': '2024-06-15',
            'grade': 'First Class',
        }

    def test_issuer_can_register_certificate(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.post('/api/items/register/', data=self.certificate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item']['category'], 'CERTIFICATE')

    def test_register_creates_certificate_detail(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.post('/api/items/register/', data=self.certificate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item_id = response.data['item']['id']
        self.assertTrue(CertificateDetail.objects.filter(item_id=item_id).exists())

    def test_register_item_status_is_pending(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.post('/api/items/register/', data=self.certificate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item']['status'], 'PENDING')

    def test_register_pharmaceutical(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.post('/api/items/register/', data={
            'category': 'PHARMACEUTICAL',
            'institution_id': self.institution_id,
            'drug_name': 'Paracetamol 500mg',
            'batch_number': 'BATCH001',
            'manufacturer': 'PharmaLab',
            'production_date': '2024-01-01',
            'expiry_date': '2026-01-01',
            'factory_location': 'Yaounde, Cameroon',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item']['category'], 'PHARMACEUTICAL')

    def test_register_document(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.post('/api/items/register/', data={
            'category': 'DOCUMENT',
            'institution_id': self.institution_id,
            'document_type': 'Passport',
            'owner_name': 'Jane Smith',
            'issuing_authority': 'Ministry of External Relations',
            'reference_number': 'REF001',
            'location': 'Yaounde',
            'issue_date': '2024-01-15',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item']['category'], 'DOCUMENT')

    def test_register_banknote(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.post('/api/items/register/', data={
            'category': 'BANKNOTE',
            'institution_id': self.institution_id,
            'currency': 'XAF',
            'denomination': '5000.00',
            'serial_number': 'BN001',
            'series': '2024',
            'issue_date': '2024-01-01',
            'issuing_bank': 'BEAC',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item']['category'], 'BANKNOTE')

    def test_register_fails_without_user_id(self):
        # No headers at all → require_role fails → 401
        response = self.client.post('/api/items/register/', data=self.certificate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_fails_for_non_issuer(self):
        self.client.credentials(
            HTTP_X_USER_ID=self.issuer_id,
            HTTP_X_USER_ROLE='VERIFIER',
        )
        response = self.client.post('/api/items/register/', data=self.certificate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_fails_with_missing_required_fields(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.post('/api/items/register/', data={
            'category': 'CERTIFICATE',
            'student_name': 'John Doe',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# My items endpoint
# ---------------------------------------------------------------------------

class TestMyItemsEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.issuer_id = str(uuid.uuid4())
        Item.objects.create(
            issuer_id=uuid.UUID(self.issuer_id),
            institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
        )

    def test_issuer_can_view_own_items(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.get('/api/items/my-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_returns_empty_list_for_issuer_with_no_items(self):
        new_id = str(uuid.uuid4())
        self.client.credentials(HTTP_X_USER_ID=new_id, HTTP_X_USER_ROLE='ISSUER')
        response = self.client.get('/api/items/my-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_fails_without_user_id_header(self):
        response = self.client.get('/api/items/my-items/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_returns_own_items(self):
        other_issuer_id = str(uuid.uuid4())
        Item.objects.create(
            issuer_id=uuid.UUID(other_issuer_id),
            institution_id=uuid.uuid4(),
            category=Item.Category.PHARMACEUTICAL,
        )
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.get('/api/items/my-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


# ---------------------------------------------------------------------------
# Item detail endpoint
# ---------------------------------------------------------------------------

class TestItemDetailEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.issuer_id = str(uuid.uuid4())
        self.item = Item.objects.create(
            issuer_id=uuid.UUID(self.issuer_id),
            institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
        )

    def test_issuer_can_view_own_item(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.item.id))

    def test_admin_can_view_any_item(self):
        self.client.credentials(**admin_headers())
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_issuer_cannot_view_item(self):
        self.client.credentials(**issuer_headers())  # different random issuer
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_item_returns_404(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.get(f'/api/items/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_can_view_item_without_token(self):
        # No auth header → item_detail falls into the else branch and returns item
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Revoke item endpoint
# ---------------------------------------------------------------------------

class TestRevokeItemEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.issuer_id = str(uuid.uuid4())
        self.item = Item.objects.create(
            issuer_id=uuid.UUID(self.issuer_id),
            institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
            status=Item.Status.REGISTERED,
        )

    def test_issuer_can_revoke_own_item(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.put(f'/api/items/{self.item.id}/revoke/', data={
            'reason': 'Certificate was issued in error and must be cancelled.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.Status.REVOKED)

    def test_revoke_sets_revoked_at_timestamp(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        self.client.put(f'/api/items/{self.item.id}/revoke/', data={
            'reason': 'Certificate was issued in error and must be cancelled.',
        }, format='json')
        self.item.refresh_from_db()
        self.assertIsNotNone(self.item.revoked_at)

    def test_revoke_fails_with_short_reason(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.put(f'/api/items/{self.item.id}/revoke/', data={
            'reason': 'Short',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revoke_fails_without_reason(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.put(f'/api/items/{self.item.id}/revoke/', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_revoke_pending_item(self):
        pending_item = Item.objects.create(
            issuer_id=uuid.UUID(self.issuer_id),
            institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
            status=Item.Status.PENDING,
        )
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.put(f'/api/items/{pending_item.id}/revoke/', data={
            'reason': 'Trying to revoke a pending item should fail here.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_issuer_cannot_revoke_item(self):
        self.client.credentials(**issuer_headers())  # different random issuer
        response = self.client.put(f'/api/items/{self.item.id}/revoke/', data={
            'reason': 'Trying to revoke someone elses item here.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_nonexistent_item_returns_404(self):
        self.client.credentials(**issuer_headers(self.issuer_id))
        response = self.client.put(f'/api/items/{uuid.uuid4()}/revoke/', data={
            'reason': 'This item does not exist in the database.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_fails_without_user_id_header(self):
        response = self.client.put(f'/api/items/{self.item.id}/revoke/', data={
            'reason': 'Testing missing user id header scenario here.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# All items endpoint
# ---------------------------------------------------------------------------

class TestAllItemsEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        Item.objects.create(
            issuer_id=uuid.uuid4(), institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
        )
        Item.objects.create(
            issuer_id=uuid.uuid4(), institution_id=uuid.uuid4(),
            category=Item.Category.PHARMACEUTICAL,
        )
        revoked = Item.objects.create(
            issuer_id=uuid.uuid4(), institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
        )
        revoked.status = Item.Status.REVOKED
        revoked.save()

    def test_admin_can_view_all_items(self):
        self.client.credentials(**admin_headers())
        response = self.client.get('/api/items/all/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_non_admin_cannot_view_all_items(self):
        self.client.credentials(HTTP_X_USER_ID=str(uuid.uuid4()), HTTP_X_USER_ROLE='ISSUER')
        response = self.client.get('/api/items/all/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_role_header_returns_403(self):
        response = self.client.get('/api/items/all/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_filter_by_category(self):
        self.client.credentials(**admin_headers())
        response = self.client.get('/api/items/all/?category=PHARMACEUTICAL')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], 'PHARMACEUTICAL')

    def test_admin_can_filter_by_status(self):
        self.client.credentials(**admin_headers())
        response = self.client.get('/api/items/all/?status=REVOKED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'REVOKED')

    def test_admin_can_filter_by_category_and_status(self):
        self.client.credentials(**admin_headers())
        response = self.client.get('/api/items/all/?category=CERTIFICATE&status=PENDING')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


# ---------------------------------------------------------------------------
# Pending items endpoint
# ---------------------------------------------------------------------------

class TestPendingItemsEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        Item.objects.create(
            issuer_id=uuid.uuid4(), institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE, status=Item.Status.PENDING,
        )
        Item.objects.create(
            issuer_id=uuid.uuid4(), institution_id=uuid.uuid4(),
            category=Item.Category.BANKNOTE, status=Item.Status.REGISTERED,
        )

    def test_admin_can_view_pending_items(self):
        self.client.credentials(**admin_headers())
        response = self.client.get('/api/items/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_non_admin_cannot_view_pending(self):
        self.client.credentials(HTTP_X_USER_ID=str(uuid.uuid4()), HTTP_X_USER_ROLE='ISSUER')
        response = self.client.get('/api/items/pending/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pending_only_returns_pending_items(self):
        self.client.credentials(**admin_headers())
        response = self.client.get('/api/items/pending/')
        for item in response.data:
            self.assertEqual(item['status'], 'PENDING')


# ---------------------------------------------------------------------------
# Approve / Reject endpoints
# ---------------------------------------------------------------------------

class TestApproveItemEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_id = str(uuid.uuid4())
        self.issuer_id = uuid.uuid4()
        self.item = Item.objects.create(
            issuer_id=self.issuer_id,
            institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
            status=Item.Status.PENDING,
        )
        CertificateDetail.objects.create(
            item=self.item,
            student_name='John Doe', matricule='MAT001',
            degree='BSc CS', institution_name='ICT University',
            graduation_date='2024-06-15', grade='First Class',
        )

    def test_admin_can_approve_item(self):
        self.client.credentials(**admin_headers(self.admin_id))
        response = self.client.put(f'/api/items/{self.item.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.Status.REGISTERED)

    def test_non_admin_cannot_approve(self):
        self.client.credentials(**issuer_headers())
        response = self.client.put(f'/api/items/{self.item.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_approve_already_registered_item(self):
        self.item.status = Item.Status.REGISTERED
        self.item.save()
        self.client.credentials(**admin_headers(self.admin_id))
        response = self.client.put(f'/api/items/{self.item.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_nonexistent_item_returns_404(self):
        self.client.credentials(**admin_headers(self.admin_id))
        response = self.client.put(f'/api/items/{uuid.uuid4()}/approve/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRejectItemEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_id = str(uuid.uuid4())
        self.item = Item.objects.create(
            issuer_id=uuid.uuid4(),
            institution_id=uuid.uuid4(),
            category=Item.Category.CERTIFICATE,
            status=Item.Status.PENDING,
        )

    def test_admin_can_reject_item(self):
        self.client.credentials(**admin_headers(self.admin_id))
        response = self.client.put(f'/api/items/{self.item.id}/reject/', data={
            'reason': 'Documents are incomplete.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.Status.REJECTED)

    def test_reject_fails_without_reason(self):
        self.client.credentials(**admin_headers(self.admin_id))
        response = self.client.put(f'/api/items/{self.item.id}/reject/', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_reject(self):
        self.client.credentials(**issuer_headers())
        response = self.client.put(f'/api/items/{self.item.id}/reject/', data={
            'reason': 'Not valid.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_nonexistent_item_returns_404(self):
        self.client.credentials(**admin_headers(self.admin_id))
        response = self.client.put(f'/api/items/{uuid.uuid4()}/reject/', data={
            'reason': 'Not valid.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_reject_already_registered_item(self):
        self.item.status = Item.Status.REGISTERED
        self.item.save()
        self.client.credentials(**admin_headers(self.admin_id))
        response = self.client.put(f'/api/items/{self.item.id}/reject/', data={
            'reason': 'Already approved.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# View helper functions
# ---------------------------------------------------------------------------

class TestViewHelperFunctions(TestCase):

    def test_generate_hash_returns_64_char_hex(self):
        from item_app.views import generate_hash
        h = generate_hash('some field data here')
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in h))

    def test_generate_hash_is_deterministic(self):
        from item_app.views import generate_hash
        self.assertEqual(generate_hash('abc'), generate_hash('abc'))

    def test_generate_hash_differs_for_different_inputs(self):
        from item_app.views import generate_hash
        self.assertNotEqual(generate_hash('abc'), generate_hash('xyz'))

    def test_call_blockchain_service_returns_mock_on_connection_failure(self):
        from item_app.views import call_blockchain_service
        result = call_blockchain_service(uuid.uuid4(), 'CERTIFICATE', 'fields')
        self.assertIn('hash', result)
        self.assertIn('transaction_hash', result)
        self.assertIn('mock-tx', result['transaction_hash'])

    def test_call_blockchain_service_success_path(self):
        from item_app.views import call_blockchain_service
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {'tx_hash': '0xdeadbeef123'}
        with patch('item_app.views.requests.post', return_value=mock_resp):
            result = call_blockchain_service(
                uuid.uuid4(), 'CERTIFICATE', 'fields',
                issuer_id='user-123', issuer_name='Test University',
            )
        self.assertEqual(result['transaction_hash'], '0xdeadbeef123')

    def test_call_output_service_returns_mock_on_connection_failure(self):
        from item_app.views import call_output_service
        result = call_output_service(uuid.uuid4(), 'CERTIFICATE', 'somehash', 'issuer-1')
        self.assertIn('qr_code_url', result)
        self.assertIn('serial_number', result)

    def test_call_output_service_success_path(self):
        from item_app.views import call_output_service
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {
            'outputs': {
                'qr_code_url': 'http://example.com/qr.png',
                'serial_number': 'QNT-2024-CERT-TEST01',
            }
        }
        with patch('item_app.views.requests.post', return_value=mock_resp):
            result = call_output_service(uuid.uuid4(), 'CERTIFICATE', 'somehash', 'issuer-1')
        self.assertEqual(result['serial_number'], 'QNT-2024-CERT-TEST01')
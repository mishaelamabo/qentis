from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from .models import BlockchainRecord


class TestBlockchainRecordModel(TestCase):

    def test_record_created_successfully(self):
        record = BlockchainRecord.objects.create(
            item_hash='a' * 64, category=BlockchainRecord.Category.ACADEMIC,
            issuer_id='issuer-001', issuer_name='ICT University', tx_hash='0xabc',
        )
        self.assertIsNotNone(record.id)
        self.assertEqual(record.status, BlockchainRecord.Status.STORED)

    def test_record_str_representation(self):
        record = BlockchainRecord.objects.create(
            item_hash='b' * 64, category=BlockchainRecord.Category.PHARMA,
            issuer_id='issuer-002', issuer_name='PharmaLab', tx_hash='0xdef',
        )
        self.assertIn('PHARMA', str(record))
        self.assertIn('STORED', str(record))

    def test_record_default_status_is_stored(self):
        record = BlockchainRecord.objects.create(
            item_hash='c' * 64, category=BlockchainRecord.Category.DOCUMENT,
            issuer_id='issuer-003', issuer_name='Ministry', tx_hash='0x123',
        )
        self.assertEqual(record.status, BlockchainRecord.Status.STORED)

    def test_record_revoke_reason_blank_by_default(self):
        record = BlockchainRecord.objects.create(
            item_hash='d' * 64, category=BlockchainRecord.Category.CURRENCY,
            issuer_id='issuer-004', issuer_name='BEAC', tx_hash='0x456',
        )
        self.assertEqual(record.revoke_reason, '')

    def test_record_has_created_at(self):
        record = BlockchainRecord.objects.create(
            item_hash='e' * 64, category=BlockchainRecord.Category.ACADEMIC,
            issuer_id='issuer-005', issuer_name='ICT', tx_hash='0x789',
        )
        self.assertIsNotNone(record.created_at)


class TestStoreHashEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/blockchain/store/'
        self.valid_payload = {
            'item_hash':   'a' * 64,
            'category':    'ACADEMIC',
            'issuer_id':   'issuer-uuid-001',
            'issuer_name': 'ICT University',
        }

    @patch('blockchain_app.views.store_hash_on_chain')
    def test_store_hash_success(self, mock_store):
        mock_store.return_value = '0xabc123'
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tx_hash', response.data)
        self.assertTrue(BlockchainRecord.objects.filter(item_hash='a' * 64).exists())

    @patch('blockchain_app.views.store_hash_on_chain')
    def test_store_creates_blockchain_record(self, mock_store):
        mock_store.return_value = '0xabc123'
        self.client.post(self.url, self.valid_payload, format='json')
        record = BlockchainRecord.objects.get(item_hash='a' * 64)
        self.assertEqual(record.category, 'ACADEMIC')
        self.assertEqual(record.issuer_name, 'ICT University')
        self.assertEqual(record.status, BlockchainRecord.Status.STORED)

    @patch('blockchain_app.views.store_hash_on_chain')
    def test_store_duplicate_hash_returns_409(self, mock_store):
        mock_store.return_value = '0xabc123'
        self.client.post(self.url, self.valid_payload, format='json')
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_store_hash_missing_fields_returns_400(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_store_hash_invalid_category_returns_400(self):
        payload = {**self.valid_payload, 'category': 'INVALID'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('blockchain_app.views.store_hash_on_chain')
    def test_store_hash_blockchain_error_returns_503(self, mock_store):
        mock_store.side_effect = Exception('Ganache connection failed')
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)

    @patch('blockchain_app.views.store_hash_on_chain')
    def test_store_all_categories_accepted(self, mock_store):
        mock_store.return_value = '0xabc'
        for i, cat in enumerate(['ACADEMIC', 'PHARMA', 'DOCUMENT', 'CURRENCY']):
            payload = {
                'item_hash':   chr(ord('a') + i) * 64,
                'category':    cat,
                'issuer_id':   f'issuer-{i}',
                'issuer_name': f'Institution {i}',
            }
            response = self.client.post(self.url, payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_store_hash_missing_issuer_id_returns_400(self):
        payload = {k: v for k, v in self.valid_payload.items() if k != 'issuer_id'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestVerifyHashEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/blockchain/verify/'

    @patch('blockchain_app.views.verify_hash_on_chain')
    def test_verify_authentic(self, mock_verify):
        mock_verify.return_value = {
            'exists': True, 'revoked': False,
            'category': 'ACADEMIC', 'issuer_id': 'issuer-001',
            'issuer_name': 'ICT University', 'timestamp': 1700000000,
            'revoke_reason': '',
        }
        response = self.client.post(self.url, {'item_hash': 'a' * 64}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'AUTHENTIC')

    @patch('blockchain_app.views.verify_hash_on_chain')
    def test_verify_authentic_returns_issuer_info(self, mock_verify):
        mock_verify.return_value = {
            'exists': True, 'revoked': False,
            'category': 'ACADEMIC', 'issuer_id': 'issuer-001',
            'issuer_name': 'ICT University', 'timestamp': 1700000000,
            'revoke_reason': '',
        }
        response = self.client.post(self.url, {'item_hash': 'a' * 64}, format='json')
        self.assertEqual(response.data['issuer_name'], 'ICT University')
        self.assertEqual(response.data['category'], 'ACADEMIC')

    @patch('blockchain_app.views.verify_hash_on_chain')
    def test_verify_not_found_returns_not_authentic(self, mock_verify):
        mock_verify.return_value = {
            'exists': False, 'revoked': False,
            'category': '', 'issuer_id': '',
            'issuer_name': '', 'timestamp': 0, 'revoke_reason': '',
        }
        response = self.client.post(self.url, {'item_hash': 'b' * 64}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'NOT_AUTHENTIC')

    @patch('blockchain_app.views.verify_hash_on_chain')
    def test_verify_revoked_returns_not_authentic(self, mock_verify):
        mock_verify.return_value = {
            'exists': True, 'revoked': True,
            'category': 'ACADEMIC', 'issuer_id': 'i1',
            'issuer_name': 'ICT', 'timestamp': 0,
            'revoke_reason': 'Fraudulent certificate',
        }
        response = self.client.post(self.url, {'item_hash': 'c' * 64}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'NOT_AUTHENTIC')
        self.assertIn('revoke_reason', response.data)

    def test_verify_missing_hash_returns_400(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('blockchain_app.views.verify_hash_on_chain')
    def test_verify_blockchain_error_returns_503(self, mock_verify):
        mock_verify.side_effect = Exception('Ganache connection failed')
        response = self.client.post(self.url, {'item_hash': 'd' * 64}, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)


class TestRevokeHashEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/blockchain/revoke/'
        self.record = BlockchainRecord.objects.create(
            item_hash='e' * 64, category='ACADEMIC',
            issuer_id='issuer-001', issuer_name='ICT University',
            tx_hash='0xabc', status=BlockchainRecord.Status.STORED,
        )

    @patch('blockchain_app.views.revoke_hash_on_chain')
    def test_revoke_success(self, mock_revoke):
        mock_revoke.return_value = '0xrevoke123'
        response = self.client.post(self.url, {
            'item_hash': 'e' * 64, 'reason': 'Diploma is fake',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tx_hash', response.data)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, BlockchainRecord.Status.REVOKED)

    @patch('blockchain_app.views.revoke_hash_on_chain')
    def test_revoke_sets_revoke_reason(self, mock_revoke):
        mock_revoke.return_value = '0xrevoke123'
        self.client.post(self.url, {
            'item_hash': 'e' * 64, 'reason': 'Diploma is fake',
        }, format='json')
        self.record.refresh_from_db()
        self.assertEqual(self.record.revoke_reason, 'Diploma is fake')

    def test_revoke_hash_not_found_returns_404(self):
        response = self.client.post(self.url, {
            'item_hash': 'f' * 64, 'reason': 'Does not exist',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_missing_fields_returns_400(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revoke_missing_reason_returns_400(self):
        response = self.client.post(self.url, {'item_hash': 'e' * 64}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('blockchain_app.views.revoke_hash_on_chain')
    def test_revoke_blockchain_error_returns_503(self, mock_revoke):
        mock_revoke.side_effect = Exception('Ganache connection failed')
        response = self.client.post(self.url, {
            'item_hash': 'e' * 64, 'reason': 'Test error',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class TestHealthCheckEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_health_check_returns_200(self):
        response = self.client.get('/api/blockchain/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_returns_service_name(self):
        response = self.client.get('/api/blockchain/health/')
        self.assertEqual(response.data['service'], 'blockchain')

    def test_health_check_returns_total_records(self):
        response = self.client.get('/api/blockchain/health/')
        self.assertIn('total_records', response.data)

    def test_health_check_returns_ganache_connected_field(self):
        response = self.client.get('/api/blockchain/health/')
        self.assertIn('ganache_connected', response.data)

    def test_health_check_ganache_connected_true(self):
        with patch('blockchain_app.web3_client.get_web3') as mock_get_web3:
            mock_w3 = MagicMock()
            mock_w3.is_connected.return_value = True
            mock_get_web3.return_value = mock_w3
            response = self.client.get('/api/blockchain/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_ganache_disconnected(self):
        response = self.client.get('/api/blockchain/health/')
        self.assertIn(response.data['ganache_connected'], [True, False])


class TestWeb3Client(TestCase):

    @patch('blockchain_app.web3_client.Web3')
    def test_get_web3_connected(self, mock_web3_class):
        mock_instance = MagicMock()
        mock_instance.is_connected.return_value = True
        mock_web3_class.return_value = mock_instance
        from .web3_client import get_web3
        w3 = get_web3()
        self.assertTrue(w3.is_connected())

    @patch('blockchain_app.web3_client.Web3')
    def test_get_web3_not_connected_raises(self, mock_web3_class):
        mock_instance = MagicMock()
        mock_instance.is_connected.return_value = False
        mock_web3_class.return_value = mock_instance
        from .web3_client import get_web3
        with self.assertRaises(ConnectionError):
            get_web3()

    @patch('blockchain_app.web3_client.Web3')
    def test_get_deployer_account_returns_first(self, mock_web3_class):
        mock_w3 = MagicMock()
        mock_w3.eth.accounts = ['0xAccount0', '0xAccount1']
        from .web3_client import get_deployer_account
        account = get_deployer_account(mock_w3)
        self.assertEqual(account, '0xAccount0')
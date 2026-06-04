import io
import uuid
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from verification_app.models import VerificationLog, FraudFlag


VALID_RESULTS = {'AUTHENTIC', 'NOT_AUTHENTIC', 'UNVERIFIABLE'}


def make_test_image(filename='test.png'):
    from PIL import Image
    img = Image.new('RGB', (10, 10), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return SimpleUploadedFile(filename, buf.getvalue(), content_type='image/png')


class MockUser:
    is_authenticated = True
    def __init__(self):
        self.id = uuid.uuid4()


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestVerificationLogModel(TestCase):

    def test_log_created_successfully(self):
        log = VerificationLog.objects.create(
            item_id=uuid.uuid4(),
            method=VerificationLog.Method.QR,
            result=VerificationLog.Result.AUTHENTIC,
            input_data='test-data',
        )
        self.assertIsNotNone(log.id)
        self.assertEqual(log.result, VerificationLog.Result.AUTHENTIC)

    def test_log_str_representation(self):
        log = VerificationLog.objects.create(
            method=VerificationLog.Method.SERIAL,
            result=VerificationLog.Result.NOT_AUTHENTIC,
            input_data='TEST-SERIAL',
        )
        self.assertIn('SERIAL', str(log))
        self.assertIn('NOT_AUTHENTIC', str(log))

    def test_log_verified_at_auto_set(self):
        log = VerificationLog.objects.create(
            method=VerificationLog.Method.QR,
            result=VerificationLog.Result.AUTHENTIC,
        )
        self.assertIsNotNone(log.verified_at)

    def test_log_item_id_nullable(self):
        log = VerificationLog.objects.create(
            method=VerificationLog.Method.SIGNATURE,
            result=VerificationLog.Result.UNVERIFIABLE,
        )
        self.assertIsNone(log.item_id)

    def test_log_all_methods(self):
        for method in [VerificationLog.Method.QR, VerificationLog.Method.SERIAL,
                       VerificationLog.Method.SIGNATURE, VerificationLog.Method.OCR,
                       VerificationLog.Method.WATERMARK]:
            log = VerificationLog.objects.create(
                method=method,
                result=VerificationLog.Result.AUTHENTIC,
            )
            self.assertEqual(log.method, method)


class TestFraudFlagModel(TestCase):

    def test_fraud_flag_created_successfully(self):
        flag = FraudFlag.objects.create(
            item_id=uuid.uuid4(),
            verification_count=10,
            window_start=timezone.now(),
            window_end=timezone.now(),
        )
        self.assertIsNotNone(flag.id)
        self.assertEqual(flag.status, FraudFlag.FlagStatus.OPEN)

    def test_fraud_flag_str_representation(self):
        item_id = uuid.uuid4()
        flag = FraudFlag.objects.create(
            item_id=item_id,
            verification_count=5,
            window_start=timezone.now(),
            window_end=timezone.now(),
        )
        self.assertIn('OPEN', str(flag))
        self.assertIn(str(item_id), str(flag))

    def test_fraud_flag_default_status_is_open(self):
        flag = FraudFlag.objects.create(
            item_id=uuid.uuid4(),
            verification_count=0,
            window_start=timezone.now(),
            window_end=timezone.now(),
        )
        self.assertEqual(flag.status, FraudFlag.FlagStatus.OPEN)


# ---------------------------------------------------------------------------
# Verify QR endpoint
# ---------------------------------------------------------------------------

class TestVerifyQREndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_verify_qr_with_valid_uuid_returns_200(self):
        with patch('verification_app.views.get_item_hash', return_value=None):
            response = self.client.post('/api/verify/qr/',
                                        data={'qr_data': str(uuid.uuid4())}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['result'], VALID_RESULTS)

    def test_verify_qr_response_has_expected_fields(self):
        with patch('verification_app.views.get_item_hash', return_value=None):
            response = self.client.post('/api/verify/qr/',
                                        data={'qr_data': str(uuid.uuid4())}, format='json')
        for field in ('result', 'method', 'message', 'verified_at'):
            self.assertIn(field, response.data)

    def test_verify_qr_invalid_uuid_format_returns_not_authentic(self):
        response = self.client.post('/api/verify/qr/',
                                    data={'qr_data': 'not-a-uuid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['result'], 'NOT_AUTHENTIC')

    def test_verify_qr_method_is_qr(self):
        with patch('verification_app.views.get_item_hash', return_value=None):
            response = self.client.post('/api/verify/qr/',
                                        data={'qr_data': str(uuid.uuid4())}, format='json')
        self.assertEqual(response.data['method'], 'QR')

    def test_verify_qr_fails_without_qr_data(self):
        response = self.client.post('/api/verify/qr/', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_qr_logs_verification(self):
        with patch('verification_app.views.get_item_hash', return_value=None):
            initial = VerificationLog.objects.count()
            self.client.post('/api/verify/qr/',
                             data={'qr_data': str(uuid.uuid4())}, format='json')
        self.assertEqual(VerificationLog.objects.count(), initial + 1)

    def test_verify_qr_no_auth_required(self):
        with patch('verification_app.views.get_item_hash', return_value=None):
            response = self.client.post('/api/verify/qr/',
                                        data={'qr_data': str(uuid.uuid4())}, format='json')
        self.assertNotIn(response.status_code,
                         [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_verify_qr_authentic_when_blockchain_exists(self):
        with patch('verification_app.views.get_item_hash', return_value='a' * 64):
            with patch('verification_app.views.get_cached_result', return_value=None):
                with patch('verification_app.views.check_blockchain',
                           return_value={'exists': True, 'item_details': {}}):
                    response = self.client.post('/api/verify/qr/',
                                               data={'qr_data': str(uuid.uuid4())}, format='json')
        self.assertEqual(response.data['result'], 'AUTHENTIC')

    def test_verify_qr_returns_cached_result(self):
        item_id = str(uuid.uuid4())
        cached = {
            'result': 'AUTHENTIC', 'item_id': item_id,
            'method': 'QR', 'message': 'Cached!',
            'item_details': None,
            'verified_at': timezone.now().isoformat(),
        }
        with patch('verification_app.views.get_item_hash', return_value='a' * 64):
            with patch('verification_app.views.get_cached_result', return_value=cached):
                initial = VerificationLog.objects.count()
                response = self.client.post('/api/verify/qr/',
                                           data={'qr_data': item_id}, format='json')
        self.assertEqual(response.data['message'], 'Cached!')
        self.assertEqual(VerificationLog.objects.count(), initial)


# ---------------------------------------------------------------------------
# Verify Serial endpoint
# ---------------------------------------------------------------------------

class TestVerifySerialEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_verify_serial_returns_200(self):
        with patch('verification_app.views.get_item_by_serial', return_value=None):
            with patch('verification_app.views.get_cached_result', return_value=None):
                response = self.client.post('/api/verify/serial/', data={
                    'serial_number': 'QNT-2024-CERT-ABCD1234',
                }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_serial_method_is_serial(self):
        with patch('verification_app.views.get_item_by_serial', return_value=None):
            with patch('verification_app.views.get_cached_result', return_value=None):
                response = self.client.post('/api/verify/serial/', data={
                    'serial_number': 'QNT-2024-CERT-ABCD1234',
                }, format='json')
        self.assertEqual(response.data['method'], 'SERIAL')

    def test_verify_serial_fails_without_serial_number(self):
        response = self.client.post('/api/verify/serial/', data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_serial_not_found_returns_not_authentic(self):
        with patch('verification_app.views.get_item_by_serial', return_value=None):
            with patch('verification_app.views.get_cached_result', return_value=None):
                response = self.client.post('/api/verify/serial/', data={
                    'serial_number': f'QNT-TEST-{uuid.uuid4().hex[:8].upper()}',
                }, format='json')
        self.assertEqual(response.data['result'], 'NOT_AUTHENTIC')

    def test_verify_serial_authentic_when_blockchain_confirms(self):
        item_id = str(uuid.uuid4())
        with patch('verification_app.views.get_cached_result', return_value=None):
            with patch('verification_app.views.get_item_by_serial', return_value={
                'blockchain_hash': 'a' * 64, 'id': item_id,
            }):
                with patch('verification_app.views.check_blockchain',
                           return_value={'exists': True, 'item_details': {}}):
                    response = self.client.post('/api/verify/serial/', data={
                        'serial_number': f'QNT-TEST-{uuid.uuid4().hex[:8].upper()}',
                    }, format='json')
        self.assertEqual(response.data['result'], 'AUTHENTIC')

    def test_verify_serial_logs_verification(self):
        with patch('verification_app.views.get_item_by_serial', return_value=None):
            with patch('verification_app.views.get_cached_result', return_value=None):
                serial = f'QNT-TEST-{uuid.uuid4().hex[:8].upper()}'
                initial = VerificationLog.objects.count()
                self.client.post('/api/verify/serial/', data={'serial_number': serial}, format='json')
        self.assertEqual(VerificationLog.objects.count(), initial + 1)

    def test_verify_serial_no_auth_required(self):
        with patch('verification_app.views.get_item_by_serial', return_value=None):
            with patch('verification_app.views.get_cached_result', return_value=None):
                response = self.client.post('/api/verify/serial/', data={
                    'serial_number': 'QNT-2024-CERT-ABCD1234',
                }, format='json')
        self.assertNotIn(response.status_code,
                         [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


# ---------------------------------------------------------------------------
# Verify Signature endpoint
# ---------------------------------------------------------------------------

class TestVerifySignatureEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_verify_signature_accepts_file_upload(self):
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 fake pdf', content_type='application/pdf')
        with patch('verification_app.views.check_blockchain',
                   return_value={'exists': False}):
            response = self.client.post('/api/verify/signature/',
                                        data={'document': pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['result'], VALID_RESULTS)

    def test_verify_signature_method_is_signature(self):
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        with patch('verification_app.views.check_blockchain',
                   return_value={'exists': False}):
            response = self.client.post('/api/verify/signature/',
                                        data={'document': pdf}, format='multipart')
        self.assertEqual(response.data['method'], 'SIGNATURE')

    def test_verify_signature_fails_without_document(self):
        response = self.client.post('/api/verify/signature/', data={}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_signature_logs_verification(self):
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 content', content_type='application/pdf')
        initial = VerificationLog.objects.count()
        with patch('verification_app.views.check_blockchain',
                   return_value={'exists': False}):
            self.client.post('/api/verify/signature/',
                             data={'document': pdf}, format='multipart')
        self.assertEqual(VerificationLog.objects.count(), initial + 1)


# ---------------------------------------------------------------------------
# Verify OCR endpoint
# ---------------------------------------------------------------------------

class TestVerifyOCREndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_verify_ocr_accepts_image_upload(self):
        response = self.client.post('/api/verify/ocr/',
                                    data={'image': make_test_image()}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['result'], VALID_RESULTS)

    def test_verify_ocr_method_is_ocr(self):
        response = self.client.post('/api/verify/ocr/',
                                    data={'image': make_test_image()}, format='multipart')
        self.assertEqual(response.data['method'], 'OCR')

    def test_verify_ocr_fails_without_image(self):
        response = self.client.post('/api/verify/ocr/', data={}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Verify Watermark endpoint
# ---------------------------------------------------------------------------

class TestVerifyWatermarkEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_verify_watermark_accepts_image_upload(self):
        response = self.client.post('/api/verify/watermark/',
                                    data={'image': make_test_image()}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['result'], VALID_RESULTS)

    def test_verify_watermark_method_is_watermark(self):
        response = self.client.post('/api/verify/watermark/',
                                    data={'image': make_test_image()}, format='multipart')
        self.assertEqual(response.data['method'], 'WATERMARK')

    def test_verify_watermark_fails_without_image(self):
        response = self.client.post('/api/verify/watermark/', data={}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_watermark_logs_verification(self):
        initial = VerificationLog.objects.count()
        self.client.post('/api/verify/watermark/',
                         data={'image': make_test_image()}, format='multipart')
        self.assertEqual(VerificationLog.objects.count(), initial + 1)


# ---------------------------------------------------------------------------
# Report item endpoint
# ---------------------------------------------------------------------------

class TestReportItemEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_report_item_succeeds(self):
        response = self.client.post('/api/verify/report/', data={
            'item_id': str(uuid.uuid4()),
            'reason':  'This item appears to be counterfeit based on visual inspection.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_report_creates_fraud_flag(self):
        initial = FraudFlag.objects.count()
        self.client.post('/api/verify/report/', data={
            'item_id': str(uuid.uuid4()),
            'reason':  'This item appears suspicious and may be counterfeit.',
        }, format='json')
        self.assertEqual(FraudFlag.objects.count(), initial + 1)

    def test_report_creates_verification_log(self):
        initial = VerificationLog.objects.count()
        self.client.post('/api/verify/report/', data={
            'item_id': str(uuid.uuid4()),
            'reason':  'This item appears suspicious and may be counterfeit.',
        }, format='json')
        self.assertEqual(VerificationLog.objects.count(), initial + 1)

    def test_report_fails_with_short_reason(self):
        response = self.client.post('/api/verify/report/', data={
            'item_id': str(uuid.uuid4()),
            'reason':  'Short',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_fails_without_item_id(self):
        response = self.client.post('/api/verify/report/', data={
            'reason': 'This looks counterfeit and suspicious.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_fails_without_reason(self):
        response = self.client.post('/api/verify/report/', data={
            'item_id': str(uuid.uuid4()),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_no_auth_required(self):
        response = self.client.post('/api/verify/report/', data={
            'item_id': str(uuid.uuid4()),
            'reason':  'This item appears to be counterfeit.',
        }, format='json')
        self.assertNotIn(response.status_code,
                         [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


# ---------------------------------------------------------------------------
# Verification history endpoint
# ---------------------------------------------------------------------------

class TestVerificationHistoryEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.item_id = uuid.uuid4()
        VerificationLog.objects.create(
            item_id=self.item_id, method=VerificationLog.Method.QR,
            result=VerificationLog.Result.AUTHENTIC, input_data=str(self.item_id),
        )
        VerificationLog.objects.create(
            item_id=self.item_id, method=VerificationLog.Method.SERIAL,
            result=VerificationLog.Result.AUTHENTIC, input_data='SERIAL-001',
        )

    def test_admin_can_view_history(self):
        self.client.credentials(HTTP_X_USER_ROLE='ADMIN')
        response = self.client.get(f'/api/verify/history/{self.item_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_non_admin_cannot_view_history(self):
        self.client.credentials(HTTP_X_USER_ROLE='ISSUER')
        response = self.client.get(f'/api/verify/history/{self.item_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_role_header_returns_403(self):
        response = self.client.get(f'/api/verify/history/{self.item_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_history_empty_for_item_with_no_logs(self):
        self.client.credentials(HTTP_X_USER_ROLE='ADMIN')
        response = self.client.get(f'/api/verify/history/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


# ---------------------------------------------------------------------------
# Fraud flags endpoint
# ---------------------------------------------------------------------------

class TestFraudFlagsEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()
        FraudFlag.objects.create(
            item_id=uuid.uuid4(), verification_count=60,
            window_start=timezone.now(), window_end=timezone.now(),
        )

    def test_admin_can_view_fraud_flags(self):
        self.client.force_authenticate(user=MockUser())
        self.client.credentials(HTTP_X_USER_ROLE='ADMIN')
        response = self.client.get('/api/verify/flags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_non_admin_cannot_view_fraud_flags(self):
        self.client.force_authenticate(user=MockUser())
        self.client.credentials(HTTP_X_USER_ROLE='ISSUER')
        response = self.client.get('/api/verify/flags/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fraud_flags_requires_authentication(self):
        # fraud_flags uses IsAuthenticated — unauthenticated should get 401
        response = self.client.get('/api/verify/flags/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fraud_flag_data_has_expected_fields(self):
        self.client.force_authenticate(user=MockUser())
        self.client.credentials(HTTP_X_USER_ROLE='ADMIN')
        response = self.client.get('/api/verify/flags/')
        flag = response.data[0]
        self.assertIn('item_id', flag)
        self.assertIn('verification_count', flag)
        self.assertIn('status', flag)
        self.assertEqual(flag['status'], 'OPEN')


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------

class TestHelperFunctions(TestCase):

    def test_get_verifier_ip_returns_remote_addr(self):
        from django.test import RequestFactory
        from verification_app.views import get_verifier_ip
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        self.assertEqual(get_verifier_ip(request), '127.0.0.1')

    def test_get_verifier_ip_prefers_x_forwarded_for(self):
        from django.test import RequestFactory
        from verification_app.views import get_verifier_ip
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.5, 192.168.1.1'
        self.assertEqual(get_verifier_ip(request), '10.0.0.5')

    def test_log_verification_creates_record(self):
        from verification_app.views import log_verification
        item_id = uuid.uuid4()
        log = log_verification(
            item_id, None,
            VerificationLog.Method.QR,
            VerificationLog.Result.AUTHENTIC,
            'qr-data', '127.0.0.1',
        )
        self.assertEqual(log.item_id, item_id)
        self.assertEqual(log.method, VerificationLog.Method.QR)
        self.assertEqual(log.verifier_ip, '127.0.0.1')

    def test_build_result_has_all_keys(self):
        from verification_app.views import build_result
        result = build_result('AUTHENTIC', uuid.uuid4(), 'QR', 'message')
        for key in ('result', 'item_id', 'method', 'message', 'item_details', 'verified_at'):
            self.assertIn(key, result)

    def test_build_result_with_none_item_id(self):
        from verification_app.views import build_result
        result = build_result('NOT_AUTHENTIC', None, 'SERIAL', 'not found')
        self.assertIsNone(result['item_id'])

    def test_get_cached_result_returns_none_when_redis_raises(self):
        from verification_app.views import get_cached_result
        with patch('verification_app.views.get_redis_client', side_effect=Exception('no redis')):
            result = get_cached_result('some-key')
        self.assertIsNone(result)

    def test_get_cached_result_returns_parsed_data_on_hit(self):
        import json
        from verification_app.views import get_cached_result
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({'result': 'AUTHENTIC', 'method': 'QR'}).encode()
        with patch('verification_app.views.get_redis_client', return_value=mock_redis):
            result = get_cached_result('test-item-id')
        self.assertEqual(result['result'], 'AUTHENTIC')

    def test_cache_result_handles_redis_error_silently(self):
        from verification_app.views import cache_result
        with patch('verification_app.views.get_redis_client', side_effect=Exception('no redis')):
            cache_result('some-key', {'result': 'AUTHENTIC'})  # should not raise

    def test_cache_result_calls_setex(self):
        from verification_app.views import cache_result
        mock_redis = MagicMock()
        with patch('verification_app.views.get_redis_client', return_value=mock_redis):
            cache_result('test-key', {'result': 'AUTHENTIC'})
        mock_redis.setex.assert_called_once()

    def test_check_blockchain_returns_dict_on_connection_failure(self):
        from verification_app.views import check_blockchain
        with patch('verification_app.views.requests.post', side_effect=Exception('no connection')):
            result = check_blockchain('a' * 64)
        self.assertIn('exists', result)
        self.assertFalse(result['exists'])

    def test_check_blockchain_authentic_response(self):
        from verification_app.views import check_blockchain
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'status': 'AUTHENTIC',
            'category': 'ACADEMIC',
            'issuer_name': 'ICT University',
            'issuer_id': 'issuer-001',
            'timestamp': 1700000000,
        }
        with patch('verification_app.views.requests.post', return_value=mock_resp):
            result = check_blockchain('a' * 64)
        self.assertTrue(result['exists'])
        self.assertIn('item_details', result)

    def test_check_blockchain_not_authentic_response(self):
        from verification_app.views import check_blockchain
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'status': 'NOT_AUTHENTIC'}
        with patch('verification_app.views.requests.post', return_value=mock_resp):
            result = check_blockchain('a' * 64)
        self.assertFalse(result['exists'])


# ---------------------------------------------------------------------------
# Fraud pattern detection
# ---------------------------------------------------------------------------

class TestCheckFraudPattern(TestCase):

    def test_fraud_flag_created_at_threshold(self):
        from verification_app.views import check_fraud_pattern
        item_id = uuid.uuid4()
        for _ in range(50):
            VerificationLog.objects.create(
                item_id=item_id,
                method=VerificationLog.Method.QR,
                result=VerificationLog.Result.AUTHENTIC,
            )
        initial = FraudFlag.objects.count()
        check_fraud_pattern(item_id)
        self.assertEqual(FraudFlag.objects.count(), initial + 1)

    def test_fraud_flag_has_correct_item_id(self):
        from verification_app.views import check_fraud_pattern
        item_id = uuid.uuid4()
        for _ in range(50):
            VerificationLog.objects.create(
                item_id=item_id,
                method=VerificationLog.Method.QR,
                result=VerificationLog.Result.AUTHENTIC,
            )
        check_fraud_pattern(item_id)
        flag = FraudFlag.objects.filter(item_id=item_id).first()
        self.assertIsNotNone(flag)
        self.assertEqual(flag.status, FraudFlag.FlagStatus.OPEN)

    def test_no_flag_below_threshold(self):
        from verification_app.views import check_fraud_pattern
        item_id = uuid.uuid4()
        for _ in range(49):
            VerificationLog.objects.create(
                item_id=item_id,
                method=VerificationLog.Method.QR,
                result=VerificationLog.Result.AUTHENTIC,
            )
        initial = FraudFlag.objects.count()
        check_fraud_pattern(item_id)
        self.assertEqual(FraudFlag.objects.count(), initial)

    def test_not_authentic_logs_do_not_trigger_flag(self):
        from verification_app.views import check_fraud_pattern
        item_id = uuid.uuid4()
        for _ in range(50):
            VerificationLog.objects.create(
                item_id=item_id,
                method=VerificationLog.Method.QR,
                result=VerificationLog.Result.NOT_AUTHENTIC,
            )
        initial = FraudFlag.objects.count()
        check_fraud_pattern(item_id)
        self.assertEqual(FraudFlag.objects.count(), initial)

    def test_no_duplicate_flag_for_same_item(self):
        from verification_app.views import check_fraud_pattern
        item_id = uuid.uuid4()
        for _ in range(50):
            VerificationLog.objects.create(
                item_id=item_id,
                method=VerificationLog.Method.QR,
                result=VerificationLog.Result.AUTHENTIC,
            )
        check_fraud_pattern(item_id)
        check_fraud_pattern(item_id)
        self.assertEqual(FraudFlag.objects.filter(item_id=item_id).count(), 1)
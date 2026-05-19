from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from .models import GeneratedOutput


class GenerateOutputsTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.generate_url = '/api/output/generate/'
        self.valid_payload = {
            'item_id':   'item-uuid-001',
            'item_hash': 'a' * 64,
            'category':  'ACADEMIC',
            'issuer_id': 'issuer-uuid-001',
            'item_name': 'Bachelor of Computer Science',
        }

    @patch('output_app.views.generate_qr_code')
    @patch('output_app.views.generate_digital_signature')
    def test_generate_academic_outputs(self, mock_sig, mock_qr):
        mock_qr.return_value  = '/app/media/qrcodes/qr_test.png'
        mock_sig.return_value = ('/app/media/signatures/sig_test.bin',
                                 '/app/media/signatures/pub_test.pem')
        response = self.client.post(self.generate_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('serial_number', response.data['outputs'])
        self.assertIn('qr_code_path', response.data['outputs'])
        self.assertIn('signature_path', response.data['outputs'])

    @patch('output_app.views.generate_qr_code')
    def test_generate_pharma_outputs(self, mock_qr):
        mock_qr.return_value = '/app/media/qrcodes/qr_test.png'
        payload = {**self.valid_payload, 'category': 'PHARMA'}
        response = self.client.post(self.generate_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('serial_number', response.data['outputs'])
        self.assertNotIn('signature_path', response.data['outputs'])

    @patch('output_app.views.generate_qr_code')
    def test_generate_document_outputs(self, mock_qr):
        mock_qr.return_value = '/app/media/qrcodes/qr_test.png'
        with patch('output_app.views.generate_digital_signature') as mock_sig:
            mock_sig.return_value = ('/app/media/signatures/sig_test.bin',
                                     '/app/media/signatures/pub_test.pem')
            payload = {**self.valid_payload, 'category': 'DOCUMENT'}
            response = self.client.post(self.generate_url, payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('signature_path', response.data['outputs'])

    @patch('output_app.views.generate_qr_code')
    def test_generate_currency_outputs(self, mock_qr):
        mock_qr.return_value = '/app/media/qrcodes/qr_test.png'
        payload = {**self.valid_payload, 'category': 'CURRENCY'}
        response = self.client.post(self.generate_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('signature_path', response.data['outputs'])

    def test_generate_missing_fields(self):
        response = self.client.post(self.generate_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_invalid_category(self):
        payload = {**self.valid_payload, 'category': 'INVALID'}
        response = self.client.post(self.generate_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('output_app.views.generate_qr_code')
    def test_generate_outputs_error(self, mock_qr):
        mock_qr.side_effect = Exception('QR generation failed')
        response = self.client.post(self.generate_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetOutputsTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        GeneratedOutput.objects.create(
            item_id       = 'item-001',
            item_hash     = 'a' * 64,
            category      = 'ACADEMIC',
            issuer_id     = 'issuer-001',
            output_type   = GeneratedOutput.OutputType.SERIAL,
            serial_number = 'QNT-2026-ACAD-A3F2B1',
        )

    def test_get_outputs_success(self):
        response = self.client.get('/api/output/item/item-001/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_outputs_not_found(self):
        response = self.client.get('/api/output/item/nonexistent/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class VerifySignatureTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url    = '/api/output/verify/signature/'

    def test_verify_signature_missing_fields(self):
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_signature_no_record(self):
        import io
        fake_file = io.BytesIO(b'fake signature content')
        fake_file.name = 'test.bin'
        response = self.client.post(self.url, {
            'file':      fake_file,
            'item_hash': 'b' * 64,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'NOT_AUTHENTIC')


class VerifyWatermarkTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url    = '/api/output/verify/watermark/'

    def test_verify_watermark_missing_fields(self):
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('output_app.views.extract_watermark')
    def test_verify_watermark_authentic(self, mock_extract):
        mock_extract.return_value = 'a' * 64
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        buf.name = 'test.png'
        response = self.client.post(self.url, {
            'image':     buf,
            'item_hash': 'a' * 64,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'AUTHENTIC')

    @patch('output_app.views.extract_watermark')
    def test_verify_watermark_not_authentic(self, mock_extract):
        mock_extract.return_value = 'z' * 64
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        buf.name = 'test.png'
        response = self.client.post(self.url, {
            'image':     buf,
            'item_hash': 'a' * 64,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'NOT_AUTHENTIC')


class HealthCheckTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get('/api/output/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service'], 'auth-output')
        self.assertIn('total_outputs', response.data)


class SerialNumberTests(TestCase):

    def test_serial_number_academic(self):
        from output_app.generators import generate_serial_number
        serial = generate_serial_number('ACADEMIC')
        self.assertTrue(serial.startswith('QNT-'))
        self.assertIn('ACAD', serial)

    def test_serial_number_pharma(self):
        from output_app.generators import generate_serial_number
        serial = generate_serial_number('PHARMA')
        self.assertIn('PHRM', serial)

    def test_serial_number_document(self):
        from output_app.generators import generate_serial_number
        serial = generate_serial_number('DOCUMENT')
        self.assertIn('DOCS', serial)

    def test_serial_number_currency(self):
        from output_app.generators import generate_serial_number
        serial = generate_serial_number('CURRENCY')
        self.assertIn('CURR', serial)

    def test_serial_number_unique(self):
        from output_app.generators import generate_serial_number
        serial1 = generate_serial_number('ACADEMIC')
        serial2 = generate_serial_number('ACADEMIC')
        self.assertNotEqual(serial1, serial2)

    def test_serial_number_custom_year(self):
        from output_app.generators import generate_serial_number
        serial = generate_serial_number('ACADEMIC', year=2026)
        self.assertIn('2026', serial)


class DigitalSignatureTests(TestCase):

    def test_signature_and_verify(self):
        from output_app.generators import generate_key_pair, verify_digital_signature
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        item_hash           = 'a' * 64
        private_key, public_key = generate_key_pair()

        signature = private_key.sign(
            item_hash.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        result = verify_digital_signature(item_hash, signature, pub_bytes)
        self.assertTrue(result)

    def test_invalid_signature_rejected(self):
        from output_app.generators import generate_key_pair, verify_digital_signature
        from cryptography.hazmat.primitives import serialization

        _, public_key = generate_key_pair()
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        result = verify_digital_signature('a' * 64, b'invalid_signature', pub_bytes)
        self.assertFalse(result)


class WatermarkTests(TestCase):

    def test_embed_and_extract_watermark(self):
        from output_app.generators import embed_watermark, extract_watermark
        from PIL import Image
        import tempfile
        import os

        # Create a test image
        img      = Image.new('RGB', (200, 200), color='white')
        tmp_path = tempfile.mktemp(suffix='.png')
        img.save(tmp_path)

        item_hash = 'a' * 64
        item_id   = 'test-item-001'

        with self.settings(MEDIA_ROOT=tempfile.mkdtemp()):
            out_path = embed_watermark(tmp_path, item_hash, item_id)
            self.assertTrue(os.path.exists(out_path))

            extracted = extract_watermark(out_path)
            self.assertEqual(extracted, item_hash)

        os.remove(tmp_path)

    def test_extract_watermark_no_watermark(self):
        from output_app.generators import extract_watermark
        from PIL import Image
        import tempfile

        img      = Image.new('RGB', (50, 50), color='white')
        tmp_path = tempfile.mktemp(suffix='.png')
        img.save(tmp_path)

        result = extract_watermark(tmp_path)
        self.assertIsNone(result)

        import os
        os.remove(tmp_path)
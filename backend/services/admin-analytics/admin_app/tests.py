from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import FraudAlert, ActivityLog


class StatsTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_get_stats_empty(self):
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_fraud_alerts', response.data)
        self.assertIn('open_fraud_alerts', response.data)
        self.assertIn('total_activity_logs', response.data)

    def test_get_stats_with_data(self):
        FraudAlert.objects.create(
            item_hash          = 'a' * 64,
            verification_count = 55,
        )
        ActivityLog.objects.create(
            event_type  = ActivityLog.EventType.REGISTRATION,
            description = 'Test registration',
        )
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_fraud_alerts'], 1)
        self.assertEqual(response.data['total_activity_logs'], 1)
        self.assertEqual(response.data['recent_registrations'], 1)


class FraudAlertTests(TestCase):

    def setUp(self):
        self.client     = APIClient()
        self.list_url   = '/api/admin/fraud-alerts/'
        self.create_url = '/api/admin/fraud-alerts/create/'
        self.alert = FraudAlert.objects.create(
            item_hash          = 'a' * 64,
            verification_count = 55,
        )

    def test_get_fraud_alerts(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_fraud_alerts_filter_open(self):
        response = self.client.get(self.list_url + '?status=OPEN')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_fraud_alerts_filter_resolved(self):
        response = self.client.get(self.list_url + '?status=RESOLVED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_fraud_alert_success(self):
        response = self.client.post(self.create_url, {
            'item_hash':          'b' * 64,
            'item_id':            'item-001',
            'issuer_id':          'issuer-001',
            'verification_count': 60,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_hash'], 'b' * 64)

    def test_create_fraud_alert_missing_fields(self):
        response = self.client.post(self.create_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_fraud_alert_resolve(self):
        url      = f'/api/admin/fraud-alerts/{self.alert.id}/update/'
        response = self.client.patch(url, {
            'status': 'RESOLVED',
            'notes':  'Verified — legitimate bulk employer check',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'RESOLVED')

    def test_update_fraud_alert_not_found(self):
        response = self.client.patch(
            '/api/admin/fraud-alerts/00000000-0000-0000-0000-000000000000/update/',
            {'status': 'RESOLVED'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_fraud_alert_invalid_status(self):
        url      = f'/api/admin/fraud-alerts/{self.alert.id}/update/'
        response = self.client.patch(url, {'status': 'INVALID'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ActivityLogTests(TestCase):

    def setUp(self):
        self.client     = APIClient()
        self.list_url   = '/api/admin/activity/'
        self.create_url = '/api/admin/activity/create/'
        ActivityLog.objects.create(
            event_type  = ActivityLog.EventType.REGISTRATION,
            description = 'Test item registered',
            actor_id    = 'issuer-001',
            item_hash   = 'a' * 64,
        )

    def test_get_activity_logs(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_activity_logs_filter(self):
        response = self.client.get(self.list_url + '?event_type=REGISTRATION')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_activity_logs_filter_no_match(self):
        response = self.client.get(self.list_url + '?event_type=REVOCATION')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_activity_log_success(self):
        response = self.client.post(self.create_url, {
            'event_type':  'VERIFICATION',
            'description': 'Item verified by employer',
            'actor_id':    'verifier-001',
            'item_hash':   'b' * 64,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['event_type'], 'VERIFICATION')

    def test_create_activity_log_missing_fields(self):
        response = self.client.post(self.create_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_activity_log_minimal(self):
        response = self.client.post(self.create_url, {
            'event_type':  'FRAUD_FLAGGED',
            'description': 'Suspicious verification pattern detected',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class HealthCheckTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get('/api/admin/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['service'], 'admin-analytics')
        self.assertIn('total_alerts', response.data)
        self.assertIn('total_logs', response.data)
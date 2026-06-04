from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import FraudAlert, ActivityLog


class TestFraudAlertModel(TestCase):

    def test_alert_created_successfully(self):
        alert = FraudAlert.objects.create(
            item_hash='a' * 64,
            verification_count=55,
        )
        self.assertIsNotNone(alert.id)
        self.assertEqual(alert.status, FraudAlert.Status.OPEN)

    def test_alert_str_representation(self):
        alert = FraudAlert.objects.create(
            item_hash='b' * 64,
            verification_count=10,
        )
        self.assertIn('OPEN', str(alert))

    def test_alert_default_status_is_open(self):
        alert = FraudAlert.objects.create(
            item_hash='c' * 64,
            verification_count=0,
        )
        self.assertEqual(alert.status, FraudAlert.Status.OPEN)

    def test_alert_notes_blank_by_default(self):
        alert = FraudAlert.objects.create(
            item_hash='d' * 64,
            verification_count=5,
        )
        self.assertEqual(alert.notes, '')

    def test_alert_has_created_at(self):
        alert = FraudAlert.objects.create(
            item_hash='e' * 64,
            verification_count=3,
        )
        self.assertIsNotNone(alert.created_at)


class TestActivityLogModel(TestCase):

    def test_log_created_successfully(self):
        log = ActivityLog.objects.create(
            event_type=ActivityLog.EventType.REGISTRATION,
            description='Test item registered',
        )
        self.assertIsNotNone(log.id)
        self.assertEqual(log.event_type, ActivityLog.EventType.REGISTRATION)

    def test_log_str_representation(self):
        log = ActivityLog.objects.create(
            event_type=ActivityLog.EventType.VERIFICATION,
            description='Test verification',
        )
        self.assertIn('VERIFICATION', str(log))

    def test_log_actor_id_blank_by_default(self):
        log = ActivityLog.objects.create(
            event_type=ActivityLog.EventType.REVOCATION,
            description='Item revoked',
        )
        self.assertEqual(log.actor_id, '')

    def test_log_has_created_at(self):
        log = ActivityLog.objects.create(
            event_type=ActivityLog.EventType.FRAUD_FLAGGED,
            description='Fraud detected',
        )
        self.assertIsNotNone(log.created_at)


class TestStatsEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_get_stats_returns_200(self):
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_stats_has_required_fields(self):
        response = self.client.get('/api/admin/stats/')
        self.assertIn('total_fraud_alerts', response.data)
        self.assertIn('open_fraud_alerts', response.data)
        self.assertIn('total_activity_logs', response.data)
        self.assertIn('recent_registrations', response.data)
        self.assertIn('recent_verifications', response.data)
        self.assertIn('recent_revocations', response.data)

    def test_get_stats_empty_db(self):
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.data['total_fraud_alerts'], 0)
        self.assertEqual(response.data['total_activity_logs'], 0)

    def test_get_stats_with_data(self):
        FraudAlert.objects.create(item_hash='a' * 64, verification_count=55)
        ActivityLog.objects.create(
            event_type=ActivityLog.EventType.REGISTRATION,
            description='Test registration',
        )
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.data['total_fraud_alerts'], 1)
        self.assertEqual(response.data['total_activity_logs'], 1)
        self.assertEqual(response.data['recent_registrations'], 1)

    def test_stats_counts_open_alerts_only(self):
        FraudAlert.objects.create(item_hash='a' * 64, verification_count=10, status=FraudAlert.Status.OPEN)
        FraudAlert.objects.create(item_hash='b' * 64, verification_count=5, status=FraudAlert.Status.RESOLVED)
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.data['open_fraud_alerts'], 1)
        self.assertEqual(response.data['total_fraud_alerts'], 2)


class TestFraudAlertEndpoints(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.alert = FraudAlert.objects.create(
            item_hash='a' * 64,
            verification_count=55,
        )

    def test_get_fraud_alerts_returns_200(self):
        response = self.client.get('/api/admin/fraud-alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_fraud_alerts_filter_open(self):
        response = self.client.get('/api/admin/fraud-alerts/?status=OPEN')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_fraud_alerts_filter_resolved_returns_empty(self):
        response = self.client.get('/api/admin/fraud-alerts/?status=RESOLVED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_fraud_alert_success(self):
        response = self.client.post('/api/admin/fraud-alerts/create/', {
            'item_hash':          'b' * 64,
            'item_id':            'item-001',
            'issuer_id':          'issuer-001',
            'verification_count': 60,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_hash'], 'b' * 64)
        self.assertEqual(response.data['status'], 'OPEN')

    def test_create_fraud_alert_missing_fields_returns_400(self):
        response = self.client.post('/api/admin/fraud-alerts/create/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_fraud_alert_missing_verification_count_returns_400(self):
        response = self.client.post('/api/admin/fraud-alerts/create/', {
            'item_hash': 'c' * 64,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_fraud_alert_resolve(self):
        url = f'/api/admin/fraud-alerts/{self.alert.id}/update/'
        response = self.client.patch(url, {
            'status': 'RESOLVED',
            'notes':  'Verified — legitimate bulk employer check',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'RESOLVED')

    def test_update_fraud_alert_dismiss(self):
        url = f'/api/admin/fraud-alerts/{self.alert.id}/update/'
        response = self.client.patch(url, {
            'status': 'DISMISSED',
            'notes':  'False positive.',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'DISMISSED')

    def test_update_fraud_alert_not_found_returns_404(self):
        response = self.client.patch(
            '/api/admin/fraud-alerts/00000000-0000-0000-0000-000000000000/update/',
            {'status': 'RESOLVED'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_fraud_alert_invalid_status_returns_400(self):
        url = f'/api/admin/fraud-alerts/{self.alert.id}/update/'
        response = self.client.patch(url, {'status': 'INVALID'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_fraud_alerts_no_filter_returns_all(self):
        FraudAlert.objects.create(item_hash='b' * 64, verification_count=10, status=FraudAlert.Status.RESOLVED)
        response = self.client.get('/api/admin/fraud-alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class TestActivityLogEndpoints(TestCase):

    def setUp(self):
        self.client = APIClient()
        ActivityLog.objects.create(
            event_type=ActivityLog.EventType.REGISTRATION,
            description='Test item registered',
            actor_id='issuer-001',
            item_hash='a' * 64,
        )

    def test_get_activity_logs_returns_200(self):
        response = self.client.get('/api/admin/activity/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_activity_logs_filter_by_event_type(self):
        response = self.client.get('/api/admin/activity/?event_type=REGISTRATION')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_activity_logs_filter_no_match(self):
        response = self.client.get('/api/admin/activity/?event_type=REVOCATION')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_activity_log_success(self):
        response = self.client.post('/api/admin/activity/create/', {
            'event_type':  'VERIFICATION',
            'description': 'Item verified by employer',
            'actor_id':    'verifier-001',
            'item_hash':   'b' * 64,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['event_type'], 'VERIFICATION')

    def test_create_activity_log_missing_fields_returns_400(self):
        response = self.client.post('/api/admin/activity/create/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_activity_log_minimal(self):
        response = self.client.post('/api/admin/activity/create/', {
            'event_type':  'FRAUD_FLAGGED',
            'description': 'Suspicious verification pattern detected',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_activity_log_all_event_types(self):
        for etype in ['REGISTRATION', 'VERIFICATION', 'REVOCATION',
                      'ISSUER_APPROVED', 'ISSUER_REJECTED', 'FRAUD_FLAGGED']:
            response = self.client.post('/api/admin/activity/create/', {
                'event_type':  etype,
                'description': f'Test {etype} event',
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_activity_log_missing_description_returns_400(self):
        response = self.client.post('/api/admin/activity/create/', {
            'event_type': 'REGISTRATION',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestHealthCheckEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_health_check_returns_200(self):
        response = self.client.get('/api/admin/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_service_name(self):
        response = self.client.get('/api/admin/health/')
        self.assertEqual(response.data['service'], 'admin-analytics')

    def test_health_check_includes_total_alerts(self):
        response = self.client.get('/api/admin/health/')
        self.assertIn('total_alerts', response.data)

    def test_health_check_includes_total_logs(self):
        response = self.client.get('/api/admin/health/')
        self.assertIn('total_logs', response.data)

    def test_health_check_counts_are_accurate(self):
        FraudAlert.objects.create(item_hash='a' * 64, verification_count=5)
        ActivityLog.objects.create(
            event_type=ActivityLog.EventType.REGISTRATION,
            description='Test',
        )
        response = self.client.get('/api/admin/health/')
        self.assertEqual(response.data['total_alerts'], 1)
        self.assertEqual(response.data['total_logs'], 1)
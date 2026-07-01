from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.gyms.models import Gym


class ApiSmokeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username='api_admin',
            email='api.admin@example.com',
            password='pass12345',
            role=getattr(User.Role, 'ADMIN', 'ADMIN'),
            is_staff=True,
        )
        self.owner = User.objects.create_user(
            username='api_owner',
            email='api.owner@example.com',
            password='pass12345',
            role=getattr(User.Role, 'OWNER', 'OWNER'),
        )
        self.customer = User.objects.create_user(
            username='api_customer',
            email='api.customer@example.com',
            password='pass12345',
            role=getattr(User.Role, 'CUSTOMER', 'CUSTOMER'),
        )
        self.gym = Gym.objects.create(
            owner=self.owner,
            name='API Gym',
            slug='api-gym',
            description='Demo API gym',
            city='Bamberg',
            address='API Street 1',
            starting_price='39.00',
            status=Gym.Status.APPROVED,
        )

    def test_gym_list_api_is_paginated(self):
        response = self.client.get('/api/gyms/?page_size=20')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['page_size'], 20)
        self.assertEqual(payload['results'][0]['slug'], 'api-gym')

    def test_favorite_api_requires_auth(self):
        response = self.client.post('/api/gyms/api-gym/favorite/')
        self.assertIn(response.status_code, [401, 403])

    def test_customer_can_favorite_gym(self):
        self.client.force_login(self.customer)
        response = self.client.post('/api/gyms/api-gym/favorite/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

    def test_owner_analytics_requires_owner_or_admin(self):
        self.client.force_login(self.customer)
        response = self.client.get('/api/owner/analytics/')
        self.assertEqual(response.status_code, 403)

    def test_owner_can_open_owner_analytics_api(self):
        self.client.force_login(self.owner)
        response = self.client.get('/api/owner/analytics/?days=30')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['owner']['username'], 'api_owner')

    @override_settings(DEMO_TOOLS_ENABLED=False)
    def test_demo_seed_disabled_returns_403(self):
        self.client.force_login(self.admin)
        response = self.client.post('/api/demo/seed-analytics/', data={'days': 30, 'customers': 5}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_email_config_is_sanitized_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get('/api/email/config/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('SECRET', response.json())
        self.assertIn(response.json()['EMAIL_HOST_PASSWORD'], ['SET', 'EMPTY'])

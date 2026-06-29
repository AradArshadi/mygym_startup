from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User


class ControlPanelSafetyTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin_user', password='pass12345', role=User.Role.ADMIN, is_staff=True)
        self.customer = User.objects.create_user(username='customer_user', password='pass12345', role=User.Role.CUSTOMER)

    def test_customer_cannot_access_safety_center(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('control_security'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_safety_center(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('control_security'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Safety Center')

    @override_settings(DEMO_TOOLS_ENABLED=False)
    def test_demo_tools_disabled_message(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('control_demo_tools'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo tools are disabled')

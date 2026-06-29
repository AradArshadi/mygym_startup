from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.gyms.models import Gym, MembershipPlan


class GymControlCenterUXTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='gym_control_owner',
            email='owner@example.com',
            password='pass12345',
            role=User.Role.OWNER,
        )
        self.customer = User.objects.create_user(
            username='gym_control_customer',
            email='customer@example.com',
            password='pass12345',
            role=User.Role.CUSTOMER,
        )
        self.gym = Gym.objects.create(
            owner=self.owner,
            name='Premium Control Gym',
            slug='premium-control-gym',
            description='A gym used for control center UX tests.',
            city='Bamberg',
            address='Owner Street 1',
            email='gym@example.com',
            starting_price=Decimal('39.00'),
            status=Gym.Status.APPROVED,
        )
        self.plan = MembershipPlan.objects.create(
            gym=self.gym,
            title='Monthly Access',
            description='Full access membership.',
            price=Decimal('49.00'),
            duration_days=30,
        )

    def test_manage_page_uses_premium_control_center_layout(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('owner_gym_manage', args=[self.gym.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'gym-control-hero-card')
        self.assertContains(response, 'gym-control-tabs')
        self.assertContains(response, 'plan-card-grid')
        self.assertContains(response, 'plan-control-card')
        self.assertContains(response, 'New plan')
        self.assertContains(response, 'Membership plans')
        self.assertContains(response, 'Analytics')

    def test_edit_page_groups_form_into_professional_sections(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('owner_gym_edit', args=[self.gym.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'management-form-card')
        self.assertContains(response, 'Basic information')
        self.assertContains(response, 'Address and map data')
        self.assertContains(response, 'Customer contact channels')
        self.assertContains(response, 'Save gym profile')
        self.assertContains(response, 'sticky-save-card')

    def test_customer_cannot_manage_owner_gym(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse('owner_gym_manage', args=[self.gym.slug]))
        self.assertEqual(response.status_code, 403)

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from .forms import GymImageForm


class GymImageUploadSafetyTests(TestCase):
    @override_settings(MAX_GYM_IMAGE_UPLOAD_MB=1, ALLOWED_GYM_IMAGE_EXTENSIONS=['jpg', 'jpeg', 'png', 'webp'])
    def test_rejects_non_image_upload(self):
        upload = SimpleUploadedFile('bad.txt', b'not-an-image', content_type='text/plain')
        form = GymImageForm(files={'image': upload}, data={'alt_text': 'bad', 'is_cover': ''})
        self.assertFalse(form.is_valid())

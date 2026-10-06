from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Product, Series
from .models import Link


User = get_user_model()


class IndexProductLinksTests(TestCase):
    def setUp(self):
        self.series = Series.objects.create(
            name='测试作品集',
            bango='test_series',
            intro='作品集介绍',
            author='测试作者',
            is_approved=True,
        )
        self.product = Product.objects.create(
            series=self.series,
            name='测试作品',
            author='测试作者',
            intro='作品介绍',
            file='products/test.txt',
            is_approved=True,
        )

    def test_product_card_and_download_have_separate_links(self):
        response = self.client.get(reverse('website_index:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('products:single_series', args=[self.series.bango]),
        )
        self.assertContains(
            response,
            reverse('products:download_file', args=[self.product.id]),
        )


class AdminNavigationTests(TestCase):
    def test_staff_user_sees_admin_link(self):
        user = User.objects.create_user(
            username='staff',
            password='StrongPassword123!',
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('website_index:index'))

        self.assertContains(response, '管理网站')
        self.assertContains(response, reverse('admin:index'))

    def test_regular_user_does_not_see_admin_link(self):
        user = User.objects.create_user(
            username='member',
            password='StrongPassword123!',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('website_index:index'))

        self.assertNotContains(response, '管理网站')


class AdminStyleTests(TestCase):
    def test_admin_login_uses_club_branding_and_styles(self):
        response = self.client.get(reverse('admin:login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '南师附中开发者社团管理网站')
        self.assertContains(
            response,
            'website_index/css/admin.css',
        )
        self.assertContains(
            response,
            'website_index/images/club-logo.png',
        )

    def test_admin_pages_remain_accessible(self):
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='StrongPassword123!',
        )
        self.client.force_login(admin_user)

        responses = [
            self.client.get(reverse('admin:index')),
            self.client.get(reverse('admin:auth_user_changelist')),
            self.client.get(reverse('admin:products_series_changelist')),
            self.client.get(reverse('admin:products_product_changelist')),
        ]

        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'website_index/css/admin.css')


class StaffLinkAdminTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff', password='StrongPassword123!', is_staff=True,
        )
        self.link = Link.objects.create(
            title='旧链接', description='描述', url='https://example.com',
        )
        self.client.force_login(self.staff)

    def test_staff_can_manage_links(self):
        change_url = reverse('admin:website_index_link_change', args=[self.link.id])
        add_response = self.client.get(reverse('admin:website_index_link_add'))
        change_response = self.client.get(change_url)
        delete_response = self.client.post(
            reverse('admin:website_index_link_delete', args=[self.link.id]),
            {'post': 'yes'},
        )

        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(change_response.status_code, 200)
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Link.objects.filter(pk=self.link.id).exists())

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Product, Series


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

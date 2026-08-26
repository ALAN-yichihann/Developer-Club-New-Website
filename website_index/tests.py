from django.test import TestCase
from django.urls import reverse

from products.models import Product, Series


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

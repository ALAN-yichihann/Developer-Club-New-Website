from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Product, Series


class ProductDownloadTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.settings_override.enable()

        series = Series.objects.create(
            name='测试系列',
            intro='系列简介',
            author='测试作者',
        )
        self.product = Product.objects.create(
            series=series,
            name='测试产品',
            author='测试作者',
            intro='产品简介',
            file=SimpleUploadedFile('product.txt', b'product content'),
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_download_returns_current_product_file(self):
        response = self.client.get(
            reverse('products:download_file', args=[self.product.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename="product.txt"',
        )
        self.assertEqual(b''.join(response.streaming_content), b'product content')
        response.close()

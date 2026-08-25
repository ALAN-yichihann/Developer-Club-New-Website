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


class EditProductTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.settings_override.enable()

        self.series = Series.objects.create(
            name='测试系列',
            bango='test_series',
            intro='系列简介',
            author='测试作者',
        )
        self.product = Product.objects.create(
            series=self.series,
            name='旧版本',
            author='旧作者',
            intro='旧介绍',
            file=SimpleUploadedFile('old.txt', b'old content'),
        )
        self.url = reverse(
            'products:edit_product',
            args=[self.series.bango, self.product.id],
        )
        self.original_file_name = self.product.file.name

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_edit_page_displays_product_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '旧版本')
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertNotContains(response, 'Current:')
        self.assertContains(response, '更改为:')

    def test_edit_updates_product_without_changing_series(self):
        response = self.client.post(
            self.url,
            {
                'name': '新版本',
                'author': '新作者',
                'intro': '新介绍',
            },
        )

        self.assertRedirects(
            response,
            reverse('products:my_single_series', args=[self.series.bango]),
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, '新版本')
        self.assertEqual(self.product.series, self.series)
        self.assertEqual(self.product.file.name, self.original_file_name)

    def test_edit_rejects_product_from_another_series(self):
        other_series = Series.objects.create(
            name='其他系列',
            bango='other_series',
            intro='其他简介',
            author='其他作者',
        )
        url = reverse(
            'products:edit_product',
            args=[other_series.bango, self.product.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Product, Series
from .forms import AdminProductForm, AdminSeriesForm


User = get_user_model()


class ProductDownloadTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.settings_override.enable()

        series = Series.objects.create(
            name='测试系列',
            bango='download_series',
            intro='系列简介',
            author='测试作者',
            is_approved=True,
        )
        self.product = Product.objects.create(
            series=series,
            name='测试产品',
            author='测试作者',
            intro='产品简介',
            file=SimpleUploadedFile('product.txt', b'product content'),
            is_approved=True,
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

        self.user = User.objects.create_user(
            username='approved_user',
            password='StrongPassword123!',
        )
        self.series = Series.objects.create(
            name='测试系列',
            bango='test_series',
            owner=self.user,
            intro='系列简介',
            author='测试作者',
            is_approved=True,
        )
        self.product = Product.objects.create(
            series=self.series,
            owner=self.user,
            name='旧版本',
            author='旧作者',
            intro='旧介绍',
            file=SimpleUploadedFile('old.txt', b'old content'),
            is_approved=True,
        )
        self.url = reverse(
            'products:edit_product',
            args=[self.series.bango, self.product.id],
        )
        self.original_file_name = self.product.file.name
        self.client.force_login(self.user)

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
        self.assertFalse(self.product.is_approved)

    def test_unchanged_product_keeps_approval(self):
        response = self.client.post(
            self.url,
            {
                'name': self.product.name,
                'author': self.product.author,
                'intro': self.product.intro,
            },
        )

        self.assertRedirects(
            response,
            reverse('products:my_single_series', args=[self.series.bango]),
        )
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_approved)
        self.assertEqual(self.product.file.name, self.original_file_name)

    def test_edit_rejects_product_from_another_series(self):
        other_series = Series.objects.create(
            name='其他系列',
            bango='other_series',
            owner=self.user,
            intro='其他简介',
            author='其他作者',
            is_approved=True,
        )
        url = reverse(
            'products:edit_product',
            args=[other_series.bango, self.product.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


class ApprovalVisibilityTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.settings_override.enable()

        self.user = User.objects.create_user(
            username='approved_user',
            password='StrongPassword123!',
        )
        self.approved_series = Series.objects.create(
            name='已审核系列',
            bango='approved_series',
            owner=self.user,
            intro='已审核系列介绍',
            author='测试作者',
            is_approved=True,
        )
        self.pending_series = Series.objects.create(
            name='待审核系列',
            owner=self.user,
            intro='待审核系列介绍',
            author='测试作者',
        )
        self.approved_product = Product.objects.create(
            series=self.approved_series,
            owner=self.user,
            name='已审核作品',
            author='测试作者',
            intro='已审核作品介绍',
            file=SimpleUploadedFile('approved.txt', b'approved'),
            is_approved=True,
        )
        self.pending_product = Product.objects.create(
            series=self.approved_series,
            owner=self.user,
            name='待审核作品',
            author='测试作者',
            intro='待审核作品介绍',
            file=SimpleUploadedFile('pending.txt', b'pending'),
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_pending_content_is_hidden_from_public_pages(self):
        products_response = self.client.get(reverse('products:all_products'))
        series_response = self.client.get(
            reverse('products:single_series', args=[self.approved_series.bango])
        )
        index_response = self.client.get(reverse('website_index:index'))

        self.assertContains(products_response, self.approved_series.name)
        self.assertNotContains(products_response, self.pending_series.name)
        self.assertContains(series_response, self.approved_product.name)
        self.assertNotContains(series_response, self.pending_product.name)
        self.assertContains(index_response, self.approved_product.name)
        self.assertNotContains(index_response, self.pending_product.name)

    def test_pending_content_is_hidden_from_personal_pages(self):
        self.client.force_login(self.user)

        works_response = self.client.get(reverse('products:my_works'))
        series_response = self.client.get(
            reverse(
                'products:my_single_series',
                args=[self.approved_series.bango],
            )
        )

        self.assertContains(works_response, self.approved_series.name)
        self.assertNotContains(works_response, self.pending_series.name)
        self.assertContains(works_response, '当前有 1 个作品集尚未审核。')
        self.assertContains(series_response, self.approved_product.name)
        self.assertNotContains(series_response, self.pending_product.name)
        self.assertContains(series_response, '当前有 1 个作品尚未审核。')

    def test_personal_series_displays_zero_pending_products(self):
        self.pending_product.delete()
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                'products:my_single_series',
                args=[self.approved_series.bango],
            )
        )

        self.assertContains(response, '当前有 0 个作品尚未审核。')

    def test_my_works_displays_zero_pending_series(self):
        self.pending_series.delete()
        self.client.force_login(self.user)

        response = self.client.get(reverse('products:my_works'))

        self.assertContains(response, '当前有 0 个作品集尚未审核。')

    def test_pending_content_cannot_be_accessed_directly(self):
        self.client.force_login(self.user)

        series_response = self.client.get(
            reverse('products:single_series', args=['pending_series'])
        )
        download_response = self.client.get(
            reverse('products:download_file', args=[self.pending_product.id])
        )
        edit_response = self.client.get(
            reverse(
                'products:edit_product',
                args=[self.approved_series.bango, self.pending_product.id],
            )
        )

        self.assertEqual(series_response.status_code, 404)
        self.assertEqual(download_response.status_code, 404)
        self.assertEqual(edit_response.status_code, 404)

    def test_new_series_is_pending_without_bango(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('products:new_series'),
            {
                'name': '新系列',
                'intro': '新系列介绍',
                'author': '测试作者',
            },
        )

        self.assertRedirects(response, reverse('products:series_added'))
        series = Series.objects.get(name='新系列')
        self.assertFalse(series.is_approved)
        self.assertIsNone(series.bango)

    def test_new_product_is_pending(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                'products:new_product',
                args=[self.approved_series.bango],
            ),
            {
                'name': '新作品',
                'author': '测试作者',
                'intro': '新作品介绍',
                'file': SimpleUploadedFile('new.txt', b'new'),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                'products:my_single_series',
                args=[self.approved_series.bango],
            ),
        )
        product = Product.objects.get(name='新作品')
        self.assertFalse(product.is_approved)

    def test_edit_series_resets_approval_and_preserves_bango(self):
        old_bango = self.approved_series.bango
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('products:edit_single_series', args=[old_bango]),
            {
                'name': '编辑后的系列',
                'intro': '编辑后的介绍',
                'author': '编辑后的作者',
            },
        )

        self.assertRedirects(response, reverse('products:series_added'))
        self.approved_series.refresh_from_db()
        self.assertFalse(self.approved_series.is_approved)
        self.assertEqual(self.approved_series.bango, old_bango)
        self.assertEqual(
            self.client.get(
                reverse('products:single_series', args=[old_bango])
            ).status_code,
            404,
        )

    def test_unchanged_series_keeps_approval(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                'products:edit_single_series',
                args=[self.approved_series.bango],
            ),
            {
                'name': self.approved_series.name,
                'intro': self.approved_series.intro,
                'author': self.approved_series.author,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                'products:my_single_series',
                args=[self.approved_series.bango],
            ),
        )
        self.approved_series.refresh_from_db()
        self.assertTrue(self.approved_series.is_approved)
        self.assertEqual(self.approved_series.bango, 'approved_series')


class ApprovalAdminFormTests(TestCase):
    def setUp(self):
        self.approved_series = Series.objects.create(
            name='已审核系列',
            bango='existing_bango',
            intro='系列介绍',
            author='测试作者',
            is_approved=True,
        )
        self.pending_series = Series.objects.create(
            name='待审核系列',
            intro='系列介绍',
            author='测试作者',
        )

    def series_form(self, bango, is_approved=True):
        return AdminSeriesForm(
            data={
                'name': self.pending_series.name,
                'bango': bango,
                'intro': self.pending_series.intro,
                'author': self.pending_series.author,
                'is_approved': is_approved,
            },
            instance=self.pending_series,
        )

    def test_approval_requires_bango(self):
        form = self.series_form('')

        self.assertFalse(form.is_valid())
        self.assertIn('已审核的作品集必须填写代号。', form.errors['bango'])

    def test_approval_rejects_duplicate_bango(self):
        form = self.series_form(self.approved_series.bango)

        self.assertFalse(form.is_valid())
        self.assertIn('该代号已经存在，请重新输入！', form.errors['bango'])

    def test_approval_accepts_unique_bango(self):
        form = self.series_form('unique_bango')

        self.assertTrue(form.is_valid(), form.errors)
        series = form.save()
        self.assertTrue(series.is_approved)
        self.assertEqual(series.bango, 'unique_bango')

    def test_pending_series_can_preserve_unique_bango(self):
        form = self.series_form('reserved_bango', is_approved=False)

        self.assertTrue(form.is_valid(), form.errors)
        series = form.save()
        self.assertFalse(series.is_approved)
        self.assertEqual(series.bango, 'reserved_bango')

    def test_product_requires_approved_series(self):
        product = Product(
            series=self.pending_series,
            name='待审核作品',
            author='测试作者',
            intro='作品介绍',
        )
        form = AdminProductForm(
            data={
                'series': self.pending_series.id,
                'name': product.name,
                'author': product.author,
                'intro': product.intro,
                'is_approved': True,
            },
            files={'file': SimpleUploadedFile('product.txt', b'product')},
            instance=product,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            '所属作品集审核通过并设置代号后，才能审核作品。',
            form.errors['is_approved'],
        )

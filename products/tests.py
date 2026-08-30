from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AuditLog, Product, Series
from .forms import AdminProductForm, AdminSeriesForm
from .validators import MAX_PRODUCT_UPLOAD_SIZE, validate_product_file
from .rate_limits import UPLOAD_LIMIT, upload_rate_limited
from .scanning import ScanResult, scan_product


User = get_user_model()


def zip_upload(filename='product.zip', members=None):
    buffer = BytesIO()
    with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
        for member_name, content in members or [('readme.txt', b'content')]:
            archive.writestr(member_name, content)
    return SimpleUploadedFile(filename, buffer.getvalue())


class FakeScanner:
    def __init__(self, result):
        self.result = result

    def scan(self, file_path):
        return self.result


class ProductDownloadTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            PRIVATE_MEDIA_ROOT=self.media_directory.name
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
            file=SimpleUploadedFile('product.exe', b'MZproduct content'),
            original_filename='product.exe',
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
            'attachment; filename="product.exe"',
        )
        self.assertEqual(b''.join(response.streaming_content), b'MZproduct content')
        self.assertEqual(response.headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        response.close()

    def test_private_file_has_no_public_url(self):
        with self.assertRaises(ValueError):
            _ = self.product.file.url

    def test_disk_name_is_randomized(self):
        self.assertNotEqual(Path(self.product.file.name).name, 'product.exe')
        self.assertTrue(self.product.file.name.endswith('.exe'))

    def test_pending_file_requires_staff_download(self):
        self.product.is_approved = False
        self.product.save(update_fields=['is_approved'])

        public_response = self.client.get(
            reverse('products:download_file', args=[self.product.id])
        )
        admin_response = self.client.get(
            reverse('products:admin_download_file', args=[self.product.id])
        )

        self.assertEqual(public_response.status_code, 404)
        self.assertRedirects(
            admin_response,
            f"{reverse('admin:login')}?next="
            f"{reverse('products:admin_download_file', args=[self.product.id])}",
        )

    def test_staff_can_download_pending_file(self):
        staff = User.objects.create_superuser(
            username='staff',
            password='StrongPassword123!',
            email='staff@example.com',
        )
        self.product.is_approved = False
        self.product.save(update_fields=['is_approved'])
        self.client.force_login(staff)

        response = self.client.get(
            reverse('products:admin_download_file', args=[self.product.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename="product.exe"',
        )
        response.close()

    def test_deleting_product_removes_private_file(self):
        file_path = Path(self.product.file.path)

        self.product.delete()

        self.assertFalse(file_path.exists())


class UploadRequestTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            PRIVATE_MEDIA_ROOT=self.media_directory.name,
            DATA_UPLOAD_MAX_MEMORY_SIZE=110 * 1024 * 1024,
        )
        self.settings_override.enable()
        self.user = User.objects.create_user(
            username='uploader',
            password='StrongPassword123!',
        )
        self.series = Series.objects.create(
            name='上传请求系列',
            bango='upload_series',
            owner=self.user,
            intro='系列介绍',
            author='测试作者',
            is_approved=True,
        )
        self.url = reverse(
            'products:new_product',
            args=[self.series.bango],
        )
        self.client.force_login(self.user)

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def payload(self, name, upload):
        return {
            'name': name,
            'author': '测试作者',
            'intro': '作品介绍',
            'file': upload,
        }

    def test_empty_file_is_rejected(self):
        response = self.client.post(
            self.url,
            self.payload('空文件', SimpleUploadedFile('empty.exe', b'')),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('file', response.context['form'].errors)
        self.assertFalse(Product.objects.filter(name='空文件').exists())

    def test_overlong_filename_is_rejected(self):
        filename = f"{'a' * 260}.exe"
        response = self.client.post(
            self.url,
            self.payload('超长文件名', SimpleUploadedFile(filename, b'MZdata')),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('file', response.context['form'].errors)
        self.assertFalse(Product.objects.filter(name='超长文件名').exists())

    def test_multiple_files_only_accepts_declared_file_field(self):
        response = self.client.post(
            self.url,
            {
                'name': '多文件请求',
                'author': '测试作者',
                'intro': '作品介绍',
                'file': [
                    SimpleUploadedFile('one.exe', b'MZone'),
                    SimpleUploadedFile('two.exe', b'MZtwo'),
                ],
            },
        )

        self.assertIn(response.status_code, {200, 302})
        self.assertLessEqual(
            Product.objects.filter(name='多文件请求').count(),
            1,
        )

    def test_malformed_multipart_request_is_rejected(self):
        response = self.client.generic(
            'POST',
            self.url,
            data=b'--broken-boundary',
            content_type='multipart/form-data; boundary=expected-boundary',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('file', response.context['form'].errors)
        self.assertFalse(Product.objects.filter(name='').exists())

    def test_anonymous_user_cannot_upload(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={self.url}",
        )

    def test_non_owner_cannot_upload(self):
        other_user = User.objects.create_user(
            username='other_uploader',
            password='StrongPassword123!',
        )
        self.client.force_login(other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_unapproved_series_cannot_accept_upload(self):
        self.series.is_approved = False
        self.series.save(update_fields=['is_approved'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)


class EditProductTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            PRIVATE_MEDIA_ROOT=self.media_directory.name
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
            file=SimpleUploadedFile('old.exe', b'MZold content'),
            original_filename='old.exe',
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

    def test_replacing_file_removes_old_private_file(self):
        old_path = Path(self.product.file.path)

        response = self.client.post(
            self.url,
            {
                'name': self.product.name,
                'author': self.product.author,
                'intro': self.product.intro,
                'file': SimpleUploadedFile('new.exe', b'MZnew content'),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.original_filename, 'new.exe')
        self.assertFalse(old_path.exists())
        self.assertTrue(Path(self.product.file.path).exists())


class ProductFileValidatorTests(TestCase):
    def test_valid_exe_is_accepted(self):
        validate_product_file(SimpleUploadedFile('product.exe', b'MZcontent'))

    def test_invalid_extension_is_rejected(self):
        with self.assertRaisesMessage(
            ValidationError,
            '只允许上传 EXE 或 ZIP 文件。',
        ):
            validate_product_file(SimpleUploadedFile('product.txt', b'content'))

    def test_fake_exe_is_rejected(self):
        with self.assertRaisesMessage(
            ValidationError,
            '文件内容不是有效的 EXE 文件。',
        ):
            validate_product_file(SimpleUploadedFile('product.exe', b'not exe'))

    def test_fake_zip_is_rejected(self):
        with self.assertRaisesMessage(
            ValidationError,
            '文件内容不是有效的 ZIP 压缩包。',
        ):
            validate_product_file(SimpleUploadedFile('product.zip', b'not zip'))

    def test_valid_zip_is_accepted(self):
        validate_product_file(zip_upload())

    def test_zip_path_traversal_is_rejected(self):
        upload = zip_upload(members=[('../outside.txt', b'content')])

        with self.assertRaisesMessage(
            ValidationError,
            'ZIP 文件包含不安全的文件路径。',
        ):
            validate_product_file(upload)

    def test_abnormal_compression_ratio_is_rejected(self):
        upload = zip_upload(members=[('large.txt', b'0' * 1024 * 1024)])

        with self.assertRaisesMessage(
            ValidationError,
            'ZIP 文件压缩比例异常。',
        ):
            validate_product_file(upload)

    def test_file_over_100_mb_is_rejected(self):
        upload = SimpleUploadedFile('large.exe', b'MZ')
        upload.size = MAX_PRODUCT_UPLOAD_SIZE + 1

        with self.assertRaisesMessage(
            ValidationError,
            '作品文件大小不能超过 100 MB。',
        ):
            validate_product_file(upload)

    def test_zip_dangerous_extension_is_rejected(self):
        upload = zip_upload(members=[('run.ps1', b'Write-Host unsafe')])

        with self.assertRaisesMessage(
            ValidationError,
            'ZIP 文件包含不允许的危险文件类型。',
        ):
            validate_product_file(upload)

    def test_zip_duplicate_names_are_rejected(self):
        upload = zip_upload(
            members=[('same.txt', b'one'), ('same.txt', b'two')]
        )

        with self.assertRaisesMessage(
            ValidationError,
            'ZIP 文件包含重复的文件名。',
        ):
            validate_product_file(upload)

    def test_zip_drive_path_is_rejected(self):
        upload = zip_upload(members=[('C:\\Windows\\file.dll', b'unsafe')])

        with self.assertRaises(ValidationError) as error:
            validate_product_file(upload)
        self.assertIn('ZIP 文件包含不安全', str(error.exception))


class ProductScanningTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            PRIVATE_MEDIA_ROOT=self.media_directory.name
        )
        self.settings_override.enable()
        self.product = Product.objects.create(
            series=Series.objects.create(
                name='扫描系列',
                bango='scan_series',
                intro='介绍',
                author='作者',
                is_approved=True,
            ),
            name='扫描作品',
            author='作者',
            intro='介绍',
            file=SimpleUploadedFile('scan.exe', b'MZscan'),
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_scanner_result_is_saved(self):
        result = scan_product(
            self.product,
            FakeScanner(ScanResult('clean', 'OK')),
        )

        self.assertEqual(result.status, 'clean')
        self.product.refresh_from_db()
        self.assertEqual(self.product.scan_status, 'clean')
        self.assertIsNotNone(self.product.scanned_at)

    def test_scanner_error_is_not_treated_as_clean(self):
        scan_product(
            self.product,
            FakeScanner(ScanResult('error', 'ClamAV unavailable')),
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.scan_status, 'error')

    @patch('products.scanning.subprocess.run')
    def test_missing_clamav_binary_returns_error(self, run):
        run.side_effect = FileNotFoundError

        result = scan_product(self.product)

        self.assertEqual(result.status, 'error')
        self.product.refresh_from_db()
        self.assertEqual(self.product.scan_status, 'error')


class UploadRateLimitTests(TestCase):
    def test_upload_rate_limit_blocks_after_ten_requests(self):
        request = type('Request', (), {
            'user': type('User', (), {'is_authenticated': True, 'pk': 42})(),
            'META': {},
        })()

        for _ in range(UPLOAD_LIMIT):
            self.assertFalse(upload_rate_limited(request))
        self.assertTrue(upload_rate_limited(request))


class ApprovalVisibilityTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            PRIVATE_MEDIA_ROOT=self.media_directory.name
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
            file=SimpleUploadedFile('approved.exe', b'MZapproved'),
            original_filename='approved.exe',
            is_approved=True,
        )
        self.pending_product = Product.objects.create(
            series=self.approved_series,
            owner=self.user,
            name='待审核作品',
            author='测试作者',
            intro='待审核作品介绍',
            file=SimpleUploadedFile('pending.exe', b'MZpending'),
            original_filename='pending.exe',
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
                'file': SimpleUploadedFile('new.exe', b'MZnew'),
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
            files={'file': SimpleUploadedFile('product.exe', b'MZproduct')},
            instance=product,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            '所属作品集审核通过并设置代号后，才能审核作品。',
            form.errors['is_approved'],
        )

    def test_product_approval_requires_clean_scan(self):
        product = Product(
            series=self.approved_series,
            name='未扫描作品',
            author='测试作者',
            intro='作品介绍',
            is_approved=True,
            scan_status=Product.ScanStatus.PENDING,
        )
        form = AdminProductForm(
            data={
                'series': self.approved_series.id,
                'name': product.name,
                'author': product.author,
                'intro': product.intro,
                'is_approved': True,
                'scan_status': Product.ScanStatus.PENDING,
            },
            files={'file': SimpleUploadedFile('product.exe', b'MZproduct')},
            instance=product,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('文件扫描通过后才能审核作品。', form.errors['scan_status'])


class AuditLogTests(TestCase):
    def test_audit_log_records_admin_approval_change(self):
        admin_user = User.objects.create_superuser(
            username='audit_admin',
            password='StrongPassword123!',
            email='audit@example.com',
        )
        series = Series.objects.create(
            name='审计系列',
            bango='audit_series',
            intro='系列介绍',
            author='测试作者',
            is_approved=True,
        )
        product = Product.objects.create(
            series=series,
            name='审计作品',
            author='测试作者',
            intro='作品介绍',
            file=SimpleUploadedFile('audit.exe', b'MZaudit'),
            original_filename='audit.exe',
            scan_status=Product.ScanStatus.CLEAN,
        )
        self.client.force_login(admin_user)

        response = self.client.post(
            reverse('admin:products_product_change', args=[product.id]),
            {
                'series': series.id,
                'owner': '',
                'name': product.name,
                'author': product.author,
                'intro': product.intro,
                'file': '',
                'original_filename': product.original_filename,
                'file_sha256': product.file_sha256,
                'scan_status': Product.ScanStatus.CLEAN,
                'scanned_at': '',
                'is_approved': 'on',
                '_save': '保存并继续编辑',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AuditLog.objects.filter(
                actor=admin_user,
                action='审核或修改作品',
                model_name='Product',
                object_id=product.id,
            ).exists()
        )

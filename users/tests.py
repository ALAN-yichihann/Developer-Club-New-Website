from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile


User = get_user_model()


class RegisterPageTests(TestCase):
    def test_register_page_uses_chinese_prompts(self):
        response = self.client.get(reverse('users:register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '用户名')
        self.assertContains(response, '密码')
        self.assertContains(response, '密码确认')
        self.assertContains(response, '真实姓名')
        self.assertContains(response, '学籍号')

    def test_real_name_and_student_id_are_required(self):
        response = self.client.post(
            reverse('users:register'),
            {
                'username': 'student',
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='student').exists())

    def test_register_creates_inactive_user_profile_without_login(self):
        response = self.client.post(
            reverse('users:register'),
            {
                'username': 'student',
                'real_name': '张三',
                'student_id': '20260001',
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register_pending.html')
        self.assertContains(response, '注册申请已提交，请等待管理员确认。')
        user = User.objects.get(username='student')
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.real_name, '张三')
        self.assertEqual(user.profile.student_id, '20260001')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inactive_user_cannot_login_or_manage_products(self):
        user = User.objects.create_user(
            username='student',
            password='StrongPassword123!',
            is_active=False,
        )
        UserProfile.objects.create(
            user=user,
            real_name='张三',
            student_id='20260001',
        )

        login_succeeded = self.client.login(
            username='student',
            password='StrongPassword123!',
        )
        response = self.client.get(reverse('products:new_series'))

        self.assertFalse(login_succeeded)
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={reverse('products:new_series')}",
        )

    def test_student_id_must_be_unique(self):
        existing_user = User.objects.create_user(
            username='existing',
            password='StrongPassword123!',
        )
        UserProfile.objects.create(
            user=existing_user,
            real_name='李四',
            student_id='20260001',
        )

        response = self.client.post(
            reverse('users:register'),
            {
                'username': 'student',
                'real_name': '张三',
                'student_id': '20260001',
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '该学籍号已经注册。')
        self.assertFalse(User.objects.filter(username='student').exists())


class LoginApprovalTests(TestCase):
    def setUp(self):
        self.password = 'StrongPassword123!'
        self.user = User.objects.create_user(
            username='student',
            password=self.password,
            is_active=False,
        )

    def test_inactive_user_sees_pending_approval_message(self):
        response = self.client.post(
            reverse('users:login'),
            {
                'username': self.user.username,
                'password': self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '你的账户还未被管理员确认，请等候')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_wrong_password_does_not_reveal_approval_status(self):
        response = self.client.post(
            reverse('users:login'),
            {
                'username': self.user.username,
                'password': 'WrongPassword123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '你的账户还未被管理员确认，请等候')

    def test_active_user_can_login(self):
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])

        response = self.client.post(
            reverse('users:login'),
            {
                'username': self.user.username,
                'password': self.password,
                'next': reverse('website_index:index'),
            },
        )

        self.assertRedirects(response, reverse('website_index:index'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)


class UserAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='StrongPassword123!',
            email='admin@example.com',
        )
        self.user = User.objects.create_user(
            username='student',
            password='StrongPassword123!',
            is_active=False,
        )
        UserProfile.objects.create(
            user=self.user,
            real_name='张三',
            student_id='20260001',
        )
        self.client.force_login(self.admin_user)

    def test_user_list_displays_profile_information(self):
        response = self.client.get(reverse('admin:auth_user_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '真实姓名')
        self.assertContains(response, '学籍号')
        self.assertContains(response, '张三')
        self.assertContains(response, '20260001')

    def test_user_detail_displays_readonly_profile_information(self):
        response = self.client.get(
            reverse('admin:auth_user_change', args=[self.user.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '张三')
        self.assertContains(response, '20260001')


class UserGreetingTests(TestCase):
    def test_authenticated_user_sees_real_name(self):
        user = User.objects.create_user(
            username='student',
            password='StrongPassword123!',
        )
        UserProfile.objects.create(
            user=user,
            real_name='张三',
            student_id='20260001',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('website_index:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '你好，社员张三')

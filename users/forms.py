from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import UserProfile


User = get_user_model()


class ApprovalAuthenticationForm(AuthenticationForm):
    def clean(self):
        try:
            return super().clean()
        except ValidationError as error:
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')

            if username and password:
                try:
                    user = User._default_manager.get_by_natural_key(username)
                except User.DoesNotExist:
                    pass
                else:
                    if user.check_password(password) and not user.is_active:
                        raise ValidationError(
                            '你的账户还未被管理员确认，请等候',
                            code='inactive',
                        ) from error

            raise


class RegisterForm(UserCreationForm):
    real_name = forms.CharField(label='真实姓名', max_length=50)
    student_id = forms.CharField(label='学籍号', max_length=30)

    def clean_real_name(self):
        return self.cleaned_data['real_name'].strip()

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id'].strip()
        if UserProfile.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError('该学籍号已经注册。')
        return student_id

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                real_name=self.cleaned_data['real_name'],
                student_id=self.cleaned_data['student_id'],
            )
        return user

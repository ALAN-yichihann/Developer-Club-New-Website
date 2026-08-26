from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='用户',
    )
    real_name = models.CharField('真实姓名', max_length=50)
    student_id = models.CharField('学籍号', max_length=30, unique=True)

    def __str__(self):
        return f'{self.real_name}（{self.student_id}）'

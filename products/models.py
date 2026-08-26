from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User

english_and_symbols_validator = RegexValidator(
    regex=r'^[a-zA-Z_]+$',
    message='只能输入英文字母和下划线！',
)

class Series(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True, 
        error_messages={
          'unique': '该名称已经存在，请重新输入！',  # 自定义重复提示语
      })
    bango = models.CharField(max_length=20, 
                             validators=[english_and_symbols_validator], 
                             unique=True, 
                             error_messages={
          'unique': '该代号已经存在，请重新输入！',  # 自定义重复提示语
      })
    owner = models.ForeignKey(User,
                              on_delete=models.SET_NULL,
                              null=True,
                              blank=True,)
    intro = models.TextField()
    author = author = models.CharField(max_length=100)
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'series'

    def __str__(self):
        return self.name

class Product(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                              null=True,
                              blank=True)
    name = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)
    intro = models.TextField()
    file = models.FileField(upload_to="products/%Y/%m/")

    def __str__(self) -> str:
        return self.name

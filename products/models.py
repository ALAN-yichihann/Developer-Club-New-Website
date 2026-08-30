from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models

from .storage import private_product_storage
from .validators import product_upload_path, validate_product_file

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
                             blank=True,
                             null=True,
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
    is_approved = models.BooleanField('已审核', default=False)

    class Meta:
        verbose_name_plural = 'series'
        constraints = [
            models.UniqueConstraint(
                fields=['bango'],
                condition=models.Q(bango__isnull=False) & ~models.Q(bango=''),
                name='unique_nonempty_series_bango',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_approved=False)
                    | (
                        models.Q(is_approved=True, bango__isnull=False)
                        & ~models.Q(bango='')
                    )
                ),
                name='series_approval_requires_bango',
            ),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    class ScanStatus(models.TextChoices):
        PENDING = 'pending', '等待扫描'
        CLEAN = 'clean', '扫描通过'
        INFECTED = 'infected', '发现风险'
        ERROR = 'error', '扫描失败'

    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                              null=True,
                              blank=True)
    name = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)
    intro = models.TextField()
    file = models.FileField(
        upload_to=product_upload_path,
        storage=private_product_storage,
        validators=[validate_product_file],
    )
    original_filename = models.CharField(
        '原始文件名',
        max_length=255,
        blank=True,
    )
    file_sha256 = models.CharField('文件 SHA-256', max_length=64, blank=True)
    scan_status = models.CharField(
        '扫描状态',
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
    )
    scanned_at = models.DateTimeField('扫描时间', null=True, blank=True)
    is_approved = models.BooleanField('已审核', default=False)

    def __str__(self) -> str:
        return self.name


class AuditLog(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_audit_logs',
    )
    action = models.CharField('操作', max_length=50)
    model_name = models.CharField('模型', max_length=50)
    object_id = models.PositiveBigIntegerField('对象 ID')
    details = models.JSONField('详情', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('IP 地址', null=True, blank=True)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.model_name} {self.object_id} - {self.action}'

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils.html import format_html

from .forms import AdminProductForm, AdminSeriesForm
from .models import AuditLog, Product, Series


def log_audit(request, action, instance, details):
    AuditLog.objects.create(
        actor=request.user,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR'),
    )


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    form = AdminSeriesForm
    list_display = ('name', 'bango', 'owner', 'is_approved', 'date_added')
    list_filter = ('is_approved',)
    search_fields = ('name', 'bango', 'author')

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return super().has_view_permission(request, obj)
        return request.user.is_staff

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return super().has_module_permission(request)
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return super().has_change_permission(request, obj)
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_readonly_fields(request, obj)
        return tuple(
            field.name for field in self.model._meta.fields
            if field.name not in {'bango', 'is_approved'}
        )

    def save_model(self, request, obj, form, change):
        old_approved = Series.objects.filter(pk=obj.pk).values_list(
            'is_approved', flat=True
        ).first()
        try:
            super().save_model(request, obj, form, change)
        except IntegrityError as error:
            raise ValidationError('该代号已经存在，请重新输入！') from error
        if old_approved != obj.is_approved or 'bango' in form.changed_data:
            log_audit(
                request,
                '审核或修改作品集',
                obj,
                {'is_approved': obj.is_approved, 'bango': obj.bango},
            )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = AdminProductForm
    list_display = ('name', 'series', 'owner', 'is_approved', 'date_added')
    list_filter = ('is_approved',)
    search_fields = ('name', 'author')
    readonly_fields = (
        'original_filename',
        'file_sha256',
        'scan_status',
        'scanned_at',
        'download_link',
    )

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return super().has_view_permission(request, obj)
        return request.user.is_staff

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return super().has_module_permission(request)
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return super().has_change_permission(request, obj)
        return request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_readonly_fields(request, obj)
        return tuple(
            field.name for field in self.model._meta.fields
            if field.name != 'is_approved'
        ) + ('download_link',)

    @admin.display(description='审核文件')
    def download_link(self, product):
        if not product.pk or not product.file:
            return '-'
        url = reverse('products:admin_download_file', args=[product.pk])
        return format_html('<a href="{}">下载文件进行审核</a>', url)

    def save_model(self, request, obj, form, change):
        old_approved = Product.objects.filter(pk=obj.pk).values_list(
            'is_approved', flat=True
        ).first()
        super().save_model(request, obj, form, change)
        if old_approved != obj.is_approved or 'file' in form.changed_data:
            log_audit(
                request,
                '审核或修改作品',
                obj,
                {
                    'is_approved': obj.is_approved,
                    'scan_status': obj.scan_status,
                    'file_sha256': obj.file_sha256,
                },
            )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'model_name', 'object_id')
    list_filter = ('action', 'model_name')
    readonly_fields = (
        'actor', 'action', 'model_name', 'object_id', 'details',
        'ip_address', 'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .forms import AdminProductForm, AdminSeriesForm
from .models import Product, Series


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    form = AdminSeriesForm
    list_display = ('name', 'bango', 'owner', 'is_approved', 'date_added')
    list_filter = ('is_approved',)
    search_fields = ('name', 'bango', 'author')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = AdminProductForm
    list_display = ('name', 'series', 'owner', 'is_approved', 'date_added')
    list_filter = ('is_approved',)
    search_fields = ('name', 'author')
    readonly_fields = ('original_filename', 'download_link')

    @admin.display(description='审核文件')
    def download_link(self, product):
        if not product.pk or not product.file:
            return '-'
        url = reverse('products:admin_download_file', args=[product.pk])
        return format_html('<a href="{}">下载文件进行审核</a>', url)

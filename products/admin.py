from django.contrib import admin

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

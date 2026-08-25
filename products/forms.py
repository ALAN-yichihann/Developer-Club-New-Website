from django import forms

from .models import Series, Product

class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ['name','bango', 'intro', 'author', ]
        labels = {'name': '系列名称','bango': '唯一代号（仅允许英文字母和下划线）', 'intro': '系列介绍', 'author': '作者'}

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', ]
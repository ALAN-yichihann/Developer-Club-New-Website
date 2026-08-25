from django import forms

from .models import Series, Product

class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ['name', 'bango', 'intro', 'author', ]
        labels = {'name': '系列名称','bango': '唯一代号（仅允许英文字母和下划线）', 'intro': '系列介绍', 'author': '作者'}
        widgets = {'intro': forms.Textarea(attrs={'cols': 80})}


class EditSeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ['name', 'intro', 'author']
        labels = {
            'name': '系列名称',
            'intro': '系列介绍',
            'author': '作者',
        }
        widgets = {'intro': forms.Textarea(attrs={'cols': 80})}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'author', 'intro', 'file']
        labels = {
            'name': '版本名称', 'author': '作者', 'intro': '介绍', 'file': '作品文件'
        }
        widgets = {'intro': forms.Textarea(attrs={'cols': 80})}

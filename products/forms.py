from django import forms

from .models import Product, Series


class EditProductFileInput(forms.ClearableFileInput):
    template_name = 'products/widgets/edit_product_file_input.html'
    input_text = '更改为'


class SeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = ['name', 'intro', 'author', ]
        labels = {'name': '系列名称', 'intro': '系列介绍', 'author': '作者'}
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


class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'author', 'intro', 'file']
        labels = {
            'name': '版本名称',
            'author': '作者',
            'intro': '介绍',
            'file': '作品文件',
        }
        widgets = {
            'intro': forms.Textarea(attrs={'cols': 80}),
            'file': EditProductFileInput(),
        }


class AdminSeriesForm(forms.ModelForm):
    class Meta:
        model = Series
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        bango = (cleaned_data.get('bango') or '').strip()
        is_approved = cleaned_data.get('is_approved')
        if is_approved and not bango:
            self.add_error('bango', '已审核的作品集必须填写代号。')
        if not is_approved and bango:
            self.add_error('bango', '未审核的作品集不能设置代号。')
        if bango and Series.objects.filter(bango=bango).exclude(
            pk=self.instance.pk
        ).exists():
            self.add_error('bango', '该代号已经存在，请重新输入！')
        cleaned_data['bango'] = bango or None
        return cleaned_data


class AdminProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_approved'):
            series = cleaned_data.get('series')
            if not series or not series.is_approved or not series.bango:
                self.add_error(
                    'is_approved',
                    '所属作品集审核通过并设置代号后，才能审核作品。',
                )
        return cleaned_data

from django import forms

from .models import Product, Series
from .validators import calculate_sha256


class EditProductFileInput(forms.ClearableFileInput):
    template_name = 'products/widgets/edit_product_file_input.html'
    input_text = '更改为'

    def __init__(self, attrs=None):
        attrs = {'accept': '.exe,.zip', **(attrs or {})}
        super().__init__(attrs)

    def is_initial(self, value):
        return bool(value and getattr(value, 'name', None))


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
        widgets = {
            'intro': forms.Textarea(attrs={'cols': 80}),
            'file': forms.ClearableFileInput(attrs={'accept': '.exe,.zip'}),
        }


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
        widgets = {
            'file': EditProductFileInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_approved'):
            series = cleaned_data.get('series')
            if not series or not series.is_approved or not series.bango:
                self.add_error(
                    'is_approved',
                    '所属作品集审核通过并设置代号后，才能审核作品。',
                )
            scan_status = cleaned_data.get(
                'scan_status',
                self.instance.scan_status,
            )
            if scan_status != Product.ScanStatus.CLEAN:
                self.add_error(
                    'scan_status',
                    '文件扫描通过后才能审核作品。',
                )
        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        if self.files.get('file'):
            product.file_sha256 = calculate_sha256(self.files['file'])
            product.scan_status = Product.ScanStatus.PENDING
            product.scanned_at = None
        if commit:
            product.save()
            self.save_m2m()
        return product

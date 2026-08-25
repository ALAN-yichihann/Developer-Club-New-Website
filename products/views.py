from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect

from .models import Product, Series
from .forms import SeriesForm

def all_products(request):
    """评论页面"""
    series = Series.objects.order_by('date_added')
    context = {'series': series}
    return render(request, 'products/products.html', context)


def single_series(request, bango):
    """显示单个作品集的页面"""
    series = Series.objects.get(bango=bango)
    products = series.product_set.order_by('-date_added')
    context = {'series': series, 'products': products}
    return render(request, 'products/product.html', context)


def download_file(request, product_id):
    """下载文件"""
    product = get_object_or_404(Product, id=product_id)
    if not product.file:
        raise Http404("文件不存在")

    try:
        product_file = product.file.open('rb')
    except FileNotFoundError as error:
        raise Http404("文件不存在") from error

    filename = Path(product.file.name).name
    return FileResponse(product_file, as_attachment=True, filename=filename)

def my_works(request):
    """用户个人的作品"""
    series = Series.objects.order_by('date_added')
    context = {'series': series}
    return render(request, 'products/my_works.html', context)

def new_series(request):
    """添加新作品合集"""
    if request.method != 'POST':
        # 未提交数据，创建一个新表单
        form = SeriesForm()
    else:
        # POST提交数据，处理
        form = SeriesForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('products:all_products')

    context = {'form': form}
    return render(request, 'products/new_series.html', context)
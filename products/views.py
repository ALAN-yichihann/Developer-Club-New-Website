from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from .models import Product, Series

def all_products(request):
    """评论页面"""
    series = Series.objects.order_by('date_added')
    context = {'series': series}
    return render(request, 'products/products.html', context)


def single_series(request, series_id):
    series = Series.objects.get(id=series_id)
    products = series.product_set.order_by('-date_added')
    context = {'series': series, 'products': products}
    return render(request, 'products/product.html', context)


def download_file(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not product.file:
        raise Http404("文件不存在")

    try:
        product_file = product.file.open('rb')
    except FileNotFoundError as error:
        raise Http404("文件不存在") from error

    filename = Path(product.file.name).name
    return FileResponse(product_file, as_attachment=True, filename=filename)

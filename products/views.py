from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EditProductForm, EditSeriesForm, ProductForm, SeriesForm
from .models import Product, Series


def all_products(request):
    """所有作品页面"""
    series = (
        Series.objects.filter(is_approved=True)
        .exclude(bango__isnull=True)
        .exclude(bango='')
        .order_by('date_added')
    )
    context = {'series': series}
    return render(request, 'products/products.html', context)


def single_series(request, bango):
    """显示单个作品集的页面"""
    series = get_object_or_404(Series, bango=bango, is_approved=True)
    products = series.product_set.filter(is_approved=True).order_by('-date_added')
    context = {'series': series, 'products': products}
    return render(request, 'products/product.html', context)


def download_file(request, product_id):
    """下载文件"""
    product = get_object_or_404(
        Product,
        id=product_id,
        is_approved=True,
        series__is_approved=True,
    )
    if not product.file:
        raise Http404("文件不存在")

    try:
        product_file = product.file.open('rb')
    except FileNotFoundError as error:
        raise Http404("文件不存在") from error

    filename = product.original_filename or Path(product.file.name).name
    response = FileResponse(
        product_file,
        as_attachment=True,
        filename=filename,
        content_type='application/octet-stream',
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@staff_member_required
def admin_download_file(request, product_id):
    """供管理员审核时下载作品文件。"""
    if not request.user.has_perm('products.view_product'):
        raise PermissionDenied
    product = get_object_or_404(Product, id=product_id)
    if not product.file:
        raise Http404('文件不存在')

    try:
        product_file = product.file.open('rb')
    except FileNotFoundError as error:
        raise Http404('文件不存在') from error

    filename = product.original_filename or Path(product.file.name).name
    response = FileResponse(
        product_file,
        as_attachment=True,
        filename=filename,
        content_type='application/octet-stream',
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
def my_works(request):
    """用户个人的作品"""
    series = (
        Series.objects.filter(owner=request.user, is_approved=True)
        .exclude(bango__isnull=True)
        .exclude(bango='')
        .order_by('date_added')
    )
    pending_series_count = Series.objects.filter(
        owner=request.user,
        is_approved=False,
    ).count()
    context = {
        'series': series,
        'pending_series_count': pending_series_count,
    }
    return render(request, 'products/my_works.html', context)

@login_required
def series_added(request):
    """已添加，未审核"""
    return render(request, 'products/series_added.html', {})

@login_required
def new_series(request):
    """添加新作品合集"""
    if request.method != 'POST':
        # 未提交数据，创建一个新表单
        form = SeriesForm()
    else:
        # POST提交数据，处理
        form = SeriesForm(data=request.POST)
        if form.is_valid():
            new_series = form.save(commit=False)
            new_series.owner = request.user
            new_series.save()
            return redirect('products:series_added')

    context = {'form': form}
    return render(request, 'products/new_series.html', context)


@login_required
def new_product(request, bango):
    """添加新作品"""
    series = get_object_or_404(Series, bango=bango, is_approved=True)

    if series.owner != request.user:
        raise Http404
    if request.method != 'POST':
        form = ProductForm()
    else:
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                product.original_filename = Path(uploaded_file.name).name
            product.owner = request.user
            product.series = series
            product.save()
            return redirect(
                'products:my_single_series',
                bango=bango,
            )

    context = {'form': form, 'series': series}
    return render(request, 'products/new_product.html', context)


@login_required
def my_single_series(request, bango):
    """显示个人单个作品集的页面"""
    series = get_object_or_404(Series, bango=bango, is_approved=True)
    if series.owner != request.user:
        raise Http404
    products = series.product_set.filter(is_approved=True).order_by('-date_added')
    pending_product_count = series.product_set.filter(
        is_approved=False
    ).count()
    context = {
        'series': series,
        'products': products,
        'pending_product_count': pending_product_count,
    }
    return render(request, 'products/my_single_series.html', context)


@login_required
def edit_single_series(request, bango):
    """编辑单个作品集的页面"""
    series = get_object_or_404(Series, bango=bango, is_approved=True)
    if series.owner != request.user:
        raise Http404
    if request.method != 'POST':
        # 初次生成，使用当前内容填充
        form = EditSeriesForm(instance=series)
    else:
        form = EditSeriesForm(instance=series, data=request.POST)
        # POST提交数据，处理
        if form.is_valid():
            if not form.has_changed():
                return redirect(
                    'products:my_single_series',
                    bango=series.bango,
                )
            updated_series = form.save(commit=False)
            updated_series.is_approved = False
            updated_series.save()
            return redirect('products:series_added')
    context = {'series': series, 'form': form}
    return render(request, 'products/edit_series.html', context)


@login_required
def edit_product(request, bango, product_id):
    """编辑单个作品"""
    series = get_object_or_404(Series, bango=bango, is_approved=True)
    product = get_object_or_404(
        Product,
        id=product_id,
        series=series,
        is_approved=True,
    )
    if series.owner != request.user:
        raise Http404
    if request.method == 'POST':
        old_file_name = product.file.name
        form = EditProductForm(
            request.POST,
            request.FILES,
            instance=product,
        )
        if form.is_valid():
            if not form.has_changed():
                return redirect(
                    'products:my_single_series',
                    bango=series.bango,
                )
            updated_product = form.save(commit=False)
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                updated_product.original_filename = Path(uploaded_file.name).name
            updated_product.is_approved = False
            updated_product.save()
            if old_file_name != updated_product.file.name and old_file_name:
                product.file.storage.delete(old_file_name)
            return redirect(
                'products:my_single_series',
                bango=series.bango,
            )
    else:
        form = EditProductForm(instance=product)

    context = {
        'series': series,
        'product': product,
        'form': form,
    }
    return render(request, 'products/edit_product.html', context)

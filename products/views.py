from django.shortcuts import render

from .models import Product, Series

def all_products(request):
    """评论页面"""
    series = Series.objects.order_by('date_added')
    context = {'series': series}
    return render(request, 'comments/comment_list.html', context)
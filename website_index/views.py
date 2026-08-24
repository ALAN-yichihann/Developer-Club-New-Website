from django.shortcuts import render

def index(request):
    """网站主页"""
    return render(request, 'website_index/index.html')
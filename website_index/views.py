from django.shortcuts import render

from .models import Intro

def index(request):
    """网站主页"""
    intro = Intro.objects.first()
    context = {'intro': intro}
    return render(request, 'website_index/index.html', context)
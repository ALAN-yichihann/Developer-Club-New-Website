from django.shortcuts import render

from .models import Intro

def index(request):
    """网站主页"""
    intro = Intro.objects.first()  # 获取第一条Intro对象
    context = {'intro': intro}
    return render(request, 'website_index/index.html', context)

def intro_list(request):
    """介绍页面，显示所有intro对象"""
    intros = Intro.objects.all()
    context = {'intros': intros}
    return render(request, 'website_index/intros.html', context)
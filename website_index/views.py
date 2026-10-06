from django.shortcuts import render

from random import randint

from .models import Intro, Development, Moment, Activity, Info, Link
from products.models import Product

def index(request):
    """网站主页"""
    intro = Intro.objects.first()  # 获取第一条Intro对象
    moments = Moment.objects.order_by('?')[:3]
    works = Product.objects.filter(
        is_approved=True,
        series__is_approved=True,
    ).order_by('-date_added')[:3]
    links = Link.objects.all()  # 获取所有Link对象
    context = {'intro': intro, 'moments': moments, 'works': works, 'links': links}
    return render(request, 'website_index/index.html', context)

def intro_list(request):
    """介绍页面，显示所有intro对象"""
    intros = Intro.objects.all()
    context = {'intros': intros}
    return render(request, 'website_index/intros.html', context)

def history(request):
    """大事记页面"""
    developments = Development.objects.all()
    context = {'developments': developments}
    return render(request, 'website_index/history.html', context)

def activities(request):
    """活动与规划页面"""
    activities = Activity.objects.all()
    context = {'activities': activities}
    return render(request, 'website_index/activities.html', context)

def join_us(request):
    """加入我们"""
    info = Info.objects.first()
    context = {'info': info}
    return render(request, 'website_index/joinus.html', context)

def haruhi(request):
    """彩蛋！"""
    hitome = '00' + str(randint(29700, 30000))
    context = {'hitome': hitome, 'lang': 'jp'}
    return render(request, 'website_index/haruhi.html', context)

def haruhi_cn(request):
    """彩蛋！"""
    hitome = '00' + str(randint(29700, 30000))
    context = {'hitome': hitome, 'lang': 'cn'}
    return render(request, 'website_index/haruhi.html', context)

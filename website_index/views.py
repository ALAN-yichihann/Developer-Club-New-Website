from django.shortcuts import render

from .models import Intro, Development, Moment, Activity, Info
from products.models import Product

def index(request):
    """网站主页"""
    intro = Intro.objects.first()  # 获取第一条Intro对象
    moments = Moment.objects.order_by('?')[:3]
    works = Product.objects.order_by('-date_added')[:3]
    context = {'intro': intro, 'moments': moments, 'works': works}
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
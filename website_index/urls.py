"""定义网站主页的url模式"""

from django.urls import path

from . import views

app_name = 'website_index'
urlpatterns = [
    # 主页
    path('', views.index, name='index'),
    path('intros/', views.intro_list, name='intro_list'),
    path('history/', views.history, name='history'),
    path('activities/', views.activities, name='activities'),
    path('joinus/', views.join_us, name='join_us')
]
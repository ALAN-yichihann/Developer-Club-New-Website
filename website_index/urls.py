"""定义网站主页的url模式"""

from django.urls import path

from . import views

app_name = 'website_index'
urlpatterns = [
    # 主页
    path('', views.index, name='index'),
]
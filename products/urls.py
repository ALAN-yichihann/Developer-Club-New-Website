"""定义products应用的URL模式"""

from django.urls import path

from . import views

app_name = 'products'
urlpatterns = [
    path('', views.all_products, name='all_productss'),
    ]
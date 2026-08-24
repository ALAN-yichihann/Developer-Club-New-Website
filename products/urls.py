"""定义products应用的URL模式"""

from django.urls import path

from . import views

app_name = 'products'
urlpatterns = [
    path('', views.all_products, name='all_products'),
    path('download/<int:product_id>/', views.download_file, name='download_file'),
    path('<int:series_id>/', views.single_series, name='single_series')
    ]

"""定义products应用的URL模式"""

from django.urls import path

from . import views

app_name = 'products'
urlpatterns = [
    path('', views.all_products, name='all_products'),
    path('my_works/', views.my_works, name='my_works'),
    path('new_series/', views.new_series, name='new_series'),
    path('my_works/series_added', views.series_added, name='series_added'),
    path('download/<int:product_id>/', views.download_file, name='download_file'),
    path(
        'admin-download/<int:product_id>/',
        views.admin_download_file,
        name='admin_download_file',
    ),
    path('<str:bango>/', views.single_series, name='single_series'),
    path('my_works/<str:bango>/', views.my_single_series, name='my_single_series'),
    path('my_works/<str:bango>/edit', views.edit_single_series, name='edit_single_series'),
    path('my_works/<str:bango>/new_work/', views.new_product, name='new_product'),
    path(
        'my_works/<str:bango>/<int:product_id>/edit/',
        views.edit_product,
        name='edit_product',
    ),
    ]

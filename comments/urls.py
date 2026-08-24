"""定义comments应用的URL模式"""

from django.urls import path

from . import views

app_name = 'comments'
urlpatterns = [
    path('comments/', views.comment_list, name='comment_list'),]
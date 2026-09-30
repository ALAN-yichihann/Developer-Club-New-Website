"""为users定义url模式"""

from django.urls import path, include

from . import views

app_name = 'users'
urlpatterns = [
    path('captcha/', views.captcha_image, name='captcha_image'),
    # 使用包含账户审核提示的登录页面
    path('login/', views.UserLoginView.as_view(), name='login'),
    # 包含默认的身份验证url
    path('', include('django.contrib.auth.urls')),
    # 注册页面
    path('register/', views.register, name='register'),
]

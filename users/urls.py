"""为users定义url模式"""

from django.urls import path, include

app_name = 'users'
urlpatterns = [
    # 包含默认的身份验证url
    path('', include('django.contrib.auth.urls'))
]
from django.shortcuts import render
from django.contrib.auth.views import LoginView

from .forms import ApprovalAuthenticationForm, RegisterForm


class UserLoginView(LoginView):
    authentication_form = ApprovalAuthenticationForm

def register(request):
    """注册新用户"""
    if request.method != 'POST':
        # 显示空注册表单
        form = RegisterForm()
    else:
        # 处理填写好的表单
        form = RegisterForm(data=request.POST)

        if form.is_valid():
            form.save()
            return render(request, 'registration/register_pending.html')

    # 显示空表单或指出表单无效
    context = {'form': form}
    return render(request, 'registration/register.html', context)

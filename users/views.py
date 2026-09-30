import secrets
import string

from PIL import Image, ImageDraw, ImageFont
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

from .forms import ApprovalAuthenticationForm, RegisterForm


CAPTCHA_SESSION_KEY = 'login_register_captcha'
CAPTCHA_LENGTH = 6


class UserLoginView(LoginView):
    authentication_form = ApprovalAuthenticationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['captcha_code'] = self.request.session.pop(CAPTCHA_SESSION_KEY, None)
        return kwargs


@never_cache
def captcha_image(request):
    """生成并返回绑定到当前会话的一次性图片验证码。"""
    alphabet = string.ascii_letters.translate(
        str.maketrans('', '', 'IiLl')
    ) + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(CAPTCHA_LENGTH))
    request.session[CAPTCHA_SESSION_KEY] = code.upper()

    image = Image.new('RGB', (250, 76), color=(246, 248, 250))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=34)
    for _ in range(18):
        x1 = secrets.randbelow(250)
        y1 = secrets.randbelow(76)
        x2 = secrets.randbelow(250)
        y2 = secrets.randbelow(76)
        draw.line((x1, y1, x2, y2), fill=(
            secrets.randbelow(130), secrets.randbelow(130), secrets.randbelow(130)
        ), width=1)
    for index, character in enumerate(code):
        draw.text(
            (12 + index * 38, 13 + secrets.randbelow(12)),
            character,
            font=font,
            fill=(20, 35, 55),
        )

    response = HttpResponse(content_type='image/png')
    image.save(response, format='PNG')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response

def register(request):
    """注册新用户"""
    if request.method != 'POST':
        # 显示空注册表单
        form = RegisterForm()
    else:
        # 处理填写好的表单
        captcha_code = request.session.pop(CAPTCHA_SESSION_KEY, None)
        form = RegisterForm(data=request.POST, captcha_code=captcha_code)

        if form.is_valid():
            form.save()
            return render(request, 'registration/register_pending.html')

    # 显示空表单或指出表单无效
    context = {'form': form}
    return render(request, 'registration/register.html', context)

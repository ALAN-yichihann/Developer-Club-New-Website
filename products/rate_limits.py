from django.core.cache import cache


UPLOAD_LIMIT = 10
UPLOAD_WINDOW = 60 * 60


def upload_rate_limited(request):
    identity = request.user.pk if request.user.is_authenticated else request.META.get(
        'REMOTE_ADDR', 'unknown'
    )
    key = f'product-upload:{identity}'
    try:
        if cache.add(key, 1, UPLOAD_WINDOW):
            return False
        count = cache.incr(key)
        return count > UPLOAD_LIMIT
    except ValueError:
        return False

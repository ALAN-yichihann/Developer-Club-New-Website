from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count

from products.models import Product, Series
from users.models import UserProfile


class Command(BaseCommand):
    help = '检查作品、作品集、用户资料和私有文件的一致性。'

    def handle(self, *args, **options):
        User = get_user_model()
        errors = []
        duplicate_bangos = (
            Series.objects.exclude(bango__isnull=True)
            .exclude(bango='')
            .values('bango')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        errors.extend(
            f"重复 bango：{item['bango']}（{item['count']} 条）"
            for item in duplicate_bangos
        )

        for series in Series.objects.filter(is_approved=True):
            if not series.bango:
                errors.append(f'已审核作品集缺少 bango：{series.pk}')

        for product in Product.objects.exclude(file=''):
            if not Path(product.file.path).exists():
                errors.append(f'作品文件不存在：Product {product.pk}')

        errors.extend(
            f'用户缺少资料：User {user.pk}'
            for user in User.objects.filter(profile__isnull=True)
        )

        if errors:
            for error in errors:
                self.stderr.write(error)
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('数据库与私有文件一致性检查通过。'))

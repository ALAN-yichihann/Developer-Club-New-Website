from django.core.management.base import BaseCommand

from products.models import Product
from products.scanning import scan_product


class Command(BaseCommand):
    help = '扫描所有等待扫描的作品文件。'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='本次最多扫描的文件数量。',
        )

    def handle(self, *args, **options):
        limit = options['limit']

        products = (
            Product.objects.filter(
                scan_status=Product.ScanStatus.PENDING,
            )
            .exclude(file='')
            .order_by('id')[:limit]
        )

        count = 0

        for product in products:
            count += 1

            try:
                result = scan_product(product)
            except Exception as error:
                product.scan_status = Product.ScanStatus.ERROR
                product.scanned_at = None
                product.save(
                    update_fields=[
                        'scan_status',
                        'scanned_at',
                    ]
                )
                self.stderr.write(
                    self.style.ERROR(
                        f'Product {product.pk} 扫描异常：{error}'
                    )
                )
                continue

            self.stdout.write(
                f'Product {product.pk}: '
                f'{result.status} '
                f'{result.detail}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'本次处理 {count} 个待扫描作品。'
            )
        )

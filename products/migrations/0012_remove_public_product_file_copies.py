from pathlib import Path

from django.conf import settings
from django.db import migrations


def remove_public_product_file_copies(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    public_root = Path(settings.MEDIA_ROOT)
    private_root = Path(settings.PRIVATE_MEDIA_ROOT)

    for product in Product.objects.exclude(file=''):
        file_name = str(product.file)
        public_file = public_root / file_name
        private_file = private_root / file_name
        if private_file.exists() and public_file.exists():
            public_file.unlink()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_product_original_filename_alter_product_file'),
    ]

    operations = [
        migrations.RunPython(
            remove_public_product_file_copies,
            migrations.RunPython.noop,
        ),
    ]

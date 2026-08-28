from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property


@deconstructible
class PrivateProductStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(base_url=None)

    @cached_property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    @cached_property
    def base_url(self):
        return None

    def _clear_cached_properties(self, setting, **kwargs):
        super()._clear_cached_properties(setting, **kwargs)
        if setting == 'PRIVATE_MEDIA_ROOT':
            self.__dict__.pop('base_location', None)
            self.__dict__.pop('location', None)


private_product_storage = PrivateProductStorage()

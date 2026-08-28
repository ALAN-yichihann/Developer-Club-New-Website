from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile, is_zipfile

from django.core.exceptions import ValidationError
from django.utils import timezone


MAX_PRODUCT_UPLOAD_SIZE = 100 * 1024 * 1024
MAX_EXTRACTED_SIZE = 500 * 1024 * 1024
MAX_ARCHIVE_FILES = 2000
MAX_COMPRESSION_RATIO = 100


def product_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    date_path = timezone.localdate().strftime('%Y/%m')
    return f'products/{date_path}/{uuid4().hex}{suffix}'


def validate_product_file(uploaded_file):
    should_close = bool(getattr(uploaded_file, 'closed', False))
    try:
        _validate_product_file(uploaded_file)
    finally:
        if should_close:
            uploaded_file.close()
        elif not uploaded_file.closed:
            uploaded_file.seek(0)


def _validate_product_file(uploaded_file):
    if uploaded_file.size > MAX_PRODUCT_UPLOAD_SIZE:
        raise ValidationError('作品文件大小不能超过 100 MB。')

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {'.exe', '.zip'}:
        raise ValidationError('只允许上传 EXE 或 ZIP 文件。')

    uploaded_file.seek(0)
    header = uploaded_file.read(2)
    uploaded_file.seek(0)

    if suffix == '.exe':
        if header != b'MZ':
            raise ValidationError('文件内容不是有效的 EXE 文件。')
        return

    if not is_zipfile(uploaded_file):
        raise ValidationError('文件内容不是有效的 ZIP 压缩包。')

    uploaded_file.seek(0)
    try:
        with ZipFile(uploaded_file) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_FILES:
                raise ValidationError('ZIP 文件包含的文件数量过多。')

            total_size = sum(member.file_size for member in members)
            compressed_size = sum(max(member.compress_size, 1) for member in members)
            if total_size > MAX_EXTRACTED_SIZE:
                raise ValidationError('ZIP 文件解压后的总体积过大。')
            if total_size / compressed_size > MAX_COMPRESSION_RATIO:
                raise ValidationError('ZIP 文件压缩比例异常。')

            for member in members:
                member_path = Path(member.filename)
                if member.flag_bits & 0x1:
                    raise ValidationError('不允许上传加密 ZIP 文件。')
                if member_path.is_absolute() or '..' in member_path.parts:
                    raise ValidationError('ZIP 文件包含不安全的文件路径。')

            if archive.testzip() is not None:
                raise ValidationError('ZIP 文件中的内容已损坏。')
    except BadZipFile as error:
        raise ValidationError('文件内容不是有效的 ZIP 压缩包。') from error

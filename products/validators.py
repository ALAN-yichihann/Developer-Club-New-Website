from pathlib import Path
import re
import hashlib
import os
from uuid import uuid4
from zipfile import BadZipFile, ZipFile, is_zipfile

from django.core.exceptions import ValidationError
from django.utils import timezone


MAX_PRODUCT_UPLOAD_SIZE = 150 * 1024 * 1024
MAX_EXTRACTED_SIZE = 500 * 1024 * 1024
MAX_ARCHIVE_FILES = 2000
MAX_COMPRESSION_RATIO = 100
MAX_ARCHIVE_MEMBER_SIZE = 100 * 1024 * 1024
DANGEROUS_ARCHIVE_EXTENSIONS = {
    '.bat', '.cmd', '.com', '.dll', '.js', '.ps1', '.scr', '.sh', '.vbs',
}


def product_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    date_path = timezone.localdate().strftime('%Y/%m')
    return f'products/quarantine/{date_path}/{uuid4().hex}{suffix}'


def calculate_sha256(uploaded_file):
    digest = hashlib.sha256()
    uploaded_file.seek(0)
    for chunk in iter(lambda: uploaded_file.read(1024 * 1024), b''):
        digest.update(chunk)
    uploaded_file.seek(0)
    return digest.hexdigest()


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
    if len(Path(uploaded_file.name).name) > 255:
        raise ValidationError('文件名长度不能超过 255 个字符。')
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
                if member.is_dir() and len(member_path.parts) > 8:
                    raise ValidationError('ZIP 文件目录层级过深。')
                if member.file_size > MAX_ARCHIVE_MEMBER_SIZE:
                    raise ValidationError('ZIP 文件中的单个文件过大。')
                if member.is_dir() is False and member.create_system == 3:
                    mode = (member.external_attr >> 16) & 0o170000
                    if mode == 0o120000:
                        raise ValidationError('ZIP 文件不允许包含符号链接。')
                if os.path.splitdrive(member.filename)[0] or re.match(
                    r'^[a-zA-Z]:[\\/]', member.filename
                ):
                    raise ValidationError('ZIP 文件包含不安全的盘符路径。')
                if member_path.suffix.lower() in DANGEROUS_ARCHIVE_EXTENSIONS:
                    raise ValidationError('ZIP 文件包含不允许的危险文件类型。')

            names = [member.filename for member in members]
            if len(names) != len(set(names)):
                raise ValidationError('ZIP 文件包含重复的文件名。')

            if archive.testzip() is not None:
                raise ValidationError('ZIP 文件中的内容已损坏。')
    except BadZipFile as error:
        raise ValidationError('文件内容不是有效的 ZIP 压缩包。') from error

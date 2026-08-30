import subprocess
from dataclasses import dataclass
from pathlib import Path

from django.utils import timezone

from .models import Product


@dataclass(frozen=True)
class ScanResult:
    status: str
    detail: str = ''


class ClamAVScanner:
    """通过本机 clamdscan 调用 ClamAV。"""

    def scan(self, file_path):
        path = Path(file_path)
        try:
            result = subprocess.run(
                ['clamdscan', '--no-summary', str(path)],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except FileNotFoundError:
            return ScanResult('error', '未找到 clamdscan，请先安装 ClamAV。')
        except subprocess.TimeoutExpired:
            return ScanResult('error', 'ClamAV 扫描超时。')

        if result.returncode == 0:
            return ScanResult('clean', result.stdout.strip())
        if result.returncode == 1:
            return ScanResult(
                'infected',
                result.stdout.strip() or result.stderr.strip(),
            )
        return ScanResult('error', result.stderr.strip() or result.stdout.strip())


def scan_product(product, scanner=None):
    """扫描 Product 文件并更新扫描状态。"""
    if not product.file:
        result = ScanResult('error', '作品没有文件。')
    else:
        result = (scanner or ClamAVScanner()).scan(product.file.path)
    product.scan_status = result.status
    product.scanned_at = timezone.now()
    product.save(update_fields=['scan_status', 'scanned_at'])
    return result

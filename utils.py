"""
公共工具模块
提供所有解码器共用的文件读取、ZIP 处理基类等功能
"""

__version__ = "1.0.0"

import os
import shutil
import subprocess
import base64
import zipfile
import io
from abc import ABC, abstractmethod


# 隐藏 PowerShell 窗口
STARTUPINFO = subprocess.STARTUPINFO()
STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
STARTUPINFO.wShowWindow = subprocess.SW_HIDE


def read_file_with_powershell(file_path: str) -> bytes:
    """使用 PowerShell ReadAllBytes 读取文件（绕过 DLP/EFS 加密）"""
    ps_path = file_path.replace('\\', '/')
    cmd = f'''
$bytes = [System.IO.File]::ReadAllBytes("{ps_path}")
[System.Convert]::ToBase64String($bytes)
'''
    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', cmd],
        capture_output=True,
        encoding='utf-8',
        startupinfo=STARTUPINFO
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell 读取失败")
    return base64.b64decode(result.stdout.strip())


class BaseDecoder(ABC):
    """ZIP 文件解密器基类 — 所有 ZIP 格式的公共抽象"""

    SUPPORTED_EXTENSIONS = []
    WORK_DIR = "Decode"

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        if not cls.SUPPORTED_EXTENSIONS:
            return False
        ext = os.path.splitext(file_path)[1].lower()
        return ext in cls.SUPPORTED_EXTENSIONS

    def _get_work_dir(self, input_path: str) -> str:
        input_dir = os.path.dirname(os.path.abspath(input_path))
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(input_dir, self.WORK_DIR, base_name)

    def _prepare_work_dir(self, input_path: str) -> str:
        work_dir = self._get_work_dir(input_path)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir, exist_ok=True)
        return work_dir

    def _generate_output_path(self, input_path: str, suffix: str = "_decode") -> str:
        dir_name = os.path.dirname(input_path)
        base, ext = os.path.splitext(os.path.basename(input_path))
        if base.endswith(suffix):
            return input_path
        return os.path.join(dir_name, f"{base}{suffix}{ext}")

    def _ensure_unique_path(self, path: str) -> str:
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        counter = 1
        while os.path.exists(path):
            path = f"{base}_{counter}{ext}"
            counter += 1
        return path

    def _process_content(self, extracted_dir: str):
        """处理解压后的内容，子类可重写"""
        pass

    def _read_bytes(self, input_path: str) -> bytes:
        """尝试直接读取加密文件，失败则用 PowerShell 绕过"""
        try:
            with open(input_path, 'rb') as f:
                zip_bytes = f.read()
            zipfile.ZipFile(io.BytesIO(zip_bytes), 'r')
            return zip_bytes
        except (zipfile.BadZipFile, OSError):
            return read_file_with_powershell(input_path)

    def _extract_and_repack(self, input_path: str, output_path: str) -> str:
        """公共解密流程：读取 → 解压 → 处理 → 重打包"""
        work_dir = self._prepare_work_dir(input_path)
        zip_bytes = self._read_bytes(input_path)

        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            zf.extractall(work_dir)

        self._process_content(work_dir)

        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(work_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    arc_name = os.path.relpath(abs_path, work_dir).replace("\\", "/")
                    zf.write(abs_path, arc_name)

        return output_path

    @abstractmethod
    def decrypt(self, input_path: str, output_path: str = None) -> str:
        pass

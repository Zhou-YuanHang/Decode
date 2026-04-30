"""
Simulink Data Dictionary (.sldd) 解密器
原理：SLDD 本质是 ZIP，解密过程 = 读取字节 → 解压 → 重新打包
使用 PowerShell ReadAllBytes 绕过加密读取，io.BytesIO 内存处理
"""

import os
import shutil
import zipfile
import io
import subprocess
import base64


# 隐藏 PowerShell 窗口
STARTUPINFO = subprocess.STARTUPINFO()
STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
STARTUPINFO.wShowWindow = subprocess.SW_HIDE


def _read_file_with_powershell(file_path: str) -> bytes:
    """使用 PowerShell ReadAllBytes 读取文件（绕过加密）"""
    cmd = f'''
$bytes = [System.IO.File]::ReadAllBytes("{file_path}")
[System.Convert]::ToBase64String($bytes)
'''
    result = subprocess.run(
        ['powershell', '-Command', cmd],
        capture_output=True,
        encoding='utf-8',
        startupinfo=STARTUPINFO
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "PowerShell 读取失败")
    return base64.b64decode(result.stdout.strip())


class SLDDDecoder:
    """Simulink Data Dictionary 解密器"""

    SUPPORTED_EXTENSIONS = ['.sldd']
    WORK_DIR = "Decode"

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in cls.SUPPORTED_EXTENSIONS

    def decrypt(self, input_path: str, output_path: str = None) -> str:
        """
        解密 SLDD 文件

        流程：
        1. 尝试直接读取，失败则用 PowerShell 读取
        2. 解压到 Decode/<文件名>/ 目录
        3. 重新打包为 xxx_decode.sldd（与原文件同级）
        """
        if output_path is None:
            output_path = self._generate_output_path(input_path)
        output_path = self._ensure_unique_path(output_path)

        work_dir = self._prepare_work_dir(input_path)

        try:
            # Step 1: 读取文件字节
            try:
                # 先尝试直接读取（未加密文件）
                with open(input_path, 'rb') as f:
                    zip_bytes = f.read()
                # 验证是否是有效 ZIP
                zipfile.ZipFile(io.BytesIO(zip_bytes), 'r')
            except (zipfile.BadZipFile, OSError):
                # 文件可能是加密的，用 PowerShell 读取
                zip_bytes = _read_file_with_powershell(input_path)

            # Step 2: 解压到工作目录
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
                zf.extractall(work_dir)

            # Step 3: 处理内部内容（预留接口）
            self._process_content(work_dir)

            # Step 4: 重新打包到输出路径
            with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(work_dir):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        arc_name = os.path.relpath(abs_path, work_dir).replace("\\", "/")
                        zf.write(abs_path, arc_name)

            return output_path

        except Exception as e:
            raise e

    def _process_content(self, extracted_dir: str):
        """处理解压后的内容，预留接口"""
        pass

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


# 全局单例
sldd_decoder = SLDDDecoder()


def decrypt_sldd(input_path: str, output_path: str = None) -> str:
    """
    解密 SLDD 文件的便捷函数

    Args:
        input_path: 输入的 .sldd 文件路径
        output_path: 输出路径，默认为 input_decode.sldd

    Returns:
        输出文件路径
    """
    return sldd_decoder.decrypt(input_path, output_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python sldd_decoder.py <file.sldd>")
        sys.exit(1)
    result = decrypt_sldd(sys.argv[1])
    print(f"解密完成: {result}")

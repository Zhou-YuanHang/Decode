"""
C/C++ 源码文件 (.c, .h) 解密器
原理：使用 PowerShell ReadAllBytes 读取加密文件
输出：
  1. Decode/<文件名>/ 子文件夹 - 存放解密后的文件
  2. 同目录的 xxx_decode.c / xxx_decode.h - 入口文件的解密副本
"""

import os
import subprocess
import shutil
import base64


# 隐藏 PowerShell 窗口
STARTUPINFO = subprocess.STARTUPINFO()
STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
STARTUPINFO.wShowWindow = subprocess.SW_HIDE


def _read_file_with_powershell(file_path: str) -> bytes:
    """使用 PowerShell 读取文件字节流（绕过 EFS 加密）"""
    ps_path = file_path.replace('\\', '/')
    cmd = f'[System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes("{ps_path}"))'
    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', cmd],
        capture_output=True,
        encoding='utf-8',
        startupinfo=STARTUPINFO
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell 读取失败")
    return base64.b64decode(result.stdout.strip())


def _ensure_unique_path(output_path: str) -> str:
    """确保输出路径唯一，不覆盖已存在文件"""
    if not os.path.exists(output_path):
        return output_path
    base, ext = os.path.splitext(output_path)
    counter = 1
    while os.path.exists(output_path):
        output_path = f"{base}_{counter}{ext}"
        counter += 1
    return output_path


def decrypt_c(input_path: str, output_path: str = None) -> list:
    """
    解密 C/C++ 源码文件 (.c 或 .h)
    C 和 H 独立解密，互不影响

    输出：
      1. Decode/<文件名>/ 子文件夹 - 存放解密后的文件
      2. 同目录的 xxx_decode.c（或 xxx_decode.h） - 入口文件的解密副本

    Args:
        input_path: 输入文件路径 (.c 或 .h)

    Returns:
        解密成功的文件路径列表
    """
    ext = os.path.splitext(input_path)[1].lower()
    input_dir = os.path.dirname(os.path.abspath(input_path))
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    # 工作目录：Decode/<文件名>/
    work_dir = os.path.join(input_dir, "Decode", base_name)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    output_files = []

    # C 和 H 独立解密，不再批量
    entry_name = os.path.basename(input_path)
    dest_path = os.path.join(work_dir, entry_name)
    file_bytes = _read_file_with_powershell(input_path)

    with open(dest_path, 'wb') as fp:
        fp.write(file_bytes)
    output_files.append(dest_path)

    # 同目录入口文件加 _decode 后缀
    entry_decode = os.path.join(input_dir, entry_name.replace(ext, f"_decode{ext}"))
    entry_decode = _ensure_unique_path(entry_decode)
    shutil.copyfile(dest_path, entry_decode)
    output_files.append(entry_decode)

    return output_files


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python source_decoder.py <path_to_file.c 或 .h>")
        print("示例: python source_decoder.py main.c")
        sys.exit(1)

    c_file = sys.argv[1]
    results = decrypt_c(c_file)
    for result in results:
        print(f"[OK] 解密完成: {result}")

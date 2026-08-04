"""
Python .py 文件解密器
原理：使用 PowerShell ReadAllBytes 读取加密文件
输出：
  1. Decode/<文件名>/ 子文件夹 - 存放解密后的文件
  2. 同目录的 xxx_decode.py - 入口文件的解密副本
"""

import os
import shutil

from utils import read_file_with_powershell


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


def decrypt_py(input_path: str, output_path: str = None) -> list:
    """
    解密 Python .py 文件

    输出：
      1. Decode/<文件名>/ 子文件夹 - 存放解密后的文件
      2. 同目录的 xxx_decode.py - 入口文件的解密副本

    Args:
        input_path: 输入文件路径 (.py)

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

    # PowerShell 读取解密
    entry_name = os.path.basename(input_path)
    dest_path = os.path.join(work_dir, entry_name)
    file_bytes = read_file_with_powershell(input_path)

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
        print("用法: python py_decoder.py <path_to_file.py>")
        print("示例: python py_decoder.py script.py")
        sys.exit(1)

    py_file = sys.argv[1]
    results = decrypt_py(py_file)
    for result in results:
        print(f"[OK] 解密完成: {result}")

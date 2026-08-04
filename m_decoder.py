"""
MATLAB .m 文件解密器
原理：使用 PowerShell ReadAllBytes 读取并解密 → 写入输出文件
"""

import os
import shutil

from utils import read_file_with_powershell


def decrypt_m(input_path: str, output_path: str = None) -> str:
    """
    解密 MATLAB .m 文件

    流程：
    1. 使用 PowerShell ReadAllBytes 读取并解密文件内容
    2. 写入输出文件

    Args:
        input_path: 输入 .m 文件路径
        output_path: 输出文件路径，为 None 则自动生成

    Returns:
        输出文件的实际路径
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        if base.endswith("_decode"):
            output_path = input_path
        else:
            output_path = f"{base}_decode{ext}"

    # 确保路径唯一
    counter = 1
    original_output = output_path
    while os.path.exists(output_path):
        base, ext = os.path.splitext(original_output)
        output_path = f"{base}_{counter}{ext}"
        counter += 1

    # 工作目录：Decode/<文件名>/
    input_dir = os.path.dirname(os.path.abspath(input_path))
    work_dir = os.path.join(input_dir, "Decode", os.path.splitext(os.path.basename(input_path))[0])
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    try:
        decrypted_bytes = read_file_with_powershell(input_path)

        with open(output_path, 'wb') as f:
            f.write(decrypted_bytes)

        return output_path

    except Exception as e:
        raise e


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python m_decoder.py <path_to_file.m>")
        print("示例: python m_decoder.py script.m")
        sys.exit(1)

    m_file = sys.argv[1]
    result = decrypt_m(m_file)
    print(f"[OK] 解密完成: {result}")

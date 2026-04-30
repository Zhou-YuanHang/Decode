"""
C/C++ 源码文件 (.c, .h) 解密器
原理：使用 PowerShell ReadAllBytes 读取加密文件，直接写入输出文件
批量解密：解密 .c 时自动解密同目录下的所有 .c 和 .h 文件
"""

import os
import subprocess


# 隐藏 PowerShell 窗口
STARTUPINFO = subprocess.STARTUPINFO()
STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
STARTUPINFO.wShowWindow = subprocess.SW_HIDE


def _decrypt_single_file(file_path: str) -> str:
    """解密单个文件，返回输出路径"""
    base, ext = os.path.splitext(file_path)
    output_path = f"{base}_decode{ext}"

    # 确保路径唯一
    counter = 1
    original_output = output_path
    while os.path.exists(output_path):
        base, ext = os.path.splitext(original_output)
        output_path = f"{base}_{counter}{ext}"
        counter += 1

    # 将路径转换为正斜杠（避免 PowerShell 转义问题）
    input_path_ps = file_path.replace('\\', '/')
    output_path_ps = output_path.replace('\\', '/')

    # PowerShell 脚本：直接复制字节流
    ps_script = f'''
$bytes = [System.IO.File]::ReadAllBytes("{input_path_ps}")
[System.IO.File]::WriteAllBytes("{output_path_ps}", $bytes)
'''

    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps_script],
        capture_output=True,
        encoding='utf-8',
        startupinfo=STARTUPINFO
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "PowerShell 执行失败")

    return output_path


def decrypt_c(input_path: str, output_path: str = None) -> list:
    """
    解密 C/C++ 源码文件 (.c, .h)
    如果输入是 .c 文件，会解密同目录下所有的 .c 和 .h 文件

    Args:
        input_path: 输入文件路径 (.c 或 .h)
        output_path: 输出文件路径（仅对单文件生效，批量解密时忽略）

    Returns:
        解密成功的文件路径列表
    """
    ext = os.path.splitext(input_path)[1].lower()
    output_files = []

    if ext == '.c':
        # 获取同目录下的所有 .c 和 .h 文件
        input_dir = os.path.dirname(os.path.abspath(input_path))
        all_files = os.listdir(input_dir)
        c_h_files = [f for f in all_files if f.endswith('.c') or f.endswith('.h')]

        # 解密所有 .c 和 .h 文件
        for f in c_h_files:
            file_path = os.path.join(input_dir, f)
            if os.path.isfile(file_path):
                output_files.append(_decrypt_single_file(file_path))

    elif ext == '.h':
        output_files.append(_decrypt_single_file(input_path))

    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    return output_files


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python c_decoder.py <path_to_file.c>")
        print("示例: python c_decoder.py main.c")
        sys.exit(1)

    c_file = sys.argv[1]
    results = decrypt_c(c_file)
    for result in results:
        print(f"[OK] 解密完成: {result}")

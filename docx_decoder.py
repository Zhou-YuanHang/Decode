"""
Word DOCX 文件解密器
原理：DOCX 本质是 ZIP，解密过程 = 读取字节 → 解压 → 重新打包
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


def decrypt_docx(input_path: str, output_path: str = None) -> str:
    """
    解密 DOCX 文件

    Args:
        input_path: 输入 DOCX 文件路径
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

    # 工作目录：放在输入文件同级目录下
    input_dir = os.path.dirname(os.path.abspath(input_path))
    work_dir = os.path.join(input_dir, "Decode", os.path.splitext(os.path.basename(input_path))[0])
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)

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
        _process_content(work_dir)

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


def _process_content(extracted_dir: str):
    """处理解压后的内容，预留接口"""
    pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python docx_decoder.py <path_to_file.docx>")
        print("示例: python docx_decoder.py document.docx")
        sys.exit(1)

    docx_file = sys.argv[1]
    result = decrypt_docx(docx_file)
    print(f"[OK] 解密完成: {result}")

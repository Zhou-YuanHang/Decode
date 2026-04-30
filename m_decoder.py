"""
MATLAB .m 文件解密器
原理：读取文件字节流 → 使用 PowerShell 解密 → 写入输出文件
使用 PowerShell ReadAllBytes 绕过文件加密/占用
"""

import os
import shutil
import subprocess
import base64


# 隐藏 PowerShell 窗口
STARTUPINFO = subprocess.STARTUPINFO()
STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
STARTUPINFO.wShowWindow = subprocess.SW_HIDE


def _read_file_with_powershell(file_path: str) -> bytes:
    """使用 PowerShell ReadAllBytes 读取文件（绕过加密/占用）"""
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


def _read_file_bytes(file_path: str) -> bytes:
    """读取文件字节流，优先直接读取，失败则用 PowerShell"""
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception:
        # 直接读取失败，使用 PowerShell 绕过
        return _read_file_with_powershell(file_path)


def decrypt_m(input_path: str, output_path: str = None) -> str:
    """
    解密 MATLAB .m 文件
    
    流程：
    1. 读取文件字节流（直接读取或 PowerShell 绕过）
    2. 使用 PowerShell 解密内容
    3. 写入输出文件
    
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
        # Step 1: 读取文件字节流
        file_bytes = _read_file_bytes(input_path)
        
        # Step 2: 使用 PowerShell 解密（关键步骤！）
        decrypted_bytes = _read_file_with_powershell(input_path)
        
        # Step 3: 写入输出文件
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

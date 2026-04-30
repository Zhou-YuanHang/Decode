#!/usr/bin/env python3
"""
SLDD Decoder - Simulink Data Dictionary 解密器
解密方法：使用 PowerShell 读取加密文件字节流，然后复制字节流到新文件
参考：m_decoder.py
"""

import os
import sys
import subprocess
import base64
from pathlib import Path


def _read_file_with_powershell(file_path: str) -> bytes:
    """
    使用 PowerShell 的 ReadAllBytes 方法读取文件字节流
    这个方法可以绕过文件加密导致的权限/占用问题
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件的原始字节流
    """
    # PowerShell 脚本：读取文件字节并转换为 base64
    ps_script = f'''
    $bytes = [System.IO.File]::ReadAllBytes("{file_path}")
    [System.Convert]::ToBase64String($bytes)
    '''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"PowerShell 执行失败: {result.stderr}")
        
        # 将 base64 转回字节流
        file_bytes = base64.b64decode(result.stdout.strip())
        return file_bytes
        
    except Exception as e:
        print(f"❌ 无法读取文件 {file_path}: {e}")
        return None


def _read_file_bytes(file_path: str) -> bytes:
    """
    读取文件字节流（优先使用 Python，失败则使用 PowerShell）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件的原始字节流
    """
    # 方法1：尝试使用 Python 直接读取
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Python 读取失败，尝试 PowerShell: {e}")
    
    # 方法2：使用 PowerShell 读取（绕过加密）
    return _read_file_with_powershell(file_path)


def decrypt_sldd(input_path: str, output_path: str = None) -> str:
    """
    解密 SLDD 文件（Simulink Data Dictionary）
    
    解密原理：
    1. 使用 PowerShell ReadAllBytes 读取加密的 .sldd 文件
    2. 将字节流直接复制到新文件（不做任何解码/解压）
    3. 解密后的文件仍保持加密状态，但可以被无解密软件的电脑上的 MATLAB 打开
    
    Args:
        input_path: 输入的 .sldd 文件路径
        output_path: 输出的解密文件路径（可选，默认为原文件名加 _decode）
        
    Returns:
        解密后的文件路径，如果失败则返回 None
    """
    # 检查输入文件
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        return None
    
    # 检查文件扩展名
    if not input_path.lower().endswith('.sldd'):
        print(f"❌ 文件扩展名不是 .sldd: {input_path}")
        return None
    
    # 生成输出文件路径
    if output_path is None:
        output_path = input_path.replace('.sldd', '_decode.sldd')
    
    print(f"🔓 开始解密 SLDD 文件...")
    print(f"   输入: {input_path}")
    print(f"   输出: {output_path}")
    
    # 读取文件字节流
    file_bytes = _read_file_bytes(input_path)
    
    if file_bytes is None:
        print(f"❌ 无法读取文件: {input_path}")
        return None
    
    print(f"   文件大小: {len(file_bytes)} 字节")
    
    # 写入解密后的文件（纯字节流复制）
    try:
        with open(output_path, 'wb') as f:
            f.write(file_bytes)
        
        print(f"✅ 解密完成: {output_path}")
        print(f"   提示: 解密后的文件仍保持加密状态")
        print(f"   可以使用 MATLAB 打开（无需解密软件）")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")
        return None


def batch_decrypt_sldd(file_list: list) -> dict:
    """
    批量解密 SLDD 文件
    
    Args:
        file_list: 文件路径列表
        
    Returns:
        结果字典：{文件路径: 成功/失败}
    """
    results = {}
    
    print(f"\n{'='*60}")
    print(f"批量解密 SLDD 文件")
    print(f"共 {len(file_list)} 个文件")
    print(f"{'='*60}\n")
    
    success_count = 0
    
    for i, file_path in enumerate(file_list, 1):
        print(f"\n[{i}/{len(file_list)}] 处理: {file_path}")
        
        result = decrypt_sldd(file_path)
        
        if result:
            results[file_path] = "成功"
            success_count += 1
        else:
            results[file_path] = "失败"
    
    print(f"\n{'='*60}")
    print(f"批量解密完成")
    print(f"成功: {success_count}/{len(file_list)}")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    # 测试代码
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # 默认使用测试文件
        input_file = "PublicParameters.sldd"
    
    if not os.path.exists(input_file):
        print(f"❌ 找不到测试文件: {input_file}")
        print(f"\n使用方法:")
        print(f"  python sldd_decoder.py [sldd文件路径]")
        sys.exit(1)
    
    decrypt_sldd(input_file)

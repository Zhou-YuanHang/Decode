"""
公共工具模块
提供所有解码器共用的文件读取等功能
"""

import subprocess
import base64


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

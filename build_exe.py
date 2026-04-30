"""
打包脚本 - 将文件解密工具打包为exe
使用 PyInstaller 打包
"""

import os
import sys
import subprocess


def main():
    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])

    # 获取项目根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "Pic.jpg")

    if not os.path.exists(icon_path):
        print(f"[错误] 图标文件不存在: {icon_path}")
        print("请确保 Pic.jpg 位于项目根目录")
        return

    # 获取 tkinterdnd2 的 tkdnd 库路径
    import tkinterdnd2
    tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), "tkdnd")
    
    if not os.path.exists(tkdnd_path):
        print(f"[警告] tkdnd 库路径不存在: {tkdnd_path}")
        print("拖放功能可能无法正常工作")
    
    # PyInstaller 参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",              # 单文件模式
        "--windowed",             # 无控制台窗口
        "--name", "文件解密工具",  # 输出文件名
        "--icon", icon_path,      # 图标文件
        "--add-data", f"Pic.jpg;.",  # 打包图标文件到exe
        "--add-data", f"{tkdnd_path};tkinterdnd2/tkdnd",  # 打包 tkdnd 库文件
        "--hidden-import", "slx_decoder",      # 显式包含解码器模块
        "--hidden-import", "xlsx_decoder",
        "--hidden-import", "docx_decoder",
        "--hidden-import", "m_decoder",
        "--clean",                # 清理临时文件
        "decoder_gui.py"
    ]

    print("开始打包...")
    print(f"命令: {' '.join(cmd)}")
    print()

    try:
        subprocess.check_call(cmd)
        print()
        print("=" * 50)
        print("打包成功！")
        print(f"输出目录: {os.path.join(base_dir, 'dist')}")
        print(f"可执行文件: {os.path.join(base_dir, 'dist', '文件解密工具.exe')}")
        print("=" * 50)
    except subprocess.CalledProcessError as e:
        print(f"[错误] 打包失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

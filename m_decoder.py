"""
MATLAB .m 文件解密器
原理：.m 文件是纯文本，"解密" = 去除 BOM、规范化编码
"""

import os
import codecs
import shutil


def decrypt_m(input_path: str, output_path: str = None) -> str:
    """
    解密 MATLAB .m 文件

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

    # 工作目录：Decode/<文件名>/（放在输入文件同级目录下，避免打包后路径问题）
    input_dir = os.path.dirname(os.path.abspath(input_path))
    work_dir = os.path.join(input_dir, "Decode", os.path.splitext(os.path.basename(input_path))[0])
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    # 尝试多种编码读取
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin-1']
    content = None

    for enc in encodings:
        try:
            with codecs.open(input_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        # 如果都失败，用二进制读取然后忽略错误
        with open(input_path, 'rb') as f:
            raw = f.read()
            # 尝试去除 BOM
            if raw.startswith(codecs.BOM_UTF8):
                raw = raw[len(codecs.BOM_UTF8):]
            content = raw.decode('utf-8', errors='ignore')

    # 处理内容（预留接口）
    content = _process_content(content)

    # 写入解密后的文件（UTF-8 无 BOM）
    with codecs.open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path


def _process_content(content: str) -> str:
    """
    处理 .m 文件内容
    预留接口，可实现：
    - 去除注释
    - 格式化代码
    - 提取函数定义
    """
    # TODO: 实现具体的 .m 文件处理逻辑
    return content


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python m_decoder.py <path_to_file.m>")
        print("示例: python m_decoder.py script.m")
        sys.exit(1)

    m_file = sys.argv[1]
    result = decrypt_m(m_file)
    print(f"[OK] 解密完成: {result}")

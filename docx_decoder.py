"""
Word DOCX 文件解密器
原理：DOCX 本质是 ZIP，解密过程 = 读取字节 → 解压 → 重新打包
使用 PowerShell ReadAllBytes 绕过加密读取，io.BytesIO 内存处理
"""

from utils import BaseDecoder


class DOCXDecoder(BaseDecoder):
    """Word DOCX 文件解密器"""

    SUPPORTED_EXTENSIONS = ['.docx']

    def decrypt(self, input_path: str, output_path: str = None) -> str:
        if output_path is None:
            output_path = self._generate_output_path(input_path)
        output_path = self._ensure_unique_path(output_path)
        return self._extract_and_repack(input_path, output_path)


# 全局单例
docx_decoder = DOCXDecoder()


def decrypt_docx(input_path: str, output_path: str = None) -> str:
    """
    解密 DOCX 文件的便捷函数

    Args:
        input_path: 输入的 .docx 文件路径
        output_path: 输出路径，默认为 input_decode.docx

    Returns:
        输出文件路径
    """
    return docx_decoder.decrypt(input_path, output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python docx_decoder.py <path_to_file.docx>")
        print("示例: python docx_decoder.py document.docx")
        sys.exit(1)

    docx_file = sys.argv[1]
    result = decrypt_docx(docx_file)
    print(f"[OK] 解密完成: {result}")

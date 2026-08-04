"""
XLSX 文件解密器
原理：XLSX 本质是 ZIP，解密过程 = 读取字节 → 解压 → 重新打包
使用 PowerShell ReadAllBytes 绕过加密读取，io.BytesIO 内存处理
"""

from utils import BaseDecoder


class XLSXDecoder(BaseDecoder):
    """XLSX 表格文件解密器"""

    SUPPORTED_EXTENSIONS = ['.xlsx']

    def decrypt(self, input_path: str, output_path: str = None) -> str:
        if output_path is None:
            output_path = self._generate_output_path(input_path)
        output_path = self._ensure_unique_path(output_path)
        return self._extract_and_repack(input_path, output_path)


# 全局单例
xlsx_decoder = XLSXDecoder()


def decrypt_xlsx(input_path: str, output_path: str = None) -> str:
    """
    解密 XLSX 文件的便捷函数

    Args:
        input_path: 输入的 .xlsx 文件路径
        output_path: 输出路径，默认为 input_decode.xlsx

    Returns:
        输出文件路径
    """
    return xlsx_decoder.decrypt(input_path, output_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python xlsx_decoder.py <file.xlsx>")
        sys.exit(1)
    result = decrypt_xlsx(sys.argv[1])
    print(f"解密完成: {result}")

"""
SLX 文件解密器
原理：SLX 本质是 ZIP，解密过程 = 读取字节 → 解压 → 重新打包
使用 PowerShell ReadAllBytes 绕过加密读取，io.BytesIO 内存处理
"""

from utils import BaseDecoder


class SLXDecoder(BaseDecoder):
    """SLX 模型文件解密器"""

    SUPPORTED_EXTENSIONS = ['.slx']

    def decrypt(self, input_path: str, output_path: str = None) -> str:
        if output_path is None:
            output_path = self._generate_output_path(input_path)
        output_path = self._ensure_unique_path(output_path)
        return self._extract_and_repack(input_path, output_path)


# 全局单例
slx_decoder = SLXDecoder()


def decrypt_slx(input_path: str, output_path: str = None) -> str:
    """
    解密 SLX 文件的便捷函数

    Args:
        input_path: 输入的 .slx 文件路径
        output_path: 输出路径，默认为 input_decode.slx

    Returns:
        输出文件路径
    """
    return slx_decoder.decrypt(input_path, output_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python slx_decoder.py <file.slx>")
        sys.exit(1)
    result = decrypt_slx(sys.argv[1])
    print(f"解密完成: {result}")

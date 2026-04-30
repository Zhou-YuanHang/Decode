"""
SLX 文件解密器
原理：SLX 本质是 ZIP，解密过程 = 解压 → 处理内部内容 → 重新打包
"""

import zipfile
import os
import shutil
from abc import ABC, abstractmethod


class BaseDecoder(ABC):
    """文件解密器基类"""

    SUPPORTED_EXTENSIONS = []
    WORK_DIR = "Decode"

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        if not cls.SUPPORTED_EXTENSIONS:
            return False
        ext = os.path.splitext(file_path)[1].lower()
        return ext in cls.SUPPORTED_EXTENSIONS

    @abstractmethod
    def decrypt(self, input_path: str, output_path: str = None) -> str:
        pass

    def _get_work_dir(self, input_path: str) -> str:
        # 获取工作目录：优先使用输入文件所在目录，避免打包后路径问题
        input_dir = os.path.dirname(os.path.abspath(input_path))
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        return os.path.join(input_dir, self.WORK_DIR, base_name)

    def _prepare_work_dir(self, input_path: str) -> str:
        work_dir = self._get_work_dir(input_path)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir, exist_ok=True)
        return work_dir

    def _generate_output_path(self, input_path: str, suffix: str = "_decode") -> str:
        dir_name = os.path.dirname(input_path)
        base, ext = os.path.splitext(os.path.basename(input_path))
        if base.endswith(suffix):
            return input_path
        return os.path.join(dir_name, f"{base}{suffix}{ext}")

    def _ensure_unique_path(self, path: str) -> str:
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        counter = 1
        while os.path.exists(path):
            path = f"{base}_{counter}{ext}"
            counter += 1
        return path


class SLXDecoder(BaseDecoder):
    """SLX 模型文件解密器"""

    SUPPORTED_EXTENSIONS = ['.slx']

    def decrypt(self, input_path: str, output_path: str = None) -> str:
        if output_path is None:
            output_path = self._generate_output_path(input_path)
        output_path = self._ensure_unique_path(output_path)

        work_dir = self._prepare_work_dir(input_path)

        try:
            with zipfile.ZipFile(input_path, 'r') as zf:
                zf.extractall(work_dir)

            self._process_content(work_dir)

            with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(work_dir):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        arc_name = os.path.relpath(abs_path, work_dir).replace("\\", "/")
                        zf.write(abs_path, arc_name)

            return output_path

        except Exception as e:
            raise e

    def _process_content(self, extracted_dir: str):
        """处理解压后的内容，预留接口"""
        pass


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

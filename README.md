# 文件解密工具 v1.5

一款通用的文件解密工具，支持拖放操作，可批量处理多种格式文件。

## 功能特性

- **拖放支持**：直接拖入文件或文件夹进行解密
- **多格式支持**：目前支持 .slx、.xlsx、.docx、.m 格式
- **类型筛选**：通过复选框选择要解密的文件类型
- **递归扫描**：可选是否包含子文件夹
- **批量处理**：一键解密所有符合条件的文件
- **单文件解密**：仅解密指定的单个文件
- **实时刷新**：扫描后新增文件可刷新重新统计
- **删除源文件**：解密完成后一键删除已解密的源文件（带确认对话框）

## 使用方法

### 方式一：直接运行 Python 脚本

```bash
python decoder_gui.py
```

### 方式二：使用打包后的 exe 文件

运行 `build_exe.py` 打包后，在 `dist/` 目录下会生成 `文件解密工具.exe`，双击即可运行。

```bash
python build_exe.py
```

### 拖入文件

1. **拖入文件夹**：解密该文件夹下的所有支持文件
2. **拖入单个文件**：可选择解密该文件或整个文件夹

### 选择选项

- **文件类型**：勾选要解密的文件扩展名（全部、.slx、.xlsx、.docx、.m）
- **包含子文件夹**：勾选则递归扫描所有子目录

### 执行解密

- **解密所有文件**：解密筛选后的全部文件
- **解密单个文件**：仅解密拖入的那个文件
- **刷新**：重新扫描文件夹，更新文件列表
- **打开位置**：打开文件所在文件夹
- **删除源文件**：删除已解密文件对应的源文件（谨慎使用）

## 解密原理

本工具针对基于 ZIP 格式的文件（如 .slx、.xlsx、.docx）进行解密：

1. **读取文件**：优先使用 Python `open()` 读取，失败则调用 PowerShell `[System.IO.File]::ReadAllBytes()` 绕过加密
2. **解压内容**：使用 `zipfile` + `io.BytesIO` 在内存中解压到工作目录 `Decode/<文件名>/`
3. **重新打包**：将解压后的内容重新压缩为 `<原文件名>_decode.<扩展名>`

解密后的文件与原文件位于同一目录。

**技术亮点**：通过 PowerShell 读取加密文件字节，解决 PyInstaller 打包后无法直接访问加密文件的问题。

## 扩展新格式

要支持新的文件格式，只需：

1. 复制 `slx_decoder.py` 为 `xxx_decoder.py`
2. 修改文件中的扩展名和函数名
3. 在 `decoder_gui.py` 的 `decoder_map` 中添加映射

## 文件结构

```
YS_Decode/
├── Decode/              # 解密工作目录（运行时生成）
├── slx_decoder.py       # SLX 解密器
├── xlsx_decoder.py      # XLSX 解密器
├── docx_decoder.py      # DOCX 解密器
├── m_decoder.py         # MATLAB .m 解密器
├── decoder_gui.py       # GUI 主程序
├── build_exe.py         # PyInstaller 打包脚本
├── README.md            # 本说明文件
├── CHANGELOG.md         # 版本更新日志
└── requirements.txt     # 依赖列表
```

## 系统要求

- Python 3.7+
- Windows 操作系统（依赖 tkinterdnd2）

## 依赖安装

```bash
pip install -r requirements.txt
```

## 版本信息

- **当前版本**：v1.5
- **发布日期**：2026-04-23

## 更新记录

### v1.5
- 修复打包后 Excel/Word 解密失败的问题
- 使用 PowerShell `ReadAllBytes` 读取加密文件，确保 exe 版本正常工作

### v1.4
- 提供 PyInstaller 打包脚本，可生成独立 exe 文件

### v1.3
- 新增删除源文件功能（带确认对话框）

### v1.2
- 新增 MATLAB .m 脚本格式支持

### v1.1
- 新增 Word .docx 格式支持

### v1.0
- 初始版本，支持 .slx、.xlsx 格式
- 完整的 GUI 界面和拖放功能

## 许可证

MIT License

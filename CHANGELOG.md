# 更新日志

## [v1.9] - 2026-05-08

### 新增

- 新增"去除 _decode 后缀"按钮
  - 解密完成后自动激活
  - 将所有 `xxx_decode.ext` 重命名为 `xxx.ext`
  - 如目标文件已存在，弹窗提示并支持覆盖
  - 重命名完成后自动禁用按钮并刷新文件列表

- 新增"删除 _decode 文件"按钮
  - 无需先解密，直接删除当前文件夹下所有 `_decode` 文件
  - 拖入文件夹时自动扫描并启用按钮
  - 解密完成后自动重新扫描并更新按钮状态
  - 带确认对话框，防止误操作

- 新增"删除 Decode 文件夹"按钮
  - 删除 slx/xlsx/docx/sldd/m 解密过程中产生的 `Decode/<文件名>/` 目录
  - 拖入文件夹时自动扫描所有 Decode 文件夹并启用按钮
  - 支持递归扫描，按钮状态实时更新
  - 带确认对话框，防止误操作

### 修复

- 修复"删除源文件"按钮 Bug
  - 问题原因：之前错误删除的是 `decrypted_files`（解密后文件）而非 `source_files`（源文件）
  - 修复方案：拆分为两个独立列表，分别记录源文件和输出文件
  - 现在正确删除原始加密文件，保留解密后的文件

### 优化

- 调整 UI 按钮布局为两行
  - 第一行：解密所有 / 解密单个 / 刷新 / 打开位置
  - 第二行：删除源文件 / 去除 _decode 后缀 / 删除 _decode 文件 / 删除 Decode 文件夹
  - 窗口高度从 580 调整为 620，确保所有按钮可见

## [v1.8.1] - 2026-05-08

### 修复

- 修复 SLX 文件解密失败问题（"File is not a zip file"）
  - 问题原因：SLX 文件被 EFS 加密时，Python open() 读取到乱码
  - 解决方案：参考 xlsx_decoder.py，使用 PowerShell ReadAllBytes 绕过加密读取
  - 添加 `_read_file_with_powershell()` 函数，使用 base64 中转读取加密文件
  - 修改 SLXDecoder.decrypt() 方法，先尝试直接读取，失败则用 PowerShell

## [v1.8] - 2026-04-30

### 新增

- 新增 C/C++ 源码（.c/.h）解密器 `source_decoder.py`
  - 使用 PowerShell `ReadAllBytes` 绕过加密读取
  - 解密 .c 时自动解密同目录下所有的 .c 和 .h 文件
  - 直接复制字节流，不做编码转换

- 重新实现 Simulink 数据字典（.sldd）解密器 `sldd_decoder.py`
  - 原理：SLDD 本质是 ZIP 格式，解压 → 重新打包
  - 支持 PowerShell `ReadAllBytes` 绕过加密读取
  - 与 xlsx_decoder.py、docx_decoder.py 共用相同模式

## [v1.7] - 2026-04-30

### 新增

- 新增 Simulink 数据字典（.sldd）格式支持（初始版本，后被修正）

## [v1.6] - 2026-04-30

### 修复

- 修复打包后 exe 运行时报错 "Unable to load tkdnd library"
  - 修改 `build_exe.py`，添加 `--add-data` 参数包含 tkdnd 库文件
  - 路径：`C:\Users\ZYH\AppData\Local\Programs\Python\Python38\Lib\site-packages\tkinterdnd2\tkdnd`

- 修复 .m 文件解密后乱码问题
  - 根本原因：MATLAB .m 文件是加密的，只有 MATLAB/VS Code 能正确解码
  - 之前的做法（解码为文本 → 重新编码）会破坏原始数据
  - 正确做法：参考 `xlsx_decoder.py` 的思路，直接复制字节流，不做任何文本解码
  - 使用 PowerShell `ReadAllBytes` 绕过文件加密/占用
  - 修改 `m_decoder.py`：删除文本解码逻辑，改为纯字节流复制

### 技术要点

- **加密文件处理**：对于加密的文件（只有特定软件能打开），不应解码为文本，而应直接复制字节流
- **PowerShell ReadAllBytes**：绕过文件加密/占用，读取原始字节流
- **PyInstaller 打包 tkinterdnd2**：需要手动添加 tkdnd 库文件路径

## [v1.5] - 2026-04-23

### 修复

- 彻底修复打包后 Excel/Word 解密失败的问题
  - 参考 AutoConverter 逻辑，使用 PowerShell `[System.IO.File]::ReadAllBytes()` 读取加密文件
  - Python `open()` 失败时自动 fallback 到 PowerShell 读取
  - 使用 `io.BytesIO` 内存处理，无需临时文件

## [v1.4] - 2026-04-22

### 新增

- 提供 PyInstaller 打包脚本 build_exe.py
- 可打包为独立 exe 文件，使用 Pic.jpg 作为图标

## [v1.3] - 2026-04-22

### 新增

- 一键删除已解密文件对应的源文件功能
  - 解密完成后启用删除按钮
  - 带确认对话框，防止误操作
  - 显示删除结果日志

## [v1.2] - 2026-04-22

### 新增

- 支持 MATLAB .m 脚本文件解密

## [v1.1] - 2026-04-22

### 新增

- 支持 Word .docx 格式文件解密

## [v1.0] - 2026-04-22

### 新增

- 支持拖入文件或文件夹进行解密
- 支持 .slx、.xlsx、.docx、.m 格式文件解密
- 文件类型多选筛选功能（全部、.slx、.xlsx、.docx、.m）
- 递归/非递归扫描选项
- 解密所有文件 / 解密单个文件 双模式
- 实时刷新文件列表功能
- 打开文件所在位置功能
- 操作日志实时显示

### 技术特性

- 基于 tkinter 的图形界面
- 支持拖放操作（tkinterdnd2）
- 多线程解密，界面不卡顿
- 模块化设计，易于扩展新格式

## 计划功能

- [ ] 解密进度条显示
- [ ] 配置文件持久化
- [ ] 批量导出解密日志

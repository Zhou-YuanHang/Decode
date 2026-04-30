# 更新日志

## [v1.7] - 2026-04-30

### 新增

- 新增 Simulink 数据字典（.sldd）格式支持
  - 创建 `sldd_decoder.py` 解密器
  - 使用 PowerShell `ReadAllBytes` 读取加密文件
  - 纯字节流复制到新文件，不做解压/解码
  - 解密后的文件仍保持加密状态，可在无解密软件的电脑上用 MATLAB 打开

### 修改

- 更新 `decoder_gui.py`，在 `decoder_map` 中添加 `.sldd` 映射
- 更新 `build_exe.py`，添加 `sldd_decoder` 到 hidden-imports
- 更新 `README.md`，添加 .sldd 格式说明

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

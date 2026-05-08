"""
通用文件解密工具 GUI
支持拖入单个文件或文件夹
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import threading


class DecoderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("文件解密工具")
        self.root.geometry("700x620")
        self.root.minsize(600, 480)

        self.current_path = None
        self.current_folder = None
        self.is_file = False
        self.all_files_in_folder = []  # 文件夹中所有支持的文件
        self.target_files = []  # 根据类型筛选后的文件
        self.source_files = []   # 记录本次成功解密的源文件路径（用于删除源文件）
        self.decrypted_files = []  # 记录本次成功解密的输出文件路径（用于去除后缀）
        self.created_decode_folders = []  # 记录本次解密创建的 Decode 文件夹路径
        self.decode_files = []  # 当前扫描到的所有 _decode 文件
        self.decode_folders = []  # 当前扫描到的所有 Decode 文件夹

        # 扩展名 -> 解密函数映射
        self.decoder_map = {
            '.slx': ('slx_decoder', 'decrypt_slx'),
            '.xlsx': ('xlsx_decoder', 'decrypt_xlsx'),
            '.docx': ('docx_decoder', 'decrypt_docx'),
            '.m': ('m_decoder', 'decrypt_m'),
            '.sldd': ('sldd_decoder', 'decrypt_sldd'),
            '.c': ('source_decoder', 'decrypt_c'),
            '.h': ('source_decoder', 'decrypt_c'),
        }

        self._build_ui()
        self._setup_drag_drop()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)

        # 拖放区域
        self.drop_frame = tk.Frame(main, bg="#e8f4e8", height=100, relief="ridge", bd=2)
        self.drop_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.drop_frame.grid_propagate(False)
        main.rowconfigure(0, weight=0)

        self.drop_label = tk.Label(
            self.drop_frame,
            text="拖放文件或文件夹到这里进行解密",
            bg="#e8f4e8",
            fg="#2e7d32",
            font=("Microsoft YaHei", 14, "bold")
        )
        self.drop_label.place(relx=0.5, rely=0.5, anchor="center")

        # 选项区域（类型选择 + 递归选项）
        options_frame = ttk.LabelFrame(main, text="解密选项", padding="10")
        options_frame.grid(row=1, column=0, sticky="ew", pady=5)
        main.rowconfigure(1, weight=0)

        # 文件类型选择
        type_subframe = ttk.Frame(options_frame)
        type_subframe.pack(fill="x", pady=(0, 5))
        ttk.Label(type_subframe, text="文件类型:").pack(side="left", padx=(0, 10))

        self.type_vars = {}
        self.all_var = tk.IntVar(value=1)
        
        ttk.Checkbutton(
            type_subframe,
            text="全部",
            variable=self.all_var,
            command=self._on_all_changed
        ).pack(side="left", padx=10)

        for ext in sorted(self.decoder_map.keys()):
            var = tk.IntVar(value=1)
            self.type_vars[ext] = var
            ttk.Checkbutton(
                type_subframe,
                text=ext,
                variable=var,
                command=self._on_type_changed
            ).pack(side="left", padx=10)

        # 递归选项
        self.recursive_var = tk.IntVar(value=1)
        ttk.Checkbutton(
            options_frame,
            text="包含子文件夹",
            variable=self.recursive_var,
            command=self._on_recursive_changed
        ).pack(anchor="w", padx=5, pady=(5, 0))

        # 文件信息区域
        info_frame = ttk.LabelFrame(main, text="文件信息", padding="10")
        info_frame.grid(row=2, column=0, sticky="ew", pady=5)
        info_frame.columnconfigure(1, weight=1)
        main.rowconfigure(2, weight=0)

        # 文件夹路径（拖入文件或文件夹都显示）
        ttk.Label(info_frame, text="文件夹:").grid(row=0, column=0, sticky="w")
        self.folder_var = tk.StringVar(value="未选择")
        self.folder_entry = ttk.Entry(info_frame, textvariable=self.folder_var, state="readonly")
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=5)

        # 文件路径（仅拖入文件时显示）
        ttk.Label(info_frame, text="文件:").grid(row=1, column=0, sticky="w", pady=5)
        self.file_var = tk.StringVar(value="-")
        self.file_entry = ttk.Entry(info_frame, textvariable=self.file_var, state="readonly")
        self.file_entry.grid(row=1, column=1, sticky="ew", padx=5)

        # 待解密数量
        ttk.Label(info_frame, text="待解密:").grid(row=2, column=0, sticky="w")
        self.count_var = tk.StringVar(value="-")
        ttk.Label(info_frame, textvariable=self.count_var).grid(row=2, column=1, sticky="w", padx=5)

        # 操作按钮 - 第一行：解密相关
        btn_frame1 = ttk.Frame(main)
        btn_frame1.grid(row=3, column=0, pady=(15, 5))
        main.rowconfigure(3, weight=0)

        self.decrypt_all_btn = ttk.Button(
            btn_frame1,
            text="🔓 解密所有文件",
            command=self._do_decrypt_all,
            state="disabled"
        )
        self.decrypt_all_btn.pack(side="left", padx=10)

        self.decrypt_single_btn = ttk.Button(
            btn_frame1,
            text="🔓 解密单个文件",
            command=self._do_decrypt_single,
            state="disabled"
        )
        self.decrypt_single_btn.pack(side="left", padx=10)

        self.refresh_btn = ttk.Button(
            btn_frame1,
            text="🔄 刷新",
            command=self._refresh_files,
            state="disabled"
        )
        self.refresh_btn.pack(side="left", padx=10)

        self.open_btn = ttk.Button(
            btn_frame1,
            text="📂 打开位置",
            command=self._open_location,
            state="disabled"
        )
        self.open_btn.pack(side="left", padx=10)

        # 操作按钮 - 第二行：清理相关
        btn_frame2 = ttk.Frame(main)
        btn_frame2.grid(row=4, column=0, pady=(0, 10))
        main.rowconfigure(4, weight=0)

        self.delete_src_btn = ttk.Button(
            btn_frame2,
            text="🗑️ 删除源文件",
            command=self._delete_source_files,
            state="disabled"
        )
        self.delete_src_btn.pack(side="left", padx=10)

        self.rename_btn = ttk.Button(
            btn_frame2,
            text="✏️ 去除_decode后缀",
            command=self._rename_remove_decode,
            state="disabled"
        )
        self.rename_btn.pack(side="left", padx=10)

        self.delete_decode_files_btn = ttk.Button(
            btn_frame2,
            text="🗑️ 删除_decode文件",
            command=self._do_delete_all_decode_files,
            state="disabled"
        )
        self.delete_decode_files_btn.pack(side="left", padx=10)

        self.delete_decode_folder_btn = ttk.Button(
            btn_frame2,
            text="📁 删除Decode文件夹",
            command=self._do_delete_decode_folders,
            state="disabled"
        )
        self.delete_decode_folder_btn.pack(side="left", padx=10)

        # 日志区域
        log_frame = ttk.LabelFrame(main, text="操作日志", padding="5")
        log_frame.grid(row=5, column=0, sticky="nsew", pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.grid(row=6, column=0, sticky="ew", pady=(5, 0))
        main.rowconfigure(6, weight=0)

    def _on_all_changed(self):
        """"全部"复选框变化时"""
        all_selected = self.all_var.get()
        for var in self.type_vars.values():
            var.set(1 if all_selected else 0)
        self._update_file_list()

    def _on_type_changed(self):
        """单个类型复选框变化时"""
        all_selected = all(var.get() for var in self.type_vars.values())
        self.all_var.set(1 if all_selected else 0)
        self._update_file_list()

    def _on_recursive_changed(self):
        """递归选项变化时"""
        self._update_file_list()

    def _update_file_list(self):
        """根据选中的类型和递归选项更新文件列表，同时扫描 _decode 文件和 Decode 文件夹"""
        selected_types = {ext for ext, var in self.type_vars.items() if var.get()}
        recursive = self.recursive_var.get()

        # 从当前文件夹中筛选
        if self.current_folder and os.path.isdir(self.current_folder):
            self.all_files_in_folder = []

            if recursive:
                # 递归扫描所有子文件夹
                for root, dirs, files in os.walk(self.current_folder):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in self.decoder_map:
                            self.all_files_in_folder.append(os.path.join(root, file))
            else:
                # 仅扫描当前文件夹（不递归）
                for file in os.listdir(self.current_folder):
                    file_path = os.path.join(self.current_folder, file)
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(file)[1].lower()
                        if ext in self.decoder_map:
                            self.all_files_in_folder.append(file_path)

            self.target_files = [f for f in self.all_files_in_folder
                                if os.path.splitext(f)[1].lower() in selected_types]

            # 扫描 _decode 文件（不限类型）
            self._scan_decode_files_and_folders(recursive)
        else:
            self.target_files = []
            self.decode_files = []
            self.decode_folders = []

        count = len(self.target_files)
        type_names = ', '.join(sorted(selected_types)) if selected_types else '无'
        self.count_var.set(f"{count} 个文件 ({type_names})")

        # 更新按钮状态
        if count > 0:
            self.decrypt_all_btn.config(state="normal")
        else:
            self.decrypt_all_btn.config(state="disabled")

        # 单个文件按钮：只有拖入的是文件且类型支持时才可用
        if self.is_file and self.current_path:
            ext = os.path.splitext(self.current_path)[1].lower()
            if ext in self.decoder_map and ext in selected_types:
                self.decrypt_single_btn.config(state="normal")
            else:
                self.decrypt_single_btn.config(state="disabled")
        else:
            self.decrypt_single_btn.config(state="disabled")

    def _scan_decode_files_and_folders(self, recursive):
        """扫描当前文件夹中的 _decode 文件和 Decode 文件夹"""
        self.decode_files = []
        self.decode_folders = []

        if not self.current_folder or not os.path.isdir(self.current_folder):
            return

        if recursive:
            for root, dirs, files in os.walk(self.current_folder):
                # 扫描 Decode 文件夹
                for d in dirs:
                    if d == "Decode":
                        self.decode_folders.append(os.path.join(root, d))
                # 扫描 _decode 文件
                for f in files:
                    base = os.path.splitext(f)[0]
                    if base.endswith("_decode"):
                        self.decode_files.append(os.path.join(root, f))
        else:
            for item in os.listdir(self.current_folder):
                item_path = os.path.join(self.current_folder, item)
                if os.path.isdir(item_path) and item == "Decode":
                    self.decode_folders.append(item_path)
                elif os.path.isfile(item_path):
                    base = os.path.splitext(item)[0]
                    if base.endswith("_decode"):
                        self.decode_files.append(item_path)

    def _setup_drag_drop(self):
        try:
            self.drop_frame.drop_target_register("DND_Files")
            self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_label.drop_target_register("DND_Files")
            self.drop_label.dnd_bind("<<Drop>>", self._on_drop)
        except Exception as e:
            self._log(f"[WARN] 拖放功能初始化失败: {e}")

    def _on_drop(self, event):
        # 处理拖放数据，支持多文件和带空格的路径
        data = event.data
        
        # Windows 拖放路径处理
        # 路径可能被大括号包裹，多个文件用空格分隔但路径本身可能含空格
        if data.startswith('{') and data.endswith('}'):
            # 单个大括号包裹的路径
            path = data.strip('{}')
        elif '}{' in data:
            # 多个大括号包裹的路径，取第一个
            path = data.split('}{')[0].strip('{}')
        elif data.startswith('"') and data.endswith('"'):
            # 双引号包裹的路径
            path = data.strip('"')
        else:
            # 普通路径
            path = data
        
        # 处理路径中的转义空格
        path = path.replace('\\ ', ' ')
        
        self._handle_path(path)

    def _handle_path(self, path):
        self.current_path = path
        self.is_file = False

        if os.path.isdir(path):
            # 拖入文件夹
            self.is_file = False
            self.current_folder = path
            self.folder_var.set(path)
            self.file_var.set("-")
            
            self._log(f"扫描文件夹: {path}")
            self._update_file_list()
            self._log(f"发现 {len(self.all_files_in_folder)} 个文件，筛选后 {len(self.target_files)} 个")
            self._update_scan_buttons()

        elif os.path.isfile(path):
            # 拖入文件
            self.is_file = True
            self.current_folder = os.path.dirname(path)
            self.folder_var.set(self.current_folder)
            self.file_var.set(path)
            
            ext = os.path.splitext(path)[1].lower()
            self._log(f"已识别文件: {os.path.basename(path)} ({ext})")
            self._update_file_list()

        else:
            self.folder_var.set("无效路径")
            self.file_var.set("-")
            self.count_var.set("-")
            self.decrypt_all_btn.config(state="disabled")
            self.decrypt_single_btn.config(state="disabled")
            self._log(f"[错误] 无效路径: {path}")
            return

        self.open_btn.config(state="normal")
        # 刷新按钮：只要有有效路径就可用（文件或文件夹都可以刷新）
        if self.current_folder and os.path.isdir(self.current_folder):
            self.refresh_btn.config(state="normal")
        else:
            self.refresh_btn.config(state="disabled")

    def _refresh_files(self):
        """刷新文件列表，重新扫描文件夹"""
        if not self.current_folder or not os.path.isdir(self.current_folder):
            return

        self._log(f"刷新文件夹: {self.current_folder}")
        self._update_file_list()
        self._log(f"重新扫描完成，共 {len(self.all_files_in_folder)} 个文件，筛选后 {len(self.target_files)} 个")

    def _do_decrypt_all(self):
        """解密所有（筛选后的）文件"""
        if not self.target_files:
            messagebox.showwarning("提示", "没有可解密的文件")
            return

        self.decrypt_all_btn.config(state="disabled")
        self.decrypt_single_btn.config(state="disabled")
        total = len(self.target_files)
        self._log(f"开始解密所有文件，共 {total} 个...")
        self._run_decrypt(self.target_files)

    def _do_decrypt_single(self):
        """解密单个文件（拖入的那个文件）"""
        if not self.is_file or not self.current_path:
            messagebox.showwarning("提示", "没有可解密的单个文件")
            return

        self.decrypt_all_btn.config(state="disabled")
        self.decrypt_single_btn.config(state="disabled")
        self._log(f"开始解密单个文件: {os.path.basename(self.current_path)}")
        self._run_decrypt([self.current_path])

    def _run_decrypt(self, files):
        """执行解密"""
        self.source_files = []   # 清空源文件记录
        self.decrypted_files = []  # 清空输出文件记录

        def decrypt_task():
            success = 0
            failed = 0

            for i, file_path in enumerate(files, 1):
                ext = os.path.splitext(file_path)[1].lower()
                decoder_name, func_name = self.decoder_map.get(ext, (None, None))

                if not decoder_name:
                    continue

                self.root.after(0, lambda i=i, total=len(files): self.status_var.set(f"正在解密 ({i}/{len(files)})..."))
                self.root.after(0, lambda f=os.path.basename(file_path): self._log(f"[{i}/{len(files)}] {f}"))

                try:
                    decoder_module = __import__(decoder_name)
                    decrypt_func = getattr(decoder_module, func_name)
                    result = decrypt_func(file_path)
                    success += 1
                    # 记录源文件（解密前）
                    self.source_files.append(file_path)
                    # 记录输出文件（解密后，decrypt_func 可能返回单个路径或路径列表）
                    if isinstance(result, list):
                        self.decrypted_files.extend(result)
                    else:
                        self.decrypted_files.append(result)
                except Exception as e:
                    self.root.after(0, lambda e=str(e): self._log(f"  [错误] {e}"))
                    failed += 1

            self.root.after(0, lambda s=success, f=failed: self._batch_done(s, f))

        threading.Thread(target=decrypt_task, daemon=True).start()

    def _batch_done(self, success, failed):
        self._log(f"解密完成: 成功 {success} 个, 失败 {failed} 个")
        self.status_var.set(f"完成 ({success}/{success+failed})")
        self.decrypt_all_btn.config(state="normal")
        self.refresh_btn.config(state="normal" if self.current_folder and os.path.isdir(self.current_folder) else "disabled")
        if self.is_file:
            self.decrypt_single_btn.config(state="normal")
        # 如果有成功解密的文件，启用删除源文件和去除后缀按钮
        if self.source_files:
            self.delete_src_btn.config(state="normal")
        if self.decrypted_files:
            self.rename_btn.config(state="normal")
        # 解密后重新扫描 _decode 文件和 Decode 文件夹，启用对应按钮
        self._scan_decode_files_and_folders(self.recursive_var.get())
        self._update_scan_buttons()
        messagebox.showinfo("解密完成", f"成功: {success} 个\n失败: {failed} 个")

    def _open_location(self):
        if self.current_folder and os.path.exists(self.current_folder):
            os.startfile(self.current_folder)

    def _update_scan_buttons(self):
        """根据扫描到的 _decode 文件和 Decode 文件夹更新按钮状态"""
        if self.decode_files:
            self.delete_decode_files_btn.config(state="normal")
        else:
            self.delete_decode_files_btn.config(state="disabled")
        if self.decode_folders:
            self.delete_decode_folder_btn.config(state="normal")
        else:
            self.delete_decode_folder_btn.config(state="disabled")

    def _do_delete_all_decode_files(self):
        """删除当前扫描到的所有 _decode 后缀文件（无需先解密）"""
        if not self.decode_files:
            messagebox.showinfo("提示", "没有找到 _decode 文件")
            return

        # 构建确认信息
        file_list = "\n".join([f"  • {os.path.basename(f)}" for f in self.decode_files[:15]])
        if len(self.decode_files) > 15:
            file_list += f"\n  ... 等共 {len(self.decode_files)} 个文件"

        confirm_msg = f"确定要删除以下 _decode 文件吗？\n\n{file_list}\n\n⚠️ 此操作不可恢复！"

        if not messagebox.askyesno("确认删除", confirm_msg, icon="warning"):
            return

        deleted = 0
        failed = 0
        for file_path in self.decode_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted += 1
                    self._log(f"[已删除] {os.path.basename(file_path)}")
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self._log(f"[删除失败] {os.path.basename(file_path)}: {e}")

        self.decode_files = []
        self.delete_decode_files_btn.config(state="disabled")

        if failed == 0:
            messagebox.showinfo("删除完成", f"成功删除 {deleted} 个 _decode 文件")
        else:
            messagebox.showwarning("删除完成", f"成功: {deleted} 个\n失败: {failed} 个")

    def _do_delete_decode_folders(self):
        """删除当前扫描到的所有 Decode 文件夹"""
        if not self.decode_folders:
            messagebox.showinfo("提示", "没有找到 Decode 文件夹")
            return

        # 构建确认信息
        folder_list = "\n".join([f"  • {os.path.basename(os.path.dirname(f))}/Decode" for f in self.decode_folders[:10]])
        if len(self.decode_folders) > 10:
            folder_list += f"\n  ... 等共 {len(self.decode_folders)} 个文件夹"

        confirm_msg = f"确定要删除以下 Decode 文件夹吗？\n\n{folder_list}\n\n⚠️ 此操作不可恢复！"

        if not messagebox.askyesno("确认删除", confirm_msg, icon="warning"):
            return

        deleted = 0
        failed = 0
        import shutil
        for folder_path in self.decode_folders:
            try:
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                    deleted += 1
                    self._log(f"[已删除] {folder_path}")
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self._log(f"[删除失败] {folder_path}: {e}")

        self.decode_folders = []
        self.delete_decode_folder_btn.config(state="disabled")

        if failed == 0:
            messagebox.showinfo("删除完成", f"成功删除 {deleted} 个 Decode 文件夹")
        else:
            messagebox.showwarning("删除完成", f"成功: {deleted} 个\n失败: {failed} 个")

    def _delete_source_files(self):
        """删除本次解密的源文件（即解密前的原始加密文件）"""
        if not self.source_files:
            messagebox.showinfo("提示", "没有可删除的源文件")
            return

        # 构建确认信息
        file_list = "\n".join([f"  • {os.path.basename(f)}" for f in self.source_files[:10]])
        if len(self.source_files) > 10:
            file_list += f"\n  ... 等共 {len(self.source_files)} 个文件"

        confirm_msg = f"确定要删除以下源文件吗？\n\n{file_list}\n\n⚠️ 此操作不可恢复！"

        if not messagebox.askyesno("确认删除", confirm_msg, icon="warning"):
            return

        # 执行删除
        deleted = 0
        failed = 0

        for file_path in self.source_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted += 1
                    self._log(f"[已删除] {os.path.basename(file_path)}")
                else:
                    failed += 1
                    self._log(f"[不存在] {os.path.basename(file_path)}")
            except Exception as e:
                failed += 1
                self._log(f"[删除失败] {os.path.basename(file_path)}: {e}")

        # 清空源文件列表，禁用按钮
        self.source_files = []
        self.delete_src_btn.config(state="disabled")

        # 刷新文件列表
        self._update_file_list()

        # 显示结果
        if failed == 0:
            messagebox.showinfo("删除完成", f"成功删除 {deleted} 个源文件")
        else:
            messagebox.showwarning("删除完成", f"成功: {deleted} 个\n失败: {failed} 个")

    def _rename_remove_decode(self):
        """将已解密文件的 _decode 后缀去掉，重命名为原始文件名"""
        if not self.decrypted_files:
            messagebox.showinfo("提示", "没有可重命名的文件")
            return

        # 找出所有带 _decode 后缀的文件
        rename_pairs = []  # (old_path, new_path)
        conflict_files = []  # 目标文件已存在

        for file_path in self.decrypted_files:
            base, ext = os.path.splitext(file_path)
            if base.endswith("_decode"):
                new_base = base[:-7]  # 去掉 "_decode"（7个字符）
                new_path = new_base + ext
                rename_pairs.append((file_path, new_path))
                if os.path.exists(new_path):
                    conflict_files.append(os.path.basename(new_path))

        if not rename_pairs:
            messagebox.showinfo("提示", "没有找到带 _decode 后缀的文件")
            return

        # 构建确认信息
        file_list = "\n".join([f"  • {os.path.basename(o)} → {os.path.basename(n)}"
                               for o, n in rename_pairs[:10]])
        if len(rename_pairs) > 10:
            file_list += f"\n  ... 等共 {len(rename_pairs)} 个文件"

        confirm_msg = f"确定要重命名以下文件吗？\n\n{file_list}"

        if conflict_files:
            conflict_list = "\n".join([f"  • {f}" for f in conflict_files[:5]])
            confirm_msg += f"\n\n⚠️ 以下文件已存在，将被覆盖：\n{conflict_list}"

        if not messagebox.askyesno("确认重命名", confirm_msg, icon="question"):
            return

        # 执行重命名
        renamed = 0
        failed = 0
        new_paths = []

        for old_path, new_path in rename_pairs:
            try:
                if os.path.exists(new_path):
                    os.remove(new_path)  # 覆盖已存在的文件
                os.rename(old_path, new_path)
                renamed += 1
                new_paths.append(new_path)
                self._log(f"[已重命名] {os.path.basename(old_path)} → {os.path.basename(new_path)}")
            except Exception as e:
                failed += 1
                self._log(f"[重命名失败] {os.path.basename(old_path)}: {e}")

        # 更新 decrypted_files 为新路径
        self.decrypted_files = new_paths
        self.rename_btn.config(state="disabled")

        # 刷新文件列表
        self._update_file_list()

        # 显示结果
        if failed == 0:
            messagebox.showinfo("重命名完成", f"成功重命名 {renamed} 个文件")
        else:
            messagebox.showwarning("重命名完成", f"成功: {renamed} 个\n失败: {failed} 个")

    def _log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")


def main():
    try:
        import tkinterdnd2
    except ImportError:
        print("正在安装 tkinterdnd2...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinterdnd2", "-q"])

    from tkinterdnd2 import TkinterDnD
    root = TkinterDnD.Tk()
    app = DecoderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

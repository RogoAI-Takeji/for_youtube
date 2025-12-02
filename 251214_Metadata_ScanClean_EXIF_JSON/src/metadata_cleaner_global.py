#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadata Scan&Clean v2.0.0 (Global)
takejii_app_001
Multi-language support (JP/EN) added.
"""

import os
import sys
import shutil
import subprocess
import threading
import json
import queue
import stat
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from collections import Counter
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ==========================================
# 🌍 LANGUAGE SETTINGS / 言語設定
# ==========================================
# Change this to 'JP' for Japanese, 'EN' for English
# ここを 'JP' にすると日本語、'EN' にすると英語になります
LANGUAGE = 'EN' 
# ==========================================

TRANSLATIONS = {
    'app_title': {'JP': 'Metadata Scan&Clean', 'EN': 'Metadata Scan & Clean'},
    'tab_clean': {'JP': 'クリーニング', 'EN': 'Cleaning'},
    'tab_scan': {'JP': 'スキャン結果', 'EN': 'Scan Results'},
    'tab_compare': {'JP': 'ビフォー・アフター', 'EN': 'Before & After'},
    
    'grp_mode': {'JP': 'クリーニングモード', 'EN': 'Cleaning Mode'},
    'mode_smart': {'JP': 'スマート削除（推奨）\n ※画質維持・向き保持。Exif/GPS/AIタグ除去', 
                   'EN': 'Smart Clean (Recommended)\n *Keeps quality/orientation. Removes Exif/GPS/AI tags.'},
    'mode_full': {'JP': '完全削除（再エンコード）\n ※画質がわずかに劣化', 
                  'EN': 'Full Clean (Re-encode)\n *Slight quality loss. Removes EVERYTHING.'},
    
    'lbl_folder': {'JP': '対象フォルダ:', 'EN': 'Target Folder:'},
    'btn_browse': {'JP': '参照', 'EN': 'Browse'},
    
    'btn_scan': {'JP': '🔍 スキャン', 'EN': '🔍 Scan'},
    'btn_diag': {'JP': '💊 診断', 'EN': '💊 Diagnose'},
    'btn_start': {'JP': '✨ 実行', 'EN': '✨ Run'},
    'btn_stop': {'JP': '⏹ 停止', 'EN': '⏹ Stop'},
    
    'status_wait': {'JP': '待機中...', 'EN': 'Ready...'},
    'status_scanning': {'JP': 'スキャン: ', 'EN': 'Scanning: '},
    'status_processing': {'JP': '処理中: ', 'EN': 'Processing: '},
    
    'col_file': {'JP': 'ファイル名', 'EN': 'Filename'},
    'col_score': {'JP': '危険度', 'EN': 'Risk Score'},
    'col_detail': {'JP': '検出情報', 'EN': 'Details'},
    
    'btn_orig': {'JP': '📂 元ファイル選択', 'EN': '📂 Select Original File'},
    'grp_before': {'JP': '📂 Before (元ファイル)', 'EN': '📂 Before (Original)'},
    'grp_after': {'JP': '✨ After (クリーニング後)', 'EN': '✨ After (Cleaned)'},
    
    'msg_scan_done': {'JP': 'スキャン完了', 'EN': 'Scan Complete'},
    'msg_total': {'JP': '総ファイル数', 'EN': 'Total Files'},
    'msg_danger': {'JP': '危険なメタデータ検出', 'EN': 'Risky Metadata Found'},
    'msg_gps': {'JP': 'GPS情報', 'EN': 'GPS Data'},
    'msg_author': {'JP': '個人名/著作権', 'EN': 'Author/Copyright'},
    'msg_ai': {'JP': 'AI生成情報', 'EN': 'AI Gen Info'},
    'msg_high_risk': {'JP': '⚠️ 高危険度ファイル', 'EN': '⚠️ High Risk Files'},
    
    'msg_no_target': {'JP': '処理対象なし', 'EN': 'No files to process'},
    'msg_done': {'JP': '完了', 'EN': 'Done'},
    'msg_success': {'JP': '✨ 成功', 'EN': '✨ Success'},
    'msg_fail': {'JP': '💀 失敗', 'EN': '💀 Failed'},
    
    'log_scan_start': {'JP': '🔍 スキャン開始...', 'EN': '🔍 Scan started...'},
    'log_env_check': {'JP': '=== 環境チェック ===', 'EN': '=== Environment Check ==='},
    'log_clean_start': {'JP': 'フォルダ再作成', 'EN': 'Re-creating folder'},
    'log_diff': {'JP': '♻ 差分処理', 'EN': '♻ Differential processing'},
    'log_output': {'JP': '📂 出力先', 'EN': '📂 Output to'},
}

def tr(key):
    return TRANSLATIONS.get(key, {}).get(LANGUAGE, key)

try:
    from PIL import Image, ImageOps
    import piexif
    HAS_PIL = True
    PIL_VERSION = Image.__version__
except ImportError:
    HAS_PIL = False
    PIL_VERSION = "N/A"

def get_ffmpeg_path():
    paths = [
        os.path.join(os.path.dirname(sys.executable), '_internal', 'ffmpeg', 'ffmpeg.exe'),
        os.path.join(os.getcwd(), 'ffmpeg', 'ffmpeg.exe'),
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\FFmpeg\bin\ffmpeg.exe"),
    ]
    for p in paths:
        if os.path.exists(p): return p
    return shutil.which('ffmpeg')

def get_ffprobe_path():
    ff = get_ffmpeg_path()
    if ff:
        d = os.path.dirname(ff)
        p = os.path.join(d, 'ffprobe.exe' if sys.platform == 'win32' else 'ffprobe')
        if os.path.exists(p): return p
    return shutil.which('ffprobe')

def remove_readonly(func, path, _):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

class MetadataApp:
    VERSION = "2.0.0"
    APP_ID = "takejii_app_001"
    
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp', '.bmp'}
    VIDEO_EXTS = {'.mp4', '.mov', '.webm', '.mkv', '.avi', '.flv', '.wmv'}
    AUDIO_EXTS = {'.mp3', '.wav', '.flac', '.ogg', '.opus', '.m4a', '.aac'}
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{tr('app_title')} ({self.APP_ID}) v{self.VERSION}")
        self.root.geometry("550x850") # Slightly wider for English text
        
        self.log_queue = queue.Queue()
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self.source_folder = tk.StringVar()
        self.clean_mode = tk.StringVar(value="smart")
        self.stop_requested = False
        
        self.create_widgets()
        self.check_environment()
        self.process_log_queue()
    
    def process_log_queue(self):
        while not self.log_queue.empty():
            msg, is_error = self.log_queue.get()
            self._write_log(msg, is_error)
        self.root.after(100, self.process_log_queue)

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tab_clean = ttk.Frame(notebook)
        notebook.add(tab_clean, text=tr('tab_clean'))
        self.create_clean_tab(tab_clean)
        
        tab_scan = ttk.Frame(notebook)
        notebook.add(tab_scan, text=tr('tab_scan'))
        self.create_scan_tab(tab_scan)
        
        tab_compare = ttk.Frame(notebook)
        notebook.add(tab_compare, text=tr('tab_compare'))
        self.create_compare_tab(tab_compare)
    
    def create_clean_tab(self, parent):
        main = ttk.Frame(parent, padding="5")
        main.pack(fill=tk.BOTH, expand=True)
        
        m_frame = ttk.LabelFrame(main, text=tr('grp_mode'), padding="5")
        m_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(m_frame, text=tr('mode_smart'), 
                       variable=self.clean_mode, value="smart").pack(anchor=tk.W)
        ttk.Radiobutton(m_frame, text=tr('mode_full'), 
                       variable=self.clean_mode, value="full").pack(anchor=tk.W)
        
        ttk.Label(main, text=tr('lbl_folder')).pack(anchor=tk.W, pady=5)
        f_frame = ttk.Frame(main)
        f_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(f_frame, textvariable=self.source_folder).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(f_frame, text=tr('btn_browse'), command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        
        b_frame = ttk.Frame(main)
        b_frame.pack(pady=10, fill=tk.X)
        
        style = ttk.Style()
        style.configure("Scan.TButton", background="#ADD8E6")
        style.configure("Diag.TButton", background="#FFB6C1")
        style.configure("Start.TButton", background="#90EE90")

        self.scan_btn = ttk.Button(b_frame, text=tr('btn_scan'), command=self.scan_folder, style="Scan.TButton")
        self.scan_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        self.diag_btn = ttk.Button(b_frame, text=tr('btn_diag'), command=self.run_diagnostic, style="Diag.TButton")
        self.diag_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        self.start_btn = ttk.Button(b_frame, text=tr('btn_start'), command=self.start_cleaning, style="Start.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        self.stop_btn = ttk.Button(b_frame, text=tr('btn_stop'), command=self.stop_process, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.progress = ttk.Progressbar(main, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        self.progress_label = ttk.Label(main, text=tr('status_wait'))
        self.progress_label.pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(main, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def create_scan_tab(self, parent):
        main = ttk.Frame(parent, padding="5")
        main.pack(fill=tk.BOTH, expand=True)
        
        self.summary_text = tk.Text(main, height=14, state=tk.DISABLED, font=("Consolas", 9))
        self.summary_text.pack(fill=tk.X, pady=5)
        
        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_tree = ttk.Treeview(tree_frame, columns=("file", "score", "details"), show="headings")
        self.file_tree.heading("file", text=tr('col_file'))
        self.file_tree.heading("score", text=tr('col_score'))
        self.file_tree.heading("details", text=tr('col_detail'))
        self.file_tree.column("file", width=150)
        self.file_tree.column("score", width=60)
        self.file_tree.column("details", width=200)
        
        sc = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        self.file_tree.bind("<Double-1>", self.show_file_detail)

    def create_compare_tab(self, parent):
        main = ttk.Frame(parent, padding="5")
        main.pack(fill=tk.BOTH, expand=True)
        
        sel_frame = ttk.Frame(main)
        sel_frame.pack(fill=tk.X, pady=5)
        ttk.Button(sel_frame, text=tr('btn_orig'), command=self.select_original_file).pack(fill=tk.X)
        
        paned = ttk.PanedWindow(main, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)
        
        f_before = ttk.LabelFrame(paned, text=tr('grp_before'), padding=2)
        paned.add(f_before, weight=2)
        self.before_text = scrolledtext.ScrolledText(f_before, width=40, height=15)
        self.before_text.pack(fill=tk.BOTH, expand=True)
        
        f_after = ttk.LabelFrame(paned, text=tr('grp_after'), padding=2)
        paned.add(f_after, weight=1)
        self.after_text = scrolledtext.ScrolledText(f_after, width=40, height=8)
        self.after_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str, error: bool = False):
        self.log_queue.put((message, error))

    def _write_log(self, message: str, error: bool):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "ERROR" if error else "INFO"
        self.log_text.insert(tk.END, f"[{ts}] {prefix}: {message}\n")
        self.log_text.see(tk.END)

    def reset_progress(self):
        self.progress['value'] = 0
        self.progress_label.config(text=tr('status_wait'))

    def check_environment(self):
        self.log(tr('log_env_check'))
        self.log(f"Python: {sys.version.split()[0]}")
        if HAS_PIL: self.log(f"✓ Pillow: {PIL_VERSION}")
        else: self.log("✗ Pillow: Not Installed", error=True)
        
        self.ffmpeg_path = get_ffmpeg_path()
        if self.ffmpeg_path: self.log(f"✓ FFmpeg: {self.ffmpeg_path}")
        else:
            self.log("✗ FFmpeg: Not Found", error=True)
            self.start_btn.config(state=tk.DISABLED)
        
        self.ffprobe_path = get_ffprobe_path()
        if self.ffprobe_path: self.log(f"✓ FFprobe: {self.ffprobe_path}")
        else: self.log("✗ FFprobe: Not Found", error=True)
        self.log("===================\n")

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.source_folder.set(f)
            self.log(f"Dir: {f}")

    def run_thread(self, target, *args):
        t = threading.Thread(target=target, args=args, daemon=True)
        t.start()

    # === SCAN ===
    def scan_folder(self):
        source = self.source_folder.get()
        if not source: return
        self.stop_requested = False
        self.stop_btn.config(state=tk.NORMAL)
        self.file_tree.delete(*self.file_tree.get_children())
        self.run_thread(self._scan_thread, source)

    def _scan_thread(self, folder):
        self.log(tr('log_scan_start'))
        all_exts = self.IMAGE_EXTS | self.VIDEO_EXTS | self.AUDIO_EXTS
        files = []
        for r, d, f in os.walk(folder):
            if '_clean' in r: continue
            for file in f:
                if os.path.splitext(file)[1].lower() in all_exts:
                    files.append(os.path.join(r, file))
        
        total = len(files)
        ext_counts = Counter([os.path.splitext(f)[1].lower() for f in files])
        ext_summary_lines = [f"  {k}: {v}" for k, v in sorted(ext_counts.items())]
        ext_summary_text = "\n".join(ext_summary_lines)

        self.root.after(0, lambda: self.progress.configure(maximum=total))
        
        gps_c = author_c = ai_c = 0
        danger = []
        
        for i, path in enumerate(files):
            if self.stop_requested: break
            self.root.after(0, lambda v=i: self.progress.configure(value=v+1))
            self.root.after(0, lambda v=i: self.progress_label.config(text=f"{tr('status_scanning')}{v+1}/{total}"))
            
            meta = self._get_simple_meta_info(path)
            if meta['has_gps']: gps_c += 1
            if meta['has_author']: author_c += 1
            if meta['has_ai']: ai_c += 1
            
            score = 0
            if meta['has_gps']: score += 40
            if meta['has_author']: score += 30
            if meta['has_ai']: score += 30
            
            if score >= 30:
                dets = []
                if meta['has_gps']: dets.append(tr('msg_gps'))
                if meta['has_author']: dets.append(tr('msg_author'))
                if meta['has_ai']: dets.append(tr('msg_ai'))
                danger.append((os.path.basename(path), score, ", ".join(dets)))
                icon = "🔴" if score >= 60 else "🟡"
                self.root.after(0, lambda p=os.path.basename(path), s=score, d=", ".join(dets), i=icon: 
                                self.file_tree.insert("", tk.END, values=(p, f"{i} {s}", d)))

        summary = f"""{tr('msg_scan_done')}
{tr('msg_total')}: {total}

📊 Exts:
{ext_summary_text}

🔴 {tr('msg_danger')}:
  📍 GPS: {gps_c}
  👤 Author: {author_c}
  🤖 AI Info: {ai_c}

{tr('msg_high_risk')}: {len(danger)}"""

        self.root.after(0, lambda: self.summary_text.configure(state=tk.NORMAL))
        self.root.after(0, lambda: self.summary_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.summary_text.insert(1.0, summary))
        self.root.after(0, lambda: self.summary_text.configure(state=tk.DISABLED))
        self.log(summary)
        self.root.after(0, lambda: self._on_scan_finished(summary))

    def _on_scan_finished(self, summary):
        messagebox.showinfo(tr('msg_scan_done'), summary)
        self.reset_progress()
        self.stop_btn.config(state=tk.DISABLED)
        self.scan_btn.config(state=tk.NORMAL)

    def _get_simple_meta_info(self, path):
        info = {'has_gps': False, 'has_author': False, 'has_ai': False}
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in self.IMAGE_EXTS and HAS_PIL:
                img = Image.open(path)
                if ext == '.png':
                    if hasattr(img, 'info'):
                        for k, v in img.info.items():
                            if isinstance(v, str) and ('workflow' in v.lower() or 'prompt' in v.lower()):
                                info['has_ai'] = True
                elif ext in ['.jpg', '.jpeg']:
                    exif = piexif.load(path)
                    if exif.get('GPS'): info['has_gps'] = True
                    if any(k in exif.get('0th', {}) for k in [piexif.ImageIFD.Artist, piexif.ImageIFD.Copyright]):
                        info['has_author'] = True
            
            elif ext in (self.VIDEO_EXTS | self.AUDIO_EXTS) and self.ffprobe_path:
                cmd = [self.ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', path]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=3)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    tags = data.get('format', {}).get('tags', {})
                    for k, v in tags.items():
                        kl = k.lower()
                        if 'location' in kl or 'gps' in kl: info['has_gps'] = True
                        if 'artist' in kl or 'author' in kl: info['has_author'] = True
                        if 'comment' in kl and ('workflow' in str(v) or 'prompt' in str(v)): info['has_ai'] = True
        except: pass
        return info

    # === DIAGNOSTIC ===
    def run_diagnostic(self):
        source = self.source_folder.get()
        if not source: return
        self.stop_requested = False
        self.stop_btn.config(state=tk.NORMAL)
        self.run_thread(self._diagnostic_thread, source)
        
    def _diagnostic_thread(self, folder):
        self.log("\n=== 💊 DIAGNOSTIC ===")
        all_files = []
        for r, d, f in os.walk(folder):
            for file in f:
                if os.path.splitext(file)[1].lower() in (self.IMAGE_EXTS | self.VIDEO_EXTS):
                    all_files.append(os.path.join(r, file))
        
        targets = all_files[:5]
        self.log(f"Checking top {len(targets)} files...")
        
        for path in targets:
            if self.stop_requested: break
            fname = os.path.basename(path)
            self.log(f"\n📄 {fname}")
            
            detail = self.extract_metadata_detail(path)
            lines = detail.split('\n')
            for line in lines[:20]:
                if line.strip() and "File:" not in line and "Size:" not in line:
                    self.log(f"  {line}")
            if len(lines) > 20:
                self.log("  ... (See 'Before & After' tab)")
        self.log("\n=== END ===")
        self.stop_btn.config(state=tk.DISABLED)

    # === CLEANING ===
    def start_cleaning(self):
        source = self.source_folder.get()
        if not source: return
        
        parent = os.path.dirname(source)
        name = os.path.basename(source)
        dest = os.path.join(parent, f"{name}_clean")
        
        strat = "new"
        if os.path.exists(dest):
            exist = sum(1 for r, d, f in os.walk(dest) for file in f)
            if exist > 0:
                ans = messagebox.askyesnocancel("Folder Exists", 
                    f"{name}_clean exists ({exist} files)\n\n"
                    "Yes: Differential\nNo: Overwrite (Delete All)\nCancel: Stop")
                if ans is None: return
                if ans is True: strat = "diff"
                if ans is False: strat = "overwrite"
        
        self.stop_requested = False
        self.stop_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.DISABLED)
        self.run_thread(self._clean_thread, source, strat)

    def _clean_thread(self, source, strat):
        try:
            parent = os.path.dirname(source)
            name = os.path.basename(source)
            dest_root = os.path.join(parent, f"{name}_clean")
            
            if strat == "overwrite":
                self.log(f"{tr('log_clean_start')}: {dest_root}")
                if os.path.exists(dest_root):
                    shutil.rmtree(dest_root, onerror=remove_readonly)
                os.makedirs(dest_root)
            elif strat == "diff":
                self.log(f"{tr('log_diff')}: {dest_root}")
                if not os.path.exists(dest_root): os.makedirs(dest_root)
            else:
                self.log(f"{tr('log_output')}: {dest_root}")
                if not os.path.exists(dest_root): os.makedirs(dest_root)
            
            targets = []
            for r, d, f in os.walk(source):
                if '_clean' in r: continue
                for file in f:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.IMAGE_EXTS | self.VIDEO_EXTS | self.AUDIO_EXTS:
                        src = os.path.join(r, file)
                        rel = os.path.relpath(src, source)
                        dst = os.path.join(dest_root, rel)
                        if strat == "diff" and os.path.exists(dst):
                            if os.path.getmtime(src) <= os.path.getmtime(dst): continue
                        targets.append((src, dst))

            if not targets:
                self.log(tr('msg_no_target'))
                self.root.after(0, lambda: messagebox.showinfo(tr('msg_done'), tr('msg_no_target')))
                self.root.after(0, lambda: self.reset_progress())
                self.root.after(0, lambda: self._enable_buttons())
                return

            self.root.after(0, lambda: self.progress.configure(maximum=len(targets)))
            ok = err = 0
            
            for i, (src, dst) in enumerate(targets):
                if self.stop_requested: break
                self.root.after(0, lambda v=i: self.progress.configure(value=v+1))
                self.root.after(0, lambda v=i, t=len(targets): self.progress_label.config(text=f"{tr('status_processing')}{v+1}/{t}"))
                try:
                    res = self.process_file(src, dst)
                    if res: ok += 1
                    else: err += 1
                except Exception as e:
                    self.log(f"⚠ Err: {os.path.basename(src)} - {e}", True)
                    err += 1
            
            msg = f"{tr('msg_done')}\n{tr('msg_success')}: {ok}\n{tr('msg_fail')}: {err}"
            self.log(msg.replace('\n', ', '))
            self.root.after(0, lambda: self._on_clean_finished(msg))
            
        except Exception as e:
            self.log(f"FATAL: {e}", True)
            self.root.after(0, lambda: self._enable_buttons())

    def _on_clean_finished(self, msg):
        messagebox.showinfo(tr('msg_done'), msg)
        self.reset_progress()
        self._enable_buttons()

    def _enable_buttons(self):
        self.stop_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)

    def process_file(self, src, dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        ext = os.path.splitext(src)[1].lower()
        
        if ext in self.IMAGE_EXTS and HAS_PIL and self.clean_mode.get() == "smart":
            try:
                if ext in ['.jpg', '.jpeg']:
                    shutil.copy2(src, dst)
                    try:
                        ed = piexif.load(src)
                        new_ed = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
                        if 274 in ed["0th"]: new_ed["0th"][274] = ed["0th"][274]
                        piexif.insert(piexif.dump(new_ed), dst)
                        return True
                    except: pass

                img = Image.open(src)
                img = ImageOps.exif_transpose(img)
                data = list(img.getdata())
                new_img = Image.new(img.mode, img.size)
                new_img.putdata(data)
                
                if ext == '.png': new_img.save(dst, optimize=True)
                elif ext in ['.jpg', '.jpeg']: new_img.save(dst, quality=95)
                else: new_img.save(dst)
                return True
            except Exception as e:
                self.log(f"Img Err: {e}", True)
                shutil.copy2(src, dst)
                return False

        d_name, b_name = os.path.split(dst)
        temp = os.path.join(d_name, f"temp_{b_name}")
        
        try:
            cmd = []
            if ext in self.VIDEO_EXTS | self.AUDIO_EXTS:
                cmd = [self.ffmpeg_path, '-y', '-hide_banner', '-loglevel', 'error',
                       '-i', src, '-map_metadata', '-1', '-c', 'copy', temp]
            else:
                shutil.copy2(src, dst)
                return True

            subprocess.run(cmd, check=True)
            if os.path.exists(temp):
                if os.path.exists(dst): os.remove(dst)
                os.rename(temp, dst)
                return True
            raise Exception("Output fail")
        except Exception as e:
            self.log(f"FFmpeg Err: {e}", True)
            if os.path.exists(temp): os.remove(temp)
            shutil.copy2(src, dst)
            return False

    def select_original_file(self):
        f = filedialog.askopenfilename()
        if f: self.run_thread(self._load_compare_info, f)

    def _load_compare_info(self, f_path):
        self.root.after(0, lambda: self.before_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.before_text.insert(1.0, "Loading..."))
        m_before = self.extract_metadata_detail(f_path)
        self.root.after(0, lambda: self.before_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.before_text.insert(1.0, m_before))
        
        clean_file = None
        try:
            abs_p = os.path.abspath(f_path)
            cur = os.path.dirname(abs_p)
            child = os.path.basename(abs_p)
            for _ in range(5):
                par = os.path.dirname(cur)
                f_name = os.path.basename(cur)
                cand_dir = os.path.join(par, f"{f_name}_clean")
                if os.path.exists(cand_dir):
                    cand_f = os.path.join(cand_dir, child)
                    if os.path.exists(cand_f):
                        clean_file = cand_f
                        break
                child = os.path.join(f_name, child)
                cur = par
                if len(os.path.splitdrive(cur)[1]) <= 1: break
        except: pass

        self.root.after(0, lambda: self.after_text.delete(1.0, tk.END))
        if clean_file:
            self.root.after(0, lambda: self.after_text.insert(1.0, "Loading..."))
            m_after = self.extract_metadata_detail(clean_file)
            self.root.after(0, lambda: self.after_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.after_text.insert(1.0, m_after))
        else:
            self.root.after(0, lambda: self.after_text.insert(1.0, "No cleaned file found"))

    def extract_metadata_detail(self, path):
        text = f"File: {os.path.basename(path)}\nSize: {os.path.getsize(path):,} bytes\n" + "-"*30 + "\n"
        ext = os.path.splitext(path)[1].lower()
        LIMIT = 1000
        
        if self.ffprobe_path and (ext in self.VIDEO_EXTS | self.AUDIO_EXTS):
            try:
                cmd = [self.ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', path]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
                data = json.loads(res.stdout)
                tags = data.get('format', {}).get('tags', {})
                if not tags: text += "✓ No Metadata"
                for k, v in tags.items():
                    s = str(v)
                    if len(s) > LIMIT: s = s[:LIMIT] + f"\n... ({len(s)-LIMIT:,} more)"
                    text += f"[{k}] : {s}\n\n"
            except Exception as e: text += f"Error: {e}"
        elif HAS_PIL and ext in self.IMAGE_EXTS:
            try:
                img = Image.open(path)
                if ext == '.png':
                    if not img.info: text += "✓ No PNG Info"
                    for k, v in img.info.items():
                        s = str(v)
                        if len(s) > LIMIT: s = s[:LIMIT] + f"\n... ({len(s)-LIMIT:,} more)"
                        text += f"[{k}] : {s}\n\n"
                elif ext in ['.jpg', '.jpeg']:
                    ed = piexif.load(path)
                    has_d = False
                    for ifd in ed:
                        if ifd == "thumbnail": continue
                        if ed[ifd]:
                            text += f"--- {ifd} ---\n"
                            for tag, val in ed[ifd].items():
                                has_d = True
                                s = str(val)
                                if isinstance(val, bytes) and len(val) > 100: s = f"<{len(val)} bytes binary>"
                                elif len(s) > LIMIT: s = s[:LIMIT] + f"\n... ({len(s)-LIMIT:,} more)"
                                t_name = piexif.TAGS[ifd].get(tag, {}).get('name', tag)
                                text += f"{t_name}: {s}\n"
                    if not has_d: text += "✓ No Exif Data"
            except Exception as e: text += f"Error: {e}"
        return text

    def stop_process(self):
        self.stop_requested = True
        self.log("Stopping...")

    def show_file_detail(self, event):
        sel = self.file_tree.selection()
        if not sel: return
        fname = self.file_tree.item(sel[0])['values'][0]
        self.log(f"🔍 Detail: {fname}")

if __name__ == '__main__':
    root = tk.Tk()
    app = MetadataApp(root)
    root.mainloop()
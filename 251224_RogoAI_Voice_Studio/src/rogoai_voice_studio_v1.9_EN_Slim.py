"""
ROGOAI Voice Studio v1.9 EN Slim
Universal Voice Generation Platform

Features:
1. VOICEVOX Character Voice Generation
2. Coqui TTS XTTS Zero-Shot Voice Cloning
3. GUI Refinement: Slim layout & Custom Filename Formatting
4. Safe Asynchronous Startup
5. English Localization

Author: ROGOAI
Version: 1.9 EN Slim
License: MIT
"""

try:
    import pyi_splash
except ImportError:
    pass

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
import json
import os
import sys
from pathlib import Path
import urllib.parse
import subprocess
import platform
from datetime import datetime
from pydub import AudioSegment
import io
import threading
import traceback
import time

# ==========================================
# PyTorch Compatibility Patch
# ==========================================
import torch
_original_load = torch.load
def _patched_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load

CUDA_AVAILABLE = torch.cuda.is_available()
CUDA_DEVICE = torch.cuda.get_device_name(0) if CUDA_AVAILABLE else "CPU"
# ==========================================

# ★追加: FFmpegのパスを特定してpydubに設定する関数
def setup_ffmpeg():
    # 1. 自身のフォルダ内の ffmpeg/ffmpeg.exe を探す
    base_path = Path(__file__).parent
    ffmpeg_exe = base_path / "ffmpeg" / "ffmpeg.exe"
    ffprobe_exe = base_path / "ffmpeg" / "ffprobe.exe"
    
    # 2. 見つかったら pydub に設定
    if ffmpeg_exe.exists():
        AudioSegment.converter = str(ffmpeg_exe)
        AudioSegment.ffmpeg = str(ffmpeg_exe)
        AudioSegment.ffprobe = str(ffprobe_exe)
        print(f"Local FFmpeg loaded: {ffmpeg_exe}")
    else:
        print("Local FFmpeg not found. Using system default.")
        
class VoicevoxCoquiGUI:
    def __init__(self, root):
        setup_ffmpeg()  # ★ここで実行！
        
        self.root = root
        gpu_status = f"GPU: {CUDA_DEVICE}" if CUDA_AVAILABLE else "CPU Mode"
        self.root.title(f"🎙️ ROGOAI Voice Studio v1.9 EN - {gpu_status}")

        try:
            icon_path = Path(__file__).parent / "make_icon" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        self.root.geometry("680x860")
        
        self.app_data = self.get_app_data_path()
        self.voicevox_server_url = "http://127.0.0.1:50021"
        
        self.coqui_enabled = False
        self.coqui_model = None
        self.samples_dir = self.app_data / "samples"
        self.samples_dir.mkdir(parents=True, exist_ok=True)
        
        self.generation_stop_flag = False
        self.config_file = self.app_data / "config.json"
        self.load_config()
        
        self.voicevox_speakers = []
        self.build_gui()
        self.initialize_app_async()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_app_data_path(self):
        if getattr(sys, 'frozen', False):
            base = Path(os.path.dirname(sys.executable))
        else:
            base = Path(os.path.dirname(os.path.abspath(__file__)))
        
        app_path = base / 'user_data'
        app_path.mkdir(parents=True, exist_ok=True)
        (app_path / 'outputs').mkdir(exist_ok=True)
        return app_path

    def initialize_app_async(self):
        def _init():
            try:
                self.download_sample_voices()
                time.sleep(1.0)
                
                default_wav = self.samples_dir / "de_female_official.wav"
                if not default_wav.exists() or default_wav.stat().st_size == 0:
                    self._download_file("de_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/de_sample.wav")
                    time.sleep(1.0)

                self.root.after(0, self.refresh_coqui_speakers)
                self.initialize_coqui()
                
                self.check_voicevox_connection()
                self.root.after(0, self.refresh_voicevox_speakers)
                
            except Exception as e:
                print(f"Init Error: {e}")
                self.root.after(0, lambda: messagebox.showerror("Launch Error", f"Error during initialization:\n{e}"))

        threading.Thread(target=_init, daemon=True).start()

    def download_sample_voices(self):
        targets = [
            ("de_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/de_sample.wav"),
            ("en_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/en_sample.wav"),
            ("fr_male_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/fr_sample.wav"),
            ("it_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/it_sample.wav"),
            ("es_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/es_sample.wav"),
            ("pt_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/pt_sample.wav"),
            ("pl_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/pl_sample.wav"),
            ("zh_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/zh-cn_sample.wav"),
            ("nl_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/nl_sample.wav"),
            ("ar_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/ar_sample.wav"),
            ("ko_female_official.wav", "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/ko_sample.wav"),
        ]
        for fname, url in targets:
            self._download_file(fname, url)

    def _download_file(self, fname, url):
        save_path = self.samples_dir / fname
        if save_path.exists() and save_path.stat().st_size > 0: return
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            self.root.after(0, lambda m=f"📥 Downloading: {fname}...": self.status_bar.config(text=m))
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f: f.write(response.content)
        except: pass

    def initialize_coqui(self):
        if self.coqui_model: return
        try:
            self.root.after(0, lambda: self.coqui_status_label.config(text="Coqui TTS: Initializing...", foreground="orange"))
            self.root.after(0, lambda: self.status_bar.config(text="🚀 Loading AI Engine (Please wait)..."))
            
            from TTS.api import TTS
            self.coqui_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            if CUDA_AVAILABLE: self.coqui_model.to("cuda")
            self.coqui_enabled = True
            
            self.root.after(0, lambda: self.coqui_status_label.config(text="Coqui TTS: Ready", foreground="green"))
            self.root.after(0, lambda: self.status_bar.config(text="✓ Coqui TTS Engine Ready"))
            
        except Exception as e:
            self.root.after(0, lambda: self.coqui_status_label.config(text="Coqui TTS: Launch Failed", foreground="red"))
            err_msg = str(e)
            print(f"Coqui Init Error: {err_msg}")
            self.root.after(0, lambda: messagebox.showerror("AI Engine Error", f"Failed to initialize Coqui TTS.\n\nError:\n{err_msg}"))

    def build_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tab_tts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tts, text="🗣️ TTS (Speech Synthesis)")
        self.build_tts_tab(self.tab_tts)

    def build_tts_tab(self, parent):
        main_frame = ttk.Frame(parent, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Server Status
        status_frame = ttk.LabelFrame(main_frame, text="Server/Engine Status", padding="2")
        status_frame.pack(fill=tk.X, pady=2)
        
        self.coqui_status_label = ttk.Label(status_frame, text="Coqui TTS: Initializing...", foreground="orange")
        self.coqui_status_label.pack(side=tk.LEFT, padx=10)
        ttk.Label(status_frame, text="|").pack(side=tk.LEFT, padx=5)

        self.voicevox_status_label = ttk.Label(status_frame, text="VOICEVOX: Checking...")
        self.voicevox_status_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(status_frame, text="🔄 Reconnect", command=self.reconnect_voicevox_async, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, text="*Launch VOICEVOX to reconnect", font=("", 8), foreground="gray").pack(side=tk.LEFT, padx=5)
        
        # 2. Engine Selection
        engine_frame = ttk.LabelFrame(main_frame, text="🎙️ Engine Selection", padding="2")
        engine_frame.pack(fill=tk.X, pady=2)
        
        default_engine = self.config.get('engine', 'coqui') 
        self.engine_var = tk.StringVar(value=default_engine)
        
        ttk.Radiobutton(engine_frame, text="Coqui TTS XTTS (File based)", variable=self.engine_var, value="coqui", command=self.update_ui_state).pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(engine_frame, text="VOICEVOX (Built-in Char)", variable=self.engine_var, value="voicevox", command=self.update_ui_state).pack(side=tk.LEFT, padx=15)

        # 3. Character Settings
        self.char_frame = ttk.LabelFrame(main_frame, text="👤 Speaker Settings", padding="2")
        self.char_frame.pack(fill=tk.X, pady=2)

        # --- Coqui TTS UI ---
        self.coqui_container = ttk.Frame(self.char_frame)
        ttk.Label(self.coqui_container, text="Speaker File:").grid(row=0, column=0, sticky=tk.W, padx=(5,2))
        
        self.coqui_speaker_var = tk.StringVar()
        self.coqui_speaker_combo = ttk.Combobox(self.coqui_container, textvariable=self.coqui_speaker_var, width=30, state="readonly")
        self.coqui_speaker_combo.grid(row=0, column=1, padx=2)
        
        ttk.Button(self.coqui_container, text="Voice Folder", command=self.open_samples_dir, width=12).grid(row=0, column=2, padx=2)
        ttk.Button(self.coqui_container, text="Refresh", command=self.refresh_coqui_speakers, width=8).grid(row=0, column=3, padx=2)
        
        ttk.Label(self.coqui_container, text="Language:").grid(row=0, column=4, sticky=tk.W, padx=(10, 2))
        self.language_var = tk.StringVar(value=self.config.get('language', 'ja'))
        self.language_combo = ttk.Combobox(self.coqui_container, textvariable=self.language_var, width=8, state="readonly")
        self.language_combo['values'] = ['ja - 日', 'en - 英', 'zh-cn - 中', 'ko - 韓', 'fr - 仏', 'de - 独']
        self.language_combo.current(0)
        self.language_combo.grid(row=0, column=5, padx=2)

        # --- VOICEVOX UI ---
        self.vv_container = ttk.Frame(self.char_frame)
        ttk.Label(self.vv_container, text="Character:").pack(side=tk.LEFT)
        self.vv_speaker_var = tk.StringVar()
        self.vv_speaker_combo = ttk.Combobox(self.vv_container, textvariable=self.vv_speaker_var, width=40, state="readonly")
        self.vv_speaker_combo.pack(side=tk.LEFT, padx=5)

        # 4. Parameters
        params_container = ttk.Frame(main_frame)
        params_container.pack(fill=tk.X, pady=2)
        
        param_frame = ttk.LabelFrame(params_container, text="🎚️ Audio Parameters ([VV]: VOICEVOX only)", padding="2")
        param_frame.pack(fill=tk.X)

        COLOR_COMMON = "#d4edda"
        COLOR_VV = "#cce5ff"
        lbl_speed = tk.Label(param_frame, text="Speed:", bg=COLOR_COMMON, padx=5)
        lbl_speed.grid(row=0, column=0, sticky=tk.W+tk.E, padx=2, pady=2)
        self.speed_var = tk.DoubleVar(value=self.config.get('speed', 1.0))
        tk.Scale(param_frame, from_=0.5, to=2.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.speed_var, showvalue=0, length=120, troughcolor=COLOR_COMMON, bg="#f0f0f0", bd=0).grid(row=0, column=1, padx=5)
        
        lbl_vol = tk.Label(param_frame, text="Volume:", bg=COLOR_COMMON, padx=5)
        lbl_vol.grid(row=0, column=2, sticky=tk.W+tk.E, padx=2, pady=2)
        self.volume_var = tk.DoubleVar(value=self.config.get('volume', 1.0))
        tk.Scale(param_frame, from_=0.0, to=2.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.volume_var, showvalue=0, length=120, troughcolor=COLOR_COMMON, bg="#f0f0f0", bd=0).grid(row=0, column=3, padx=5)

        lbl_pitch = tk.Label(param_frame, text="Pitch [VV]:", bg=COLOR_VV, padx=5)
        lbl_pitch.grid(row=1, column=0, sticky=tk.W+tk.E, padx=2, pady=2)
        self.pitch_var = tk.DoubleVar(value=self.config.get('pitch', 0.0))
        self.pitch_scale = tk.Scale(param_frame, from_=-0.15, to=0.15, resolution=0.01, orient=tk.HORIZONTAL, variable=self.pitch_var, showvalue=0, length=120, troughcolor=COLOR_VV, bg="#f0f0f0", bd=0)
        self.pitch_scale.grid(row=1, column=1, padx=5)

        lbl_int = tk.Label(param_frame, text="Intonation [VV]:", bg=COLOR_VV, padx=5)
        lbl_int.grid(row=1, column=2, sticky=tk.W+tk.E, padx=2, pady=2)
        self.intonation_var = tk.DoubleVar(value=self.config.get('intonation', 1.0))
        self.intonation_scale = tk.Scale(param_frame, from_=0.0, to=2.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.intonation_var, showvalue=0, length=120, troughcolor=COLOR_VV, bg="#f0f0f0", bd=0)
        self.intonation_scale.grid(row=1, column=3, padx=5)

        silence_frame = ttk.LabelFrame(params_container, text="🔇 Silence Settings (sec)", padding="2")
        silence_frame.pack(fill=tk.X, pady=2)
        ttk.Label(silence_frame, text="Start:").pack(side=tk.LEFT, padx=2)
        self.pre_silence_var = tk.DoubleVar(value=self.config.get('pre_silence', 0.1))
        ttk.Entry(silence_frame, textvariable=self.pre_silence_var, width=4).pack(side=tk.LEFT)
        ttk.Label(silence_frame, text="End:").pack(side=tk.LEFT, padx=5)
        self.post_silence_var = tk.DoubleVar(value=self.config.get('post_silence', 0.1))
        ttk.Entry(silence_frame, textvariable=self.post_silence_var, width=4).pack(side=tk.LEFT)
        ttk.Label(silence_frame, text="Punctuation:").pack(side=tk.LEFT, padx=5)
        self.punctuation_silence_var = tk.DoubleVar(value=self.config.get('punctuation_silence', 0.3))
        ttk.Entry(silence_frame, textvariable=self.punctuation_silence_var, width=4).pack(side=tk.LEFT)

        # 5. Text Input
        text_frame = ttk.LabelFrame(main_frame, text="📝 Text Input", padding="2")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        tool_frame = ttk.Frame(text_frame)
        tool_frame.pack(fill=tk.X)
        
        ttk.Button(tool_frame, text="📂 Load", command=self.load_text_file, width=8).pack(side=tk.LEFT)
        tk.Button(tool_frame, text="🗑️ Clear", command=self.clear_text_input, bg="#dc3545", fg="white", font=("", 8, "bold"), relief=tk.RAISED, width=8).pack(side=tk.LEFT, padx=10)
        
        self.text_input = scrolledtext.ScrolledText(text_frame, width=60, height=5)
        self.text_input.pack(fill=tk.BOTH, expand=True)

        # 6. Output Settings
        output_frame = ttk.LabelFrame(main_frame, text="💾 Output Settings", padding="5")
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Output Dir:").grid(row=0, column=0, sticky=tk.W, padx=5)
        default_output = self.config.get('output_dir', str(self.app_data / 'outputs'))
        self.output_dir_var = tk.StringVar(value=default_output)
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=30).grid(row=0, column=1, padx=5, columnspan=2, sticky=tk.W+tk.E)
        
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir, width=7).grid(row=0, column=3, padx=2)
        ttk.Button(output_frame, text="Open", command=self.open_output_dir, width=5).grid(row=0, column=4, padx=2)
        
        ttk.Label(output_frame, text="Format:").grid(row=0, column=5, sticky=tk.W, padx=10)
        self.format_var = tk.StringVar(value=self.config.get('format', 'wav'))
        ttk.Combobox(output_frame, textvariable=self.format_var, values=['wav', 'mp3'], width=5, state="readonly").grid(row=0, column=6, sticky=tk.W, padx=2)

        ttk.Label(output_frame, text="Prefix:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.prefix_var = tk.StringVar(value=self.config.get('prefix', 'voice'))
        ttk.Entry(output_frame, textvariable=self.prefix_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(output_frame, text="Seq Digits:").grid(row=1, column=2, sticky=tk.E, padx=2)
        self.seq_digits_var = tk.IntVar(value=self.config.get('seq_digits', 3))
        ttk.Spinbox(output_frame, from_=1, to=10, textvariable=self.seq_digits_var, width=3).grid(row=1, column=3, sticky=tk.W, padx=2)

        ttk.Label(output_frame, text="Naming Rule:").grid(row=2, column=0, sticky=tk.W, padx=5)
        # ★Default changed for EN
        self.filename_pattern_var = tk.StringVar(value=self.config.get('filename_pattern', '{ID}_{Prefix}_{Seq}'))
        self.pattern_entry = ttk.Entry(output_frame, textvariable=self.filename_pattern_var)
        self.pattern_entry.grid(row=2, column=1, columnspan=5, sticky=tk.W+tk.E, padx=5)
        
        tag_frame = ttk.Frame(output_frame)
        tag_frame.grid(row=3, column=1, columnspan=5, sticky=tk.W, pady=2)
        
        def add_tag(tag):
            self.pattern_entry.insert(tk.INSERT, tag)
            
        ttk.Label(tag_frame, text="Insert Tags:", font=("", 8), foreground="gray").pack(side=tk.LEFT, padx=(5,5))
        # Updated tags for EN
        ttk.Button(tag_frame, text="+Text(7)", command=lambda: add_tag("{Text}"), width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(tag_frame, text="+ID", command=lambda: add_tag("{ID}"), width=5).pack(side=tk.LEFT, padx=1)
        ttk.Button(tag_frame, text="+Date", command=lambda: add_tag("{Date}"), width=6).pack(side=tk.LEFT, padx=1)
        ttk.Button(tag_frame, text="+Prefix", command=lambda: add_tag("{Prefix}"), width=9).pack(side=tk.LEFT, padx=1)
        ttk.Button(tag_frame, text="+Seq", command=lambda: add_tag("{Seq}"), width=6).pack(side=tk.LEFT, padx=1)

        # 7. Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        self.generate_button = tk.Button(button_frame, text="🎵 Start Generation", command=self.generate_voice, bg="#28a745", fg="white", font=("", 12, "bold"), padx=15, pady=5, relief=tk.RAISED, cursor="hand2")
        self.generate_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = tk.Button(button_frame, text="⏹️ Stop", command=self.stop_generation, bg="#dc3545", fg="white", font=("", 12, "bold"), padx=15, pady=5, relief=tk.RAISED, cursor="hand2", state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Reset Config", command=self.reset_settings).pack(side=tk.LEFT, padx=5)

        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.update_ui_state()

    def open_samples_dir(self):
        if not self.samples_dir.exists(): self.samples_dir.mkdir()
        if platform.system() == "Windows": os.startfile(self.samples_dir)
        elif platform.system() == "Darwin": subprocess.Popen(["open", self.samples_dir])
        else: subprocess.Popen(["xdg-open", self.samples_dir])

    def open_output_dir(self):
        path = Path(self.output_dir_var.get())
        if not path.exists(): path.mkdir(parents=True, exist_ok=True)
        if platform.system() == "Windows": os.startfile(path)
        elif platform.system() == "Darwin": subprocess.Popen(["open", path])
        else: subprocess.Popen(["xdg-open", path])

    def reconnect_voicevox_async(self):
        self.voicevox_status_label.config(text="VOICEVOX: Reconnecting...", foreground="orange")
        threading.Thread(target=self._reconnect_voicevox, daemon=True).start()

    def _reconnect_voicevox(self):
        try:
            requests.get(f"{self.voicevox_server_url}/version", timeout=2)
            self.root.after(0, lambda: self.voicevox_status_label.config(text="VOICEVOX: Connected", foreground="green"))
            self.root.after(0, self.refresh_voicevox_speakers)
            self.root.after(0, lambda: messagebox.showinfo("Success", "Connected to VOICEVOX Engine!"))
        except:
            self.root.after(0, lambda: self.voicevox_status_label.config(text="VOICEVOX: Disconnected", foreground="red"))

    def update_ui_state(self):
        engine = self.engine_var.get()
        if engine == 'voicevox':
            self.vv_container.pack(fill=tk.X, expand=True)
            self.coqui_container.grid_forget()
            self.pitch_scale.config(state='normal', fg='black')
            self.intonation_scale.config(state='normal', fg='black')
        else:
            self.vv_container.pack_forget()
            self.coqui_container.pack(fill=tk.X, expand=True)
            self.pitch_scale.config(state='disabled', fg='gray')
            self.intonation_scale.config(state='disabled', fg='gray')
            if not self.coqui_speaker_combo['values']:
                self.refresh_coqui_speakers()

    def refresh_voicevox_speakers(self):
        self.voicevox_speakers = self.get_voicevox_speakers()
        speaker_values = [f"{s['name']} (ID: {s['id']})" for s in self.voicevox_speakers]
        self.vv_speaker_combo['values'] = speaker_values
        if self.voicevox_speakers:
            self.vv_speaker_combo.current(0)

    def refresh_coqui_speakers(self):
        options = []
        if self.samples_dir.exists():
            files = list(self.samples_dir.glob("*.wav")) + list(self.samples_dir.glob("*.mp3"))
            options = [f.name for f in files]
        if not options: options = ["(Sample folder is empty)"]
        self.coqui_speaker_combo['values'] = options
        
        default_target = "de_female_official.wav"
        if default_target in options: self.coqui_speaker_combo.current(options.index(default_target))
        else: self.coqui_speaker_combo.current(0)

    def get_first_7_chars(self, text):
        clean_text = text.replace('\n', '').replace('\r', '').replace(' ', '').replace('　', '')
        return clean_text[:7] if len(clean_text) >= 7 else clean_text.ljust(7, '_')

    def load_text_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.text_input.delete(1.0, tk.END)
                self.text_input.insert(1.0, f.read())

    def reset_settings(self):
        self.speed_var.set(1.0)
        self.pitch_var.set(0.0)
        self.intonation_var.set(1.0)
        self.volume_var.set(1.0)
        self.pre_silence_var.set(0.1)
        self.post_silence_var.set(0.1)
        self.punctuation_silence_var.set(0.3)
        self.status_bar.config(text="Settings reset")

    def clear_text_input(self):
        if messagebox.askyesno("Confirm", "Clear text?"):
            self.text_input.delete(1.0, tk.END)

    def stop_generation(self):
        self.generation_stop_flag = True
        self.status_bar.config(text="⏹️ Stopping...")

    def generate_voice(self):
        text = self.text_input.get(1.0, tk.END).strip()
        if not text: return
        if self.engine_var.get() == 'coqui' and not self.coqui_enabled:
            messagebox.showwarning("Busy", "Coqui TTS is initializing.")
            return
        
        segments = [s.strip() for s in text.split('\n\n') if s.strip()]
        self.generation_stop_flag = False
        self.generate_button.config(state='disabled', text="🎵 Generating...")
        self.stop_button.config(state='normal')
        threading.Thread(target=self._generate_voice_async, args=(segments,), daemon=True).start()

    def generate_filename(self, speaker_id, index, extension, text="", engine="VOICEVOX"):
        pattern = self.filename_pattern_var.get()
        if not pattern: pattern = "{ID}_{Prefix}_{Seq}"
        
        prefix = self.prefix_var.get()
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        first_7 = self.get_first_7_chars(text)
        
        digits = self.seq_digits_var.get()
        seq_str = str(index).zfill(digits)
        
        if engine == "CoquiTTS": chara_id = "CQ"
        else: chara_id = f"{speaker_id:03d}"
        
        # ★Fix: Replace EN Tags
        fname = pattern.replace("{Text}", first_7)
        fname = fname.replace("{ID}", f"ID{chara_id}")
        fname = fname.replace("{Date}", timestamp)
        fname = fname.replace("{Prefix}", prefix)
        fname = fname.replace("{Seq}", seq_str)
        
        return f"{fname}.{extension}"

    def _generate_voice_async(self, segments):
        try:
            output_dir = Path(self.output_dir_var.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            speed = self.speed_var.get()
            volume = self.volume_var.get()
            pre_sil = self.pre_silence_var.get()
            post_sil = self.post_silence_var.get()
            ext = self.format_var.get()
            
            self.root.after(0, lambda: self._show_progress_dialog(len(segments)))
            
            count = 0
            for i, seg in enumerate(segments, 1):
                if self.generation_stop_flag: break
                
                self.root.after(0, lambda p=int((i-1)/len(segments)*100), c=i: self._update_progress(p, f"Generating: {c}/{len(segments)}"))
                
                if self.engine_var.get() == 'coqui':
                    wav = self.run_coqui(seg, speed)
                    engine_name = "CoquiTTS"
                else:
                    wav = self.run_voicevox(seg)
                    engine_name = "VOICEVOX"
                
                audio = self.post_process_audio(wav, volume, pre_sil, post_sil)
                fname = self.generate_filename(self.get_speaker_id(), i, ext, seg, engine_name)
                
                if ext == "mp3": audio.export(output_dir / fname, format="mp3", bitrate="192k")
                else: audio.export(output_dir / fname, format="wav")
                count += 1
            
            self.root.after(0, lambda: self._update_progress(100, "Done!"))
            self.root.after(0, lambda: self._on_generation_complete(count, len(segments), output_dir))
        except Exception as e:
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self.generate_button.config(state='normal', text="🎵 Start Generation"))
            self.root.after(0, lambda: self.stop_button.config(state='disabled'))
            self.root.after(0, self._close_progress_dialog)
            self.root.after(0, self.save_config)

    def _show_progress_dialog(self, total):
        self.progress_dialog = tk.Toplevel(self.root)
        self.progress_dialog.title("Processing")
        self.progress_dialog.geometry("400x120")
        ttk.Label(self.progress_dialog, text="Generating Audio...", font=("", 11)).pack(pady=10)
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(self.progress_dialog, variable=self.progress_var, maximum=100, length=350).pack()
        self.progress_status_var = tk.StringVar()
        ttk.Label(self.progress_dialog, textvariable=self.progress_status_var).pack(pady=5)

    def _update_progress(self, percent, status):
        if hasattr(self, 'progress_var'): self.progress_var.set(percent)
        if hasattr(self, 'progress_status_var'): self.progress_status_var.set(status)
    
    def _close_progress_dialog(self):
        if hasattr(self, 'progress_dialog'): self.progress_dialog.destroy()

    def _on_generation_complete(self, count, total, output_dir):
        msg = f"Complete: {count}/{total} files\nSaved to: {output_dir}"
        messagebox.showinfo("Done", msg)

    def run_coqui(self, text, speed):
        if not self.coqui_model: raise Exception("Engine initializing...")
        fname = self.coqui_speaker_var.get()
        lang = self.language_var.get().split(' - ')[0]
        temp = self.app_data / "temp.wav"
        self.coqui_model.tts_to_file(text=text, speaker_wav=str(self.samples_dir / fname), language=lang, file_path=str(temp), speed=speed)
        with open(temp, 'rb') as f: data = f.read()
        return data

    def run_voicevox(self, text):
        sid = self.get_speaker_id()
        q = requests.post(f"{self.voicevox_server_url}/audio_query?text={urllib.parse.quote(text)}&speaker={sid}").json()
        q['speedScale'] = self.speed_var.get()
        q['volumeScale'] = self.volume_var.get()
        q['pitchScale'] = self.pitch_var.get()
        q['intonationScale'] = self.intonation_var.get()
        return requests.post(f"{self.voicevox_server_url}/synthesis?speaker={sid}", json=q).content

    def post_process_audio(self, wav_bytes, volume, pre, post):
        audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
        if volume != 1.0 and volume > 0:
            import math
            audio = audio + (20 * math.log10(volume))
        if pre > 0: audio = AudioSegment.silent(duration=int(pre*1000)) + audio
        if post > 0: audio = audio + AudioSegment.silent(duration=int(post*1000))
        return audio

    def check_voicevox_connection(self):
        try: requests.get(f"{self.voicevox_server_url}/version", timeout=1)
        except: self.voicevox_status_label.config(text="VOICEVOX: Disconnected", foreground="red")

    def get_voicevox_speakers(self):
        try:
            res = requests.get(f"{self.voicevox_server_url}/speakers")
            return [{'name': f"{s['name']}-{st['name']}", 'id': st['id']} for s in res.json() for st in s['styles']]
        except: return []

    def get_speaker_id(self):
        val = self.vv_speaker_var.get()
        for s in self.voicevox_speakers:
            if f"{s['name']} (ID: {s['id']})" == val: return s['id']
        return 1

    def browse_output_dir(self):
        d = filedialog.askdirectory()
        if d: self.output_dir_var.set(d)

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f: self.config = json.load(f)
        else: self.config = {}

    def save_config(self):
        try:
            self.config = {
                'engine': self.engine_var.get(),
                'speaker_id': self.get_speaker_id(),
                'speed': self.speed_var.get(),
                'pitch': self.pitch_var.get(),
                'intonation': self.intonation_var.get(),
                'volume': self.volume_var.get(),
                'pre_silence': self.pre_silence_var.get(),
                'post_silence': self.post_silence_var.get(),
                'punctuation_silence': self.punctuation_silence_var.get(),
                'output_dir': self.output_dir_var.get(),
                'format': self.format_var.get(),
                'filename_pattern': self.filename_pattern_var.get(),
                'seq_digits': self.seq_digits_var.get(),
                'prefix': self.prefix_var.get(),
                'language': self.language_var.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f: json.dump(self.config, f, indent=2)
        except: pass

    def on_closing(self):
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    root = tk.Tk()
    style = ttk.Style()
    if 'vista' in style.theme_names(): style.theme_use('vista')
    app = VoicevoxCoquiGUI(root)
    try:
        if pyi_splash.is_alive(): pyi_splash.close()
    except NameError: pass
    root.mainloop()
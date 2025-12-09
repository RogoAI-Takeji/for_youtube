"""
RogoAI Voice Studio - 最終完全版 (文字コードエラー修正済み)
CP932で扱えない絵文字を排除し、raw stringを使用してエスケープ警告を解消。
"""
import os
import shutil
from pathlib import Path

# 基本設定
BASE_NAME = "RogoAI_Voice_Studio"
VERSION = "v1.9"
DIST_ROOT = "dist"

# requirements.txt の内容
REQUIREMENTS_CONTENT = """TTS==0.22.0
requests
Pillow
soundfile
librosa
numpy
inflect
pysbd
gruut[de,es,fr]==2.2.3
anyascii
jamo
pypinyin
jieba
mecab-python3
unidic-lite
cutlet
g2pkk
bangla
bnnumerizer
bnunicodenormalizer
transformers==4.33.0
"""

def create_edition(lang):
    """指定された言語(JP/EN)のパッケージを作成"""
    is_jp = (lang == "JP")
    suffix = "JP" if is_jp else "EN"
    app_script = f"rogoai_voice_studio_v1.9_{suffix}_Slim.py"
    
    folder_name = f"{BASE_NAME}_{VERSION}_{suffix}"
    target_dir = os.path.join(DIST_ROOT, folder_name)
    
    print(f"\n>>> [{suffix}版] パッケージ作成開始: {folder_name}")
    
    # 1. フォルダ作成
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir)
    
    # 2. アプリファイルコピー
    if os.path.exists(app_script):
        shutil.copy2(app_script, target_dir)
        print(f"  アプリ本体: {app_script}")
    else:
        print(f"  [警告] {app_script} が見つかりません！")

    # 3. アイコン (あれば)
    if os.path.exists("make_icon"):
        shutil.copytree("make_icon", os.path.join(target_dir, "make_icon"))

# ★追加: FFmpeg (あればコピー)
    if os.path.exists("ffmpeg"):
        print(f"  FFmpegを同梱中...")
        shutil.copytree("ffmpeg", os.path.join(target_dir, "ffmpeg"))

    # 4. requirements.txt 作成
    with open(os.path.join(target_dir, "requirements.txt"), 'w', encoding='utf-8') as f:
        f.write(REQUIREMENTS_CONTENT)

    # 5. バッチファイル作成
    if is_jp:
        # --- JP版バッチ ---
        
        # 1. Pythonインストール案内
        with open(os.path.join(target_dir, "1_Pythonインストール(未導入の方のみ).bat"), 'w', encoding='cp932') as f:
            f.write(r"""@echo off
chcp 65001 >nul
cls
echo ========================================
echo  RogoAI Voice Studio セットアップ
echo          ステップ 1 / 3
echo ========================================
echo.
echo 【確認】
echo   あなたのPCに Python 3.11 は入っていますか？
echo   入っていれば、このステップは不要です！
echo.
echo   次の「2_初回セットアップ」に進んでください。
echo.
echo ----------------------------------------
echo.
echo 【Python 3.11 が全くない場合】
echo.
echo   以下の手順でインストールしてください：
echo.
echo   1. 自動でダウンロードページが開きます
echo.
echo   2. 一番下までスクロールして
echo      「Windows installer (64-bit)」をクリック
echo.
echo   3. ダウンロードしたファイルを実行
echo.
echo   4. 画面真ん中の「Install Now」をクリックするだけ！
echo      (チェックボックスなどはそのままでOKです)
echo.
echo   5. インストール完了まで待つ
echo.
echo ========================================
echo.
echo 準備ができたら何かキーを押してダウンロードページを開きます...
pause
start https://www.python.org/downloads/release/python-3119/
""")

        # 2. 環境構築 (venv)
        with open(os.path.join(target_dir, "2_初回セットアップ(環境構築).bat"), 'w', encoding='cp932') as f:
            f.write(r"""@echo off
cls
echo ========================================
echo  RogoAI Voice Studio セットアップ
echo          ステップ 2 / 3
echo ========================================
echo.
echo 【これから行うこと】
echo.
echo   1. PC内の Python 3.11 を探します
echo   2. 専用環境(venv)を作成します
echo   3. 必要なライブラリを「安全な順序」で入れます
echo.
echo   ※所要時間：20-30分
echo.
pause
echo.

echo [1/5] Python 3.11 を検索中...
echo.

REM pyランチャー優先
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [発見] pyランチャー経由で Python 3.11 を見つけました。
    set PYTHON_CMD=py -3.11
    goto create_venv
)

REM pythonコマンド確認
python --version 2>&1 | find "3.11" >nul
if %errorlevel% equ 0 (
    echo [発見] 標準の python コマンドが 3.11 です。
    set PYTHON_CMD=python
    goto create_venv
)

REM エラー
echo ========================================
echo  エラー: Python 3.11 が見つかりません
echo ========================================
echo.
echo 「1_Pythonインストール.bat」を実行して
echo Python 3.11 をインストールしてください。
echo.
pause
exit /b 1

:create_venv
echo.
echo [2/5] 専用環境(venv)を作成中...
echo.

if exist venv (
    rmdir /s /q venv
)

%PYTHON_CMD% -m venv venv

if %errorlevel% neq 0 (
    echo エラー: 環境の作成に失敗しました。
    pause
    exit /b 1
)

echo 環境作成完了！
echo.
echo [3/5] 基本ライブラリをインストール中 (pydub等)...
echo      ※ここが重要です。GUIの起動に必要なものを先に入れます。
echo.

REM pipアップデート
venv\Scripts\python -m pip install --upgrade pip

REM 重要: pydub, requests, Pillow を先にインストール
venv\Scripts\python -m pip install pydub requests Pillow

if %errorlevel% neq 0 (
    echo エラー: 基本ライブラリのインストールに失敗しました。
    pause
    exit /b 1
)

echo.
echo [4/5] PyTorch (GPU版) をインストール中...
echo      ※サイズが大きいので時間がかかります...
echo.

venv\Scripts\python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

if %errorlevel% neq 0 (
    echo.
    echo  ※GPU版のインストールに失敗しました。CPU版を入れます。
    venv\Scripts\python -m pip install torch torchaudio
)

echo.
echo [5/5] 音声合成エンジン (TTS) をインストール中...
echo      ※これが一番時間がかかります (10-15分)
echo.

venv\Scripts\python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ----------------------------------------------------
    echo  [注意] TTSの一部のインストールに失敗した可能性があります。
    echo  ただし、基本機能は動作する可能性があります。
    echo  一度、起動を試してみてください。
    echo ----------------------------------------------------
    pause
)

echo.
echo ========================================
echo  セットアップ完了！
echo ========================================
echo.
echo 次からは「3_起動.bat」で起動できます。
pause
""")

        # 3. 起動
        with open(os.path.join(target_dir, "3_起動.bat"), 'w', encoding='cp932') as f:
            f.write(f"""@echo off
cd /d "%~dp0"
if not exist venv (
    echo エラー: セットアップが完了していません。
    echo 「2_初回セットアップ.bat」を実行してください。
    pause
    exit /b
)
start "" venv\Scripts\pythonw.exe {app_script}
""")

        # 4. デバッグ起動
        with open(os.path.join(target_dir, "起動_デバッグ(黒画面).bat"), 'w', encoding='cp932') as f:
            f.write(f"""@echo off
cd /d "%~dp0"
if not exist venv (
    echo エラー: セットアップが完了していません。
    echo 「2_初回セットアップ.bat」を実行してください。
    pause
    exit /b
)
echo 起動中... エラーがあれば下に表示されます。
venv\Scripts\python.exe {app_script}
pause
""")
            
        # README (JP)
        with open(os.path.join(target_dir, "README.txt"), 'w', encoding='utf-8-sig') as f:
            f.write(f"""========================================
 {BASE_NAME} {VERSION} ({suffix})
========================================

【使い方】

  1. 「1_Pythonインストール.bat」
     ※既に Python 3.11 が入っている方は【不要】です。

  2. 「2_初回セットアップ.bat」
     初回のみ実行します。
     ・PC内の Python 3.11 を自動で探して使います。
     ・このフォルダ内だけに専用環境を作ります。
     ・GPUがある場合はGPU版をインストールします。

  3. 「3_起動.bat」
     普段はこれをダブルクリックして起動します。

【トラブルシューティング】
  ・起動しない場合は「起動_デバッグ(黒画面).bat」を実行してください。
    エラーメッセージが表示されます。

  ・初回起動時はAIモデルのダウンロードに時間がかかります。

【開発者】
  Takejii (RogoAI)
========================================
""")

    else:
        # --- EN版バッチ (英語) ---
        
        # 1. Install Python (Simple)
        with open(os.path.join(target_dir, "1_Install_Python.bat"), 'w', encoding='ascii') as f:
            f.write("""@echo off
cls
echo ========================================
echo  RogoAI Voice Studio Setup
echo          STEP 1 / 3
echo ========================================
echo.
echo  [CHECK]
echo  Do you already have Python 3.11 installed?
echo  If YES, you can SKIP this step.
echo.
echo  Please proceed to "2_Setup_Environment".
echo.
echo ----------------------------------------
echo.
echo  [If you DON'T have Python 3.11]
echo.
echo  1. The download page will open automatically
echo.
echo  2. Scroll down and click "Windows installer (64-bit)"
echo.
echo  3. Run the installer
echo.
echo  4. Just click "Install Now" (No need to check boxes)
echo.
echo ========================================
pause
start https://www.python.org/downloads/release/python-3119/
""")

        # 2. Setup Env (Ordered)
        with open(os.path.join(target_dir, "2_Setup_Environment.bat"), 'w', encoding='ascii') as f:
            f.write("""@echo off
cls
echo ========================================
echo  RogoAI Voice Studio Setup
echo          STEP 2 / 3
echo ========================================
echo.
echo  1. Searching for Python 3.11 on your PC...
echo  2. Creating dedicated environment (venv)...
echo  3. Installing libraries in SAFE ORDER...
echo.
echo   *Estimated time: 20-30 mins
echo.
pause
echo.

echo [1/5] Searching for Python 3.11...
echo.

REM Method 1: py launcher
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [Found] Python 3.11 via py launcher.
    set PYTHON_CMD=py -3.11
    goto create_venv
)

REM Method 2: python command
python --version 2>&1 | find "3.11" >nul
if %errorlevel% equ 0 (
    echo [Found] Default python command is 3.11.
    set PYTHON_CMD=python
    goto create_venv
)

echo ========================================
echo  ERROR: Python 3.11 not found
echo ========================================
echo.
echo Please run "1_Install_Python.bat".
echo.
pause
exit /b 1

:create_venv
echo.
echo [2/5] Creating venv...
echo.

if exist venv (
    rmdir /s /q venv
)

%PYTHON_CMD% -m venv venv

if %errorlevel% neq 0 (
    echo ERROR: Failed to create environment.
    pause
    exit /b 1
)

echo.
echo [3/5] Installing Basic Libraries (pydub, requests...)...
echo.

venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install pydub requests Pillow

if %errorlevel% neq 0 (
    echo ERROR: Failed to install basic libraries.
    pause
    exit /b 1
)

echo.
echo [4/5] Installing PyTorch (GPU version)...
echo.

venv\Scripts\python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

if %errorlevel% neq 0 (
    echo.
    echo  *GPU install failed. Trying CPU version...
    venv\Scripts\python -m pip install torch torchaudio
)

echo.
echo [5/5] Installing TTS Engine...
echo      (This takes time...)
echo.

venv\Scripts\python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ----------------------------------------------------
    echo  WARNING: TTS installation had issues.
    echo  However, the app might still work.
    echo  Please try launching it.
    echo ----------------------------------------------------
    pause
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo You can now run "3_Start.bat".
pause
""")

        # 3. Start
        with open(os.path.join(target_dir, "3_Start.bat"), 'w', encoding='ascii') as f:
            f.write(f'@echo off\ncd /d "%~dp0"\nif not exist venv (\n  echo Please run 2_Setup_Environment.bat first.\n  pause\n  exit /b\n)\nstart "" venv\Scripts\pythonw.exe {app_script}\n')

        # 4. Debug Start
        with open(os.path.join(target_dir, "Start_Debug.bat"), 'w', encoding='ascii') as f:
            f.write(f'@echo off\ncd /d "%~dp0"\nif not exist venv (\n  echo Please run 2_Setup_Environment.bat first.\n  pause\n  exit /b\n)\necho Launching...\nvenv\Scripts\python.exe {app_script}\npause\n')

        # README (EN)
        with open(os.path.join(target_dir, "README.txt"), 'w', encoding='utf-8') as f:
            f.write(f"""========================================
 {BASE_NAME} {VERSION} ({suffix})
========================================

[INSTRUCTIONS]

  1. Run "1_Install_Python.bat"
     (Only if you don't have Python 3.11 installed)

  2. Run "2_Setup_Environment.bat"
     (Run once. Takes 20-30 mins)
     *Automatically finds Python 3.11.
     *Creates a dedicated environment here.

  3. Run "3_Start.bat"
     (Double-click to launch app)

[TROUBLESHOOTING]
  - If app doesn't start, run "Start_Debug.bat" to see errors.
  - First launch takes time to download AI models.

[DEVELOPER]
  Takejii (RogoAI)
========================================
""")

    print(f"  ✅ {suffix}版 作成完了")
    return target_dir

def main():
    print("="*60)
    print(f"  {BASE_NAME} 配布パッケージ作成ツール (文字化け修正版)")
    print("="*60)

    # 1. JP版の作成
    create_edition("JP")

    # 2. EN版の作成
    create_edition("EN")
    
    print("\n" + "="*60)
    print("  🎉 全工程完了！ distフォルダを確認してください")
    print("="*60)

if __name__ == "__main__":
    main()
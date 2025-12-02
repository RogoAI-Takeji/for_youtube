\# Metadata Scan \& Clean



画像・動画・音声ファイルに含まれる  

GPS・EXIF・Author 情報・AI生成プロンプトなどの  

危険なメタデータを自動検知し、一括削除する Windows ツールです。



!\[Version](https://img.shields.io/badge/version-1.0.0-blue.svg)

!\[License](https://img.shields.io/badge/license-MIT-green.svg)



---



\## 概要 (Overview)



このアプリは、指定したフォルダ内の画像・動画をスキャンし、  

プライバシーリスクとなるメタデータ（GPS 位置情報、Exif、AI生成情報など）を検出し、安全にクリーニングします。



SNS 共有、ブログ掲載、AI生成画像の公開前の  

\*\*「最終セキュリティチェック」\*\* として最適です。



---



\## 特徴 (Features)



\### ⭐ AI生成メタデータへの対応（最大の特徴）

一般的な EXIF 削除ツールでは除去できない  

\*\*ComfyUI / Stable Diffusion / WebUI が生成するプロンプト・ワークフロー情報\*\* を検知し、削除できます。



例（AI生成メタデータ内部）:



```json

{

&nbsp; "prompt": "...",

&nbsp; "negative\_prompt": "...",

&nbsp; "workflow": "{...}",

&nbsp; "seed": 12345

}

```



これらが公開されると  

\*\*制作手法・環境・プロンプトなどが第三者に漏洩します。\*\*



---



\### ⭐ 基本のメタデータ削除



\- GPS 位置情報（Location）

\- 撮影者情報（Author）

\- 撮影日時・カメラ機種（EXIF）

\- 著作権情報（Copyright）



---



\### ⭐ 2つのクリーニングモード



\- \*\*スマート削除（推奨）\*\*  

&nbsp; 画質を劣化させず、メタデータのみを安全に除去します。



\- \*\*完全削除（最強）\*\*  

&nbsp; 再エンコードにより、すべての付加情報・履歴を完全除去します。



---



\## 使い方 (Usage)



1\. \*\*起動\*\*  

&nbsp;  `Metadata\_Scan\_Clean.exe` を実行します。



2\. \*\*フォルダ選択\*\*  

&nbsp;  「参照」ボタンから処理したいフォルダを選びます。



3\. \*\*スキャン\*\*  

&nbsp;  「🔍 スキャン」で危険なメタデータを含むファイル一覧が表示されます。  

&nbsp;  - 🔴 赤：GPS など重大情報  

&nbsp;  - 🟡 黄：AI生成情報など



4\. \*\*クリーニング実行\*\*  

&nbsp;  「✨ 実行」を押すと、安全なファイルが  

&nbsp;  \*\*元フォルダを絶対に上書きせず、必ず `\_clean` フォルダに出力されます。\*\*



これにより、誤操作でも元ファイルが失われません。



---



\## ダウンロード (Download)



最新バージョンは GitHub の \*\*Releases\*\* から取得できます：  

👉 <https://github.com/RogoAI-Takeji/for\_youtube/releases>



\- 🇯🇵 日本語版（JP UI）  

\- 🇬🇧 英語版（EN UI）  

\- ZIP版（インストール不要）  

\- ソースコード版（src/）



を提供しています。



※ \*\*ZIP を解凍して `.exe` を実行するだけで使えます。\*\*  

※ 日本語版と英語版は内部ランタイム構成が同一のため、容量はほぼ同じです。



---



\## 動作環境 (Requirements)



\### EXE 版（通常はこちら）

\- Windows 10 / 11（64bit）

\- Python 不要

\- FFmpeg 不要（内部処理にバンドル済み）



\### ソースコード版（src/）

\- Python 3.x  

\- Pillow / piexif / ffmpeg-python  

\- FFmpeg（動画処理を行う場合）



---



\## よくある質問 (FAQ)



\### Q. EXE 版は安全ですか？

A. ソースコード（MIT License）をすべて公開しているため、内容を確認した上で利用できます。



\### Q. GPS 情報は完全に削除されますか？

A. ファイル内部から削除しますが、投稿先プラットフォームが再生成する場合があります。  

&nbsp;  投稿前の最終確認はご自身でお願いします。



---



\## 免責事項 (Disclaimer)



\- 本アプリはプライバシー保護を支援する目的のツールです。  

&nbsp; \*\*あらゆる情報の完全削除を保証するものではありません。\*\*

\- SNS・共有サービスへの投稿前には最終確認をお願いします。

\- 本ソフトウェアの利用により発生した損害について、作者は責任を負いません。



---



\## ライセンス (License)



このソフトウェアは \*\*MIT License\*\* で公開されています。  

詳細は \[LICENSE](LICENSE) を参照してください。



---



\## 作者 (Author)



\*\*RogoAI-Takeji\*\*  



\- YouTube: <https://www.youtube.com/@老後AI>  

\- GitHub: <https://github.com/RogoAI-Takeji>  



App ID: `takejii\_app\_001`




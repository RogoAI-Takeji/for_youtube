\# Metadata Scan \& Clean



画像・動画ファイルのメタデータ（個人情報や AI 生成パラメータ）を安全に検知し、削除するための Windows デスクトップアプリです。



!\[Version](https://img.shields.io/badge/version-1.9.6-blue.svg)

!\[License](https://img.shields.io/badge/license-MIT-green.svg)



---



\## 概要 (Overview)

このアプリは、指定したフォルダ内の画像・動画をスキャンし、プライバシーリスクとなるメタデータ（GPS 位置情報・Exif 情報・撮影者情報・AI生成プロンプトなど）を検出し、安全な状態にクリーニングします。



SNS投稿、共有、動画制作、ブログ掲載の前の「最終セキュリティチェック」に最適です。



---



\## 特徴 (Features)



\### ⭐ AI生成メタデータへの対応（本アプリ最大の特徴）

一般的な EXIF 削除ツールでは落としきれない、  

\*\*ComfyUI / Stable Diffusion / WebUI などの AI 生成物に含まれるプロンプト・ワークフロー情報\*\* を検知し、削除します。



例（AI生成画像の内部メタデータ）：



{

"prompt": "...",

"negative\_prompt": "...",

"seed": 12345,

"workflow": "{...}",

...

}



これらは SNS やブログにアップすると、  

\*\*個人の制作手法やデータがそのまま流出する危険\*\*があります。



---



\### ⭐ 基本のメタデータ削除

\- GPS 位置情報（Location）

\- 撮影者情報（Author）

\- 撮影日時・カメラ機種（EXIF）

\- 著作権情報（Copyright）



\### ⭐ 2つのクリーニングモード

\- \*\*スマート削除（推奨）\*\*  

&nbsp; 画質を劣化させず、メタデータのみを安全に除去します。



\- \*\*完全削除（最強）\*\*  

&nbsp; 再エンコードを行い、すべての付加情報を根こそぎ削除します。



---



\## 使い方 (Usage)



1\. \*\*起動\*\*  

&nbsp;  `Metadata\_Scan\_Clean.exe` を実行します。



2\. \*\*フォルダ選択\*\*  

&nbsp;  「参照」ボタンから対象フォルダを指定します。



3\. \*\*スキャン\*\*  

&nbsp;  「🔍 スキャン」で、危険なメタデータを含むファイル一覧が生成されます。  

&nbsp;  - 🔴 赤：GPS などの重大情報  

&nbsp;  - 🟡 黄：AI生成情報や一般メタデータ  



4\. \*\*クリーニング実行\*\*  

&nbsp;  「✨ 実行」で、安全なファイルを  

&nbsp;  \*\*元フォルダを上書きせず、必ず `\_clean` フォルダに出力\*\*します。



これにより、万が一の誤操作でも元データは守られます。



---



\## ダウンロード (Download)



最新バージョンは GitHub の \*\*Releases\*\* から取得できます。



👉 <https://github.com/RogoAI-Takeji/for\_youtube/releases>



\- JP版（日本語UI）

\- EN版（英語UI）

\- ZIP版（インストール不要）

\- ソースコード版



を用意しています。



---



\## 動作環境 (Requirements)



\### EXE 版

\- Python 不要  

\- FFmpeg 不要  

\- Windows 10 / 11（64bit）



\### ソースコード版（src/）

\- Python 3.x  

\- Pillow / piexif / ffmpeg-python  

\- FFmpeg（動画クリーニングをする場合のみ必須）



---



\## よくある質問 (FAQ)



\### Q. EXE 版は安全ですか？

A. ソースコードをすべて公開しているため、

　 内容を確認しながらご利用いただけます。



\### Q. 位置情報は完全に削除できますか？

A. GPS / Exif 情報は除去しますが、  

　 SNS側で再生成される場合があります。  

　 最終確認は投稿前にお願いします。



---



\## 免責事項 (Disclaimer)

\- 本アプリはプライバシー保護を支援するものですが、  

&nbsp; \*\*あらゆる情報の完全削除を保証するものではありません。\*\*

\- SNS へ投稿する際は、最終チェックを利用者自身が行ってください。

\- 本ソフトの使用によって発生した損害について、  

&nbsp; 作者は責任を負いません。



---



\## ライセンス (License)

このソフトウェアは \*\*MIT License\*\* の下で公開されています。  

詳細は \[LICENSE](LICENSE) をご確認ください。



---



\## 作者 (Author)

\*\*RogoAI-Takeji\*\*



\- YouTube: <https://www.youtube.com/@老後AI>

\- GitHub: <https://github.com/RogoAI-Takeji>



アプリID: `takejii\_app\_001`


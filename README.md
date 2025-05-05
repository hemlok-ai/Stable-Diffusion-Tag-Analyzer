# 🏷️ Stable Diffusion Tag Analyzer

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Gradio](https://img.shields.io/badge/Gradio-UI-green) ![License](https://img.shields.io/badge/License-MIT-yellow) ![HuggingFace](https://img.shields.io/badge/Deploy-HF_Space-orange)

> Stable Diffusion向け追加学習素材の「タグ」を集計・可視化するツールです。

---

## ✨ 機能概要

- 素材画像に対応する`.txt`ファイルからタグを抽出
- 出現回数を集計しランキング表示
- 除外タグの指定も可能(LoRA指定タグ等)
- CSV / Markdown / JSONのログ出力対応
- 既存ログの読み込み・可視化も可能
- スタンドアロンで動作

---

## 🚀 使用方法

### 1. 起動（ローカル）

```bash
git clone https://github.com/hemlok-ai/Stable-Diffusion-Tag-Analyzer.git
cd Stable-Diffusion-Tag-Analyzer

python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

ブラウザが開いてUIが起動します。

---

## 📄 ライセンス

MIT License

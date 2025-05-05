import os
import glob
import json
import gradio as gr
import pandas as pd
import plotly.express as px
from collections import Counter
from PIL import Image
from datetime import datetime
import base64
from io import BytesIO

# 画像とテキストのペア処理関数
def process_directory(directory, exclude_tags_str):
    try:
        exclude_tags = set(tag.strip() for tag in exclude_tags_str.split(",") if tag.strip())
        tag_counter = Counter()
        file_tags = {}

        image_files = glob.glob(os.path.join(directory, "*.png")) + glob.glob(os.path.join(directory, "*.jpg"))

        for img_path in image_files:
            base, _ = os.path.splitext(img_path)
            txt_path = base + ".txt"
            tags = []
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    tags = [tag.strip() for tag in f.read().split(",") if tag.strip() and tag.strip() not in exclude_tags]
                    tag_counter.update(tags)
            file_tags[os.path.basename(img_path)] = tags # テキストファイルがない場合もファイル名のみ含める

        tag_df = pd.DataFrame(tag_counter.items(), columns=["Tag", "Count"]).sort_values("Count", ascending=False)

        # 統計
        total_tags = sum(tag_counter.values())
        unique_tags = len(tag_counter)
        avg = total_tags / unique_tags if unique_tags > 0 else 0

        # 最頻出タグの文字列を別途生成
        most_common_tag_str = "なし"
        if not tag_df.empty:
             most_common_tag = tag_df.iloc[0]
             most_common_tag_str = f"**{most_common_tag['Tag']}**（{most_common_tag['Count']}回）"


        summary = f"""
        ### 📊 基本統計情報
        - 総タグ数: **{total_tags}**
        - ユニークタグ数: **{unique_tags}**
        - 平均出現回数: **{avg:.2f}**
        - 最頻出タグ: {most_common_tag_str}
        """

        # グラフ
        if not tag_df.empty:
            fig = px.bar(tag_df.head(30), x="Tag", y="Count", title="タグ出現数ランキング（上位30件）")
            hist = px.histogram(tag_df, x="Count", nbins=20, title="タグ出現数の分布")
        else:
            fig = None
            hist = None


        # ログ出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # CSV出力
        csv_path = os.path.join(log_dir, f"tag_log_{timestamp}.csv")
        tag_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        # Markdown出力
        md_path = os.path.join(log_dir, f"tag_summary_{timestamp}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(summary) # summaryの内容をファイルに書き込む

        # metadata.json出力
        json_path = os.path.join(log_dir, f"metadata_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(file_tags, f, ensure_ascii=False, indent=2)

        # ログファイルのパスを返す
        return tag_df, fig, hist, summary, csv_path, md_path, json_path

    except Exception as e:
        import traceback
        error_msg = f"エラー: {str(e)}\n{traceback.format_exc()}"
        return pd.DataFrame(), None, None, error_msg, None, None, None # エラー時はNoneを返す

# ログ読み込み用 (CSV)
def load_log_csv(csv_file):
    if csv_file is None:
        return pd.DataFrame(), None
    try:
        df = pd.read_csv(csv_file.name)
        fig = px.bar(df.head(30), x="Tag", y="Count", title="[ログ] タグ出現数ランキング")
        return df, fig
    except Exception as e:
        return pd.DataFrame(), None


# UI
with gr.Blocks(css="""
    body { padding: 3em !important; }
    .gradio-container { max-width: 1200px; margin: auto; } /* 全体の最大幅と中央寄せ */
    .gradio-row { gap: 1em; } /* Row間の隙間 */
    .gradio-column { gap: 1em; } /* Column間の隙間 */
    .gr-dataframes { width: 100% !important; } /* Dataframeの幅を調整 */
""") as demo: 
    gr.Markdown("# 📒 StableDiffusion素材 タグ管理ツール")

    with gr.Tabs():
        with gr.TabItem("素材解析"):
            gr.Markdown("## 🏷️ タグ集計と基本統計")

            with gr.Row():
                directory_input = gr.Textbox(label="素材ディレクトリパス", placeholder="例: /path/to/your/images")
                exclude_input = gr.Textbox(label="除外タグ（カンマ区切り）", placeholder="例: masterpiece, best quality", scale=0.5) # 幅を調整

            run_btn = gr.Button("集計開始")

            with gr.Row():
                with gr.Column(scale=1):
                    stat_output = gr.Markdown("") # 統計情報を左カラムに
                with gr.Column(scale=2):
                    tag_table = gr.Dataframe(headers=["Tag", "Count"], label="タグカウント結果", interactive=False)
            with gr.Column(): # グラフは縦に並べる
                plot_output = gr.Plot(label="タグ出現数ランキング（上位30件）")
                hist_output = gr.Plot(label="タグ出現数の分布")

            # ログファイルのダウンロードリンクを表示する出力 (Markdownもgr.Fileに戻す)
            log_csv_file = gr.File(label="CSVログ ダウンロード", file_count="single", visible=False)
            log_md_file = gr.File(label="Markdownサマリー ダウンロード", file_count="single", visible=False)
            log_json_file = gr.File(label="metadata.json ダウンロード", file_count="single", visible=False)


            run_btn.click(
                fn=process_directory,
                inputs=[directory_input, exclude_input],
                outputs=[tag_table, plot_output, hist_output, stat_output, log_csv_file, log_md_file, log_json_file]
            ).then( # 処理完了後にログファイルを visible にし、value にパスを設定してダウンロード可能にする
                fn=lambda csv_path, md_path, json_path: {
                    log_csv_file: gr.update(visible=csv_path is not None, value=csv_path if csv_path else None),
                    log_md_file: gr.update(visible=md_path is not None, value=md_path if md_path else None), # valueを設定
                    log_json_file: gr.update(visible=json_path is not None, value=json_path if json_path else None)  # valueを設定
                },
                inputs=[log_csv_file, log_md_file, log_json_file], # .then には直前の出力が自動で渡されるため、inputsは不要
                outputs=[log_csv_file, log_md_file, log_json_file]
            )


        with gr.TabItem("ログ読み込み"):
            gr.Markdown("## 📂 ログファイル読み込み")
            with gr.Row():
                csv_in = gr.File(label="CSVログファイルを選択", file_types=[".csv"])
                load_btn = gr.Button("ログ読込")
            log_table = gr.Dataframe(label="ログファイル内容")
            log_plot = gr.Plot(label="タグランキンググラフ（ログ）")
            load_btn.click(fn=load_log_csv, inputs=csv_in, outputs=[log_table, log_plot])

        # タグ編集タブを削除


if __name__ == "__main__":
    demo.launch()
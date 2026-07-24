from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.parser import parse_band_page


st.set_page_config(page_title="BandPM Collector", page_icon="🎺", layout="wide")

st.title("🎺 BandPM Collector")
st.caption("吹奏楽団の公式サイトから、営業・調査用の基本情報を抽出します。")

url_text = st.text_area(
    "解析するURL",
    height=180,
    placeholder="https://example.com/band-a\nhttps://example.com/band-b",
)

if "results" not in st.session_state:
    st.session_state.results = []

if st.button("解析する", type="primary", use_container_width=True):
    urls = [line.strip() for line in url_text.splitlines() if line.strip()]

    if not urls:
        st.warning("URLを1件以上入力してください。")
    else:
        results: list[dict[str, Any]] = []
        progress = st.progress(0)
        status = st.empty()

        for index, url in enumerate(urls, start=1):
            status.write(f"解析中: {url}")
            try:
                result = parse_band_page(url)
            except Exception as exc:
                result = {
                    "band_name": "",
                    "prefecture": "",
                    "city": "",
                    "website_url": url,
                    "contact_url": "",
                    "contact_email": "",
                    "recruiting": "",
                    "rehearsal": "",
                    "concert_info": "",
                    "source_url": url,
                    "fetched_at": "",
                    "confidence": 0,
                    "notes": f"解析エラー: {exc}",
                }

            results.append(result)
            progress.progress(index / len(urls))

        st.session_state.results = results
        status.success(f"{len(results)}件の解析が完了しました。")

if st.session_state.results:
    st.subheader("解析結果")
    dataframe = pd.DataFrame(st.session_state.results)
    edited_dataframe = st.data_editor(
        dataframe,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
    )

    csv_bytes = edited_dataframe.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")

    st.download_button(
        label="CSVをダウンロード",
        data=csv_bytes,
        file_name="bandpm_collector_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("まだ解析結果はありません。")

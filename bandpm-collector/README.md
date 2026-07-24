# BandPM Collector

アマチュア吹奏楽団の公式サイトから、営業・リサーチに使える基本情報を抽出し、CSVとして保存するローカルWebアプリです。

## 現在のMVP

WebサイトのURLを入力すると、可能な範囲で次の情報を抽出します。

- 団体名
- 都道府県・市区町村候補
- 問い合わせ先URL
- 公開メールアドレス
- 団員募集の有無
- 練習情報
- 演奏会情報
- 情報元URL
- 取得日時

## 必要環境

- Windows 10 / 11
- Python 3.11以上を推奨

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 起動

```bash
streamlit run app.py
```

起動後、通常は次のURLがブラウザで開きます。

```text
http://localhost:8501
```

## 使い方

1. 吹奏楽団の公式サイトURLを1行ずつ入力する
2. 「解析する」を押す
3. 抽出結果を確認・修正する
4. CSVをダウンロードする

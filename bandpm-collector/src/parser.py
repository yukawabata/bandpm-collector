from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (compatible; BandPMCollector/0.1; "
    "+https://github.com/yukawabata/bandpm-collector)"
)

PREFECTURES = [
    "北海道",
    "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県",
    "沖縄県",
]

EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
CITY_PATTERN = re.compile(r"([一-龥ぁ-んァ-ヶー]{1,12}(?:市|区|町|村))")

BAND_NAME_KEYWORDS = (
    "吹奏楽団",
    "ウインドオーケストラ",
    "ウィンドオーケストラ",
    "シンフォニックバンド",
    "ブラスバンド",
    "吹奏楽",
)
CONTACT_KEYWORDS = ("お問い合わせ", "問い合わせ", "contact", "連絡先")
RECRUITING_KEYWORDS = ("団員募集", "メンバー募集", "団員募集中", "入団", "見学")
REHEARSAL_KEYWORDS = ("練習日", "練習場所", "練習時間", "毎週", "隔週", "合奏")
CONCERT_KEYWORDS = ("演奏会", "定期演奏会", "コンサート", "公演", "concert")


def fetch_html(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URLは http:// または https:// から始めてください。")

    response = requests.get(
        url,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type.lower():
        raise RuntimeError(f"HTMLページではありません: {content_type or '不明'}")

    response.encoding = response.apparent_encoding or response.encoding
    return response.text


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_first_prefecture(text: str) -> str:
    return next((item for item in PREFECTURES if item in text), "")


def find_first_city(text: str) -> str:
    match = CITY_PATTERN.search(text)
    return match.group(1) if match else ""


def extract_emails(text: str) -> list[str]:
    return sorted(set(EMAIL_PATTERN.findall(text)))


def link_matches_keyword(
    text: str,
    href: str,
    keywords: Iterable[str],
) -> bool:
    haystack = f"{text} {href}".lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def find_contact_url(soup: BeautifulSoup, base_url: str) -> str:
    for anchor in soup.find_all("a", href=True):
        label = clean_text(anchor.get_text(" ", strip=True))
        href = anchor.get("href", "")
        if link_matches_keyword(label, href, CONTACT_KEYWORDS):
            return urljoin(base_url, href)
    return ""


def extract_relevant_sentence(
    text: str,
    keywords: Iterable[str],
    max_length: int = 220,
) -> str:
    segments = re.split(r"[。\n\r]|(?<=[！？!?])", clean_text(text))
    for segment in segments:
        if any(keyword.lower() in segment.lower() for keyword in keywords):
            return segment[:max_length].strip()
    return ""


def extract_band_name(soup: BeautifulSoup) -> str:
    candidates: list[str] = []

    if soup.title and soup.title.string:
        candidates.append(clean_text(soup.title.string))

    for selector in ("h1", "header h1", ".site-title", ".logo"):
        element = soup.select_one(selector)
        if element:
            candidates.append(clean_text(element.get_text(" ", strip=True)))

    for candidate in candidates:
        if any(keyword in candidate for keyword in BAND_NAME_KEYWORDS):
            return re.split(r"[|｜–—\-]", candidate)[0].strip()[:120]

    return candidates[0][:120] if candidates else ""


def calculate_confidence(result: dict[str, object]) -> int:
    score = 0
    score += 25 if result.get("band_name") else 0
    score += 15 if result.get("prefecture") or result.get("city") else 0
    score += 20 if result.get("contact_url") or result.get("contact_email") else 0
    score += 15 if result.get("recruiting") else 0
    score += 10 if result.get("rehearsal") else 0
    score += 10 if result.get("concert_info") else 0
    score += 5 if result.get("website_url") else 0
    return min(score, 100)


def parse_band_page(url: str) -> dict[str, object]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    page_text = clean_text(soup.get_text(" ", strip=True))
    emails = extract_emails(page_text)

    result: dict[str, object] = {
        "band_name": extract_band_name(soup),
        "prefecture": find_first_prefecture(page_text),
        "city": find_first_city(page_text),
        "website_url": url,
        "contact_url": find_contact_url(soup, url),
        "contact_email": emails[0] if emails else "",
        "recruiting": extract_relevant_sentence(page_text, RECRUITING_KEYWORDS),
        "rehearsal": extract_relevant_sentence(page_text, REHEARSAL_KEYWORDS),
        "concert_info": extract_relevant_sentence(page_text, CONCERT_KEYWORDS),
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "confidence": 0,
        "notes": "",
    }
    result["confidence"] = calculate_confidence(result)
    return result

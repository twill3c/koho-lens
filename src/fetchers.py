"""会社別の取得・抽出(F-01/F-06)。

fetch_company(company, get) -> [{"title","url","date"}...](新しい順)
get(url, ua) -> bytes は注入可能(テストではフィクスチャ、実運用では http_get)。

HTML 抽出は各サイトの安定したマークアップ(class 名・URL パターン)に固定した
正規表現で行う。構造変更で 0 件になった場合は pipeline 側で ok=False として
前回分を保持する(F-05)ため、ここでは例外にしない。
"""

from __future__ import annotations

import re
from html import unescape

from .dates import normalize_date
from .feedparse import parse_feed
from .sources import BROWSER_UA, PROJECT_UA
from .urlutil import absolutize


def _clean(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _https(url: str) -> str:
    return "https://" + url[len("http://") :] if url.startswith("http://") else url


# ---- HTML パーサ(会社別) ----------------------------------------------


def parse_hitachi_json(raw: bytes) -> list[dict]:
    # AEM page_search JSON: searchPagesList[].newsTitle / newsPath / newsPublishDate
    import json as _json

    data = _json.loads(raw.decode("utf-8", "ignore"))
    return [
        {
            "title": _clean(it.get("newsTitle", "")),
            "url": it.get("newsPath", ""),
            "date": normalize_date(it.get("newsPublishDate", "")),
        }
        for it in data.get("searchPagesList", [])
    ]


def parse_nttdata(html: str, base: str) -> list[dict]:
    # 日付ブロックの後に category とリンクが続く。報道発表(release)のみ採る
    pat = re.compile(
        r'class="c-list-news-date-merge__date"[^>]*>([^<]+)</p>.*?'
        r'<a href="(/global/ja/news/[^"]+)">(.*?)</a>',
        re.S,
    )
    items = []
    for date, href, title in pat.findall(html):
        if "/news/release/" not in href:
            continue
        items.append(
            {
                "title": _clean(title),
                "url": absolutize(base, href),
                "date": normalize_date(date),
            }
        )
    return items


def parse_tis(html: str, base: str) -> list[dict]:
    # <li data-date="…"><time datetime="2026-08-19">…</time>…
    # <a href="/news/2026/tisi_news/…">タイトル</a>(ニュースリリースのみ)
    pat = re.compile(
        r'<time datetime="([\d-]+)">[^<]*</time>.*?'
        r'<a href="(/news/\d{4}/tisi_news/[^"]+)"\s*>(.*?)</a>',
        re.S,
    )
    items = []
    for date, href, title in pat.findall(html):
        items.append(
            {
                "title": _clean(title),
                "url": absolutize(base, href),
                "date": normalize_date(date),
            }
        )
    return items


def parse_canon_its(html: str, base: str) -> list[dict]:
    # <span class="date">2026年8月18日</span> … <a href="/corporate/newsrelease/…">…</a>
    pat = re.compile(
        r'<span class="date">([^<]+)</span>.*?'
        r'<a href="(/corporate/newsrelease/[^"]+)">(.*?)</a>',
        re.S,
    )
    items = []
    for date, href, title in pat.findall(html):
        items.append(
            {
                "title": _clean(title),
                "url": absolutize(base, href),
                "date": normalize_date(date),
            }
        )
    return items


def parse_nssol(html: str, base: str) -> list[dict]:
    # digitalpr.jp/c/814: <article><h2><a href="/r/N">…</a></h2>…
    # <li class="postDate">2026年08月19日</li>
    pat = re.compile(
        r'<h2><a href="(/r/\d+)">(.*?)</a></h2>.*?'
        r'<li class="postDate">([^<]+)</li>',
        re.S,
    )
    items = []
    for href, title, date in pat.findall(html):
        items.append(
            {
                "title": _clean(title),
                "url": absolutize(base, href),
                "date": normalize_date(date),
            }
        )
    return items


_HTML_PARSERS = {
    "nttdata": parse_nttdata,
    "tis": parse_tis,
    "canon_its": parse_canon_its,
    "nssol": parse_nssol,
}


# ---- sitemap 戦略(NRI / アクセンチュア) --------------------------------


def _page_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if not m:
        return ""
    return _clean(m.group(1)).split(" | ")[0].strip()


def nri_select(sitemap: str) -> list[tuple[str, str]]:
    """(url, date) を新しい順に。日付は URL の YYYYMMDD。_N 無しはソフト 404 のため除外。

    公式の新着一覧はニュースリリース(/newsrelease/)とお知らせ(/info/)の
    混在なので両区分を対象にする。ディレクトリが異なると URL 辞書順は
    日付順にならないため、日付キーで並べ替える。
    """
    urls = set(
        re.findall(
            r"<loc>(https://www\.nri\.com/jp/news/"
            r"(?:newsrelease|info)/\d{8}_\d+\.html)</loc>",
            sitemap,
        )
    )
    out = []
    for u in urls:
        ymd = re.search(r"/(\d{8})_", u).group(1)
        out.append((u, f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"))
    out.sort(key=lambda t: (t[1], t[0]), reverse=True)
    return out


def accenture_select(sitemap: str) -> list[tuple[str, str]]:
    """(url, lastmod日付) を lastmod 降順に。正確な掲載日は記事ページから取り直す。"""
    entries = re.findall(
        r"<url>\s*<loc>(https://newsroom\.accenture\.jp/jp/news/\d{4}/[^<]+)</loc>"
        r"(?:\s*<lastmod>([^<]+)</lastmod>)?",
        sitemap,
    )
    entries.sort(key=lambda e: e[1], reverse=True)
    return [(u, normalize_date(lm)) for u, lm in entries]


def _fetch_sitemap_items(company, get, ua) -> list[dict]:
    sitemap = get(company["primary_url"], ua).decode("utf-8", "ignore")
    select = nri_select if company["id"] == "nri" else accenture_select
    items = []
    for url, date in select(sitemap)[:5]:
        page = get(url, ua).decode("utf-8", "ignore")
        title = _page_title(page)
        if company["id"] == "accenture":
            # 掲載日はページ本文の YYYY/M/D 表記を優先(lastmod は ±1 日ズレる)
            m = re.search(r"\d{4}/\d{1,2}/\d{1,2}", page)
            date = normalize_date(m.group(0)) if m else date
        if title:
            items.append({"title": title, "url": url, "date": date})
    return items


# ---- 入口 ----------------------------------------------------------------


def fetch_company(company, get) -> list[dict]:
    ua = BROWSER_UA if company.get("ua") == "browser" else PROJECT_UA
    strategy = company["strategy"]
    if strategy == "json":
        items = parse_hitachi_json(get(company["primary_url"], ua))
    elif strategy == "feed":
        items = parse_feed(get(company["primary_url"], ua))
    elif strategy == "sitemap":
        items = _fetch_sitemap_items(company, get, ua)
    else:
        html = get(company["primary_url"], ua).decode("utf-8", "ignore")
        items = _HTML_PARSERS[company["id"]](html, company["primary_url"])
    return [
        {"title": it["title"], "url": _https(it["url"]), "date": it["date"]}
        for it in items
        if it["title"] and it["url"]
    ]

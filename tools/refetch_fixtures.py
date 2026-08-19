"""テストフィクスチャの再取得ツール(手動実行専用)。

tests/fixtures/{id}.(xml|html) に各社の primary 応答を保存する。
sitemap 戦略の会社(nri / accenture)は最新 5 記事ページも
tests/fixtures/pages/{id}/{n}.html に保存し、URL → ファイルの対応を
tests/fixtures/pages/{id}/map.json に書く。

実行: python tools/refetch_fixtures.py
更新は専用コミット(test: update fixtures)で行うこと(TEST_SPEC 実行規約)。
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.fetchers import accenture_select, nri_select  # noqa: E402
from src.sources import BROWSER_UA, COMPANIES, PROJECT_UA  # noqa: E402

FIX = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def get(url: str, ua: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": ua, "Accept-Language": "ja"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def sitemap_top5(company_id: str, sitemap: bytes) -> list[str]:
    """本番と同じ選定ロジック(src.fetchers)で上位 5 記事 URL を返す。"""
    text = sitemap.decode("utf-8", "ignore")
    select = nri_select if company_id == "nri" else accenture_select
    return [u for u, _ in select(text)[:5]]


def main() -> None:
    only = set(sys.argv[1:])  # 例: python tools/refetch_fixtures.py nri
    FIX.mkdir(parents=True, exist_ok=True)
    for co in COMPANIES:
        if only and co["id"] not in only:
            continue
        ua = BROWSER_UA if co.get("ua") == "browser" else PROJECT_UA
        raw = get(co["primary_url"], ua)
        ext = {"feed": "xml", "sitemap": "xml", "json": "json"}.get(co["strategy"], "html")
        (FIX / f"{co['id']}.{ext}").write_bytes(raw)
        print(f"{co['id']}: primary {len(raw)} bytes")
        if co["strategy"] == "sitemap":
            top3 = sitemap_top5(co["id"], raw)
            pages = FIX / "pages" / co["id"]
            pages.mkdir(parents=True, exist_ok=True)
            mapping = {}
            for i, url in enumerate(top3):
                time.sleep(1)
                body = get(url, ua)
                fname = f"{i}.html"
                (pages / fname).write_bytes(body)
                mapping[url] = fname
                print(f"  page {url} → {fname} ({len(body)} bytes)")
            (pages / "map.json").write_text(
                json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8"
            )
        time.sleep(1)


if __name__ == "__main__":
    main()

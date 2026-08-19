"""11 社の取得経路の宣言的定義(F-06)。

strategy:
- feed:        primary_url が RSS/Atom/RDF フィード
- html:        primary_url の静的 HTML を会社別パーサで抽出
- sitemap:     primary_url が sitemap.xml。URL 群から最新 3 件を選び、
               各記事ページを追加取得してタイトル・日付を得る(fetchers 参照)

ua:
- project(既定): "koho-lens/1.0 (+https://github.com/twill3c/koho-lens)"
- browser: WAF が非ブラウザ UA を一律遮断するサイト(NEC)のみ。
  robots.txt で対象パスの許可を確認済み(2026-08-20, /press は Disallow 対象外)

調査経緯(2026-08-20):
- 富士通: 公式 global.fujitsu は bot 管理で 429 → 公式 PR TIMES アカウントの RDF を使用
- TIS: tis.co.jp は tisi.jp へ 301(現・TISI株式会社)
- 日鉄ソリューションズ: 公式 /press/ は JS レンダリング必須 → 公式 Digital PR Platform
  アカウント(digitalpr.jp/c/814)の静的 HTML を使用
- NRI / アクセンチュア: 一覧が JS レンダリング必須 → sitemap.xml 経由
"""

PROJECT_UA = "koho-lens/1.0 (+https://github.com/twill3c/koho-lens)"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

COMPANIES = [
    {
        "id": "fujitsu",
        "name": "富士通",
        "source_url": "https://global.fujitsu/ja-jp/pr/news",
        "primary_url": "https://prtimes.jp/companyrdf.php?company_id=93942",
        "strategy": "feed",
        "allowed_domains": ["prtimes.jp", "global.fujitsu"],
    },
    {
        "id": "nec",
        "name": "NEC",
        "source_url": "https://jpn.nec.com/press/index.html",
        "primary_url": "https://jpn.nec.com/ja/press/press.xml",
        "strategy": "feed",
        "ua": "browser",
        "allowed_domains": ["jpn.nec.com"],
    },
    {
        "id": "hitachi",
        "name": "日立製作所",
        "source_url": "https://www.hitachi.com/ja-jp/press/",
        "primary_url": "https://www.hitachi.com/ja-jp/press/",
        "strategy": "html",
        "allowed_domains": ["hitachi.com"],
    },
    {
        "id": "nttdata",
        "name": "NTTデータ",
        "source_url": "https://www.nttdata.com/global/ja/news/",
        "primary_url": "https://www.nttdata.com/global/ja/news/",
        "strategy": "html",
        "allowed_domains": ["nttdata.com"],
    },
    {
        "id": "nri",
        "name": "野村総合研究所",
        "source_url": "https://www.nri.com/jp/news/index.html",
        "primary_url": "https://www.nri.com/jp/sitemap.xml",
        "strategy": "sitemap",
        "allowed_domains": ["nri.com"],
    },
    {
        "id": "scsk",
        "name": "SCSK",
        "source_url": "https://www.scsk.jp/news/2026/index.html",
        "primary_url": "https://www.scsk.jp/rss.xml",
        "strategy": "feed",
        "allowed_domains": ["scsk.jp"],
    },
    {
        "id": "tis",
        "name": "TIS(TISI)",
        "source_url": "https://www.tisi.jp/news/",
        "primary_url": "https://www.tisi.jp/news/",
        "strategy": "html",
        "allowed_domains": ["tisi.jp"],
    },
    {
        "id": "accenture",
        "name": "アクセンチュア",
        "source_url": "https://newsroom.accenture.jp/",
        "primary_url": "https://newsroom.accenture.jp/sitemap.xml",
        "strategy": "sitemap",
        "allowed_domains": ["newsroom.accenture.jp"],
    },
    {
        "id": "ibm",
        "name": "日本IBM",
        "source_url": "https://jp.newsroom.ibm.com/announcements",
        "primary_url": "https://jp.newsroom.ibm.com/announcements?pagetemplate=rss",
        "strategy": "feed",
        "allowed_domains": ["jp.newsroom.ibm.com"],
    },
    {
        "id": "nssol",
        "name": "日鉄ソリューションズ",
        "source_url": "https://www.nssol.nipponsteel.com/press/",
        "primary_url": "https://digitalpr.jp/c/814",
        "strategy": "html",
        "allowed_domains": ["digitalpr.jp", "nssol.nipponsteel.com"],
    },
    {
        "id": "canon_its",
        "name": "キヤノンITソリューションズ",
        "source_url": "https://www.canon-its.co.jp/corporate/newsrelease",
        "primary_url": "https://www.canon-its.co.jp/corporate/newsrelease",
        "strategy": "html",
        "allowed_domains": ["canon-its.co.jp"],
    },
]

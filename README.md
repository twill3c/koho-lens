# 広報レンズ(koho-lens)

日本の主要 IT サービス企業 11 社(富士通・NEC・日立製作所・NTTデータ・野村総合研究所・
SCSK・TIS・アクセンチュア・日本IBM・日鉄ソリューションズ・キヤノンITソリューションズ)の
最新プレスリリースを各 3 件、ヘッドライン+リンクで一望する静的サイト。

**本番**: https://koho-lens.vercel.app

## 仕組み

```
GitHub Actions cron(6 時間間隔)
  → python -m src.fetch(11 社を収集 → data/releases.json → out/index.html)
  → data: snapshot コミット
  → Vercel Git 連携が out/ を自動配信
```

- 取得経路は [src/sources.py](src/sources.py) に宣言的に定義(feed / html / sitemap)
- 1 社の取得失敗は全体を止めず、前回分を保持して「取得失敗」表示(グレースフル劣化)
- ランタイム依存は Python 標準ライブラリのみ

## 開発

```bash
python -m pytest -q        # テスト(pytest のみ dev 依存)
python -m src.fetch        # 手動収集+レンダリング
python tools/refetch_fixtures.py  # テストフィクスチャ再取得(専用コミットで)
```

仕様は [SPEC.md](SPEC.md)、テスト対応は [TEST_SPEC.md](TEST_SPEC.md) を参照。

## 法務・収集ポリシー

- 保存・表示するのは各社が公式公開する**見出し・リンク・日付のみ**(本文は保存しない)
- 収集は 6 時間間隔。User-Agent に本リポジトリ URL を明記
  (WAF が非ブラウザ UA を一律遮断する 1 社のみ、robots.txt の許可を確認のうえブラウザ相当 UA)
- 見出しの著作権は各発表企業に帰属。出典は各社公式サイトへリンク

# 歴代映画 興行収入ランキング

世界の映画を興行収入順にまとめた、データで見る名作ガイドサイトです。

## 構成

- `build_site.py` … `films_clean.csv` からサイトを自動生成するスクリプト
- `docs/` … 生成された公開用サイト（GitHub Pages の公開フォルダ）
  - `index.html` … 興行収入ランキング
  - `about.html` … サイト紹介
  - `privacy.html` … プライバシーポリシー／アフィリエイト開示

## 更新方法

```
C:\Python313\python.exe build_site.py
```

を実行すると `docs/` が最新データで作り直されます。

## 公開

GitHub Pages を `main` ブランチの `/docs` フォルダから配信する設定にしています。

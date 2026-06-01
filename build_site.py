# -*- coding: utf-8 -*-
# ======================================================================
#  映画ランキングサイト ビルダー  -  build_site.py
# ----------------------------------------------------------------------
#  films_clean.csv（Wikipediaの歴代興行収入データ＝合法に使える）を読んで、
#  Amazonアソシエイト審査に出せる本物のサイトを docs/ フォルダに自動生成する。
#
#  作るページ:
#    docs/index.html    ... 興行収入ランキング（Amazonリンク付き）＋紹介文
#    docs/about.html    ... サイト紹介（運営者情報）
#    docs/privacy.html  ... プライバシーポリシー＋アフィリエイト開示（審査で必須）
#
#  このスクリプトを実行するたびにサイトが作り直されるので、
#  あとで git push まで自動化すれば「毎回最新の自動更新サイト」になる。
# ======================================================================

import csv
import os
import html
from urllib.parse import quote_plus      # URL用に文字を安全な形に変換する係
from datetime import datetime, timezone, timedelta

# --- 設定（ここを書き換えるだけで挙動が変わる）---------------------------
CSV_PATH = "../films_clean.csv"   # 映画データの場所（scraping-practice 直下）
OUT_DIR = "docs"                  # 出力先フォルダ（GitHub Pagesで公開する場所）
TOP_N = 30                        # ランキングに載せる件数

# ★AmazonアソシエイトのトラッキングID（登録後にここを自分のIDへ）★
#   今は仮。例: "yuuki-22"。これ経由で売れると報酬が入る。
AMAZON_TAG = "YOURID-22"

SITE_NAME = "歴代映画 興行収入ランキング"
SITE_DESC = "世界の映画を興行収入順にまとめた、データで見る名作ガイド。"


def load_movies():
    """films_clean.csv を読んで、映画の一覧（辞書のリスト）を返す。"""
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    movies = []
    for r in rows:
        # 興行収入(数値)が空や非数値の行はスキップ（安全のため）
        gross_raw = r.get("興行収入(数値)", "").strip()
        if not gross_raw.isdigit():
            continue
        movies.append({
            "rank":  int(r["Rank"]) if r["Rank"].isdigit() else 0,
            "title": r["Title"].strip(),
            "year":  r["Year"].strip(),
            "gross": int(gross_raw),
        })

    # 興行収入の高い順に並べて、上位だけ返す
    movies.sort(key=lambda m: -m["gross"])
    return movies[:TOP_N]


def amazon_link(title):
    """映画タイトルから Amazon検索のアフィリエイトリンクを作る。
    ※Amazonの商品データを"スクレイプして表示"するのは規約違反なので、
      検索リンクへ送る方式にしている（これは規約OK）。"""
    # スペースや「:」などをURL用に変換（例: "Avengers: Endgame" → "Avengers%3A+Endgame"）
    keyword = quote_plus(f"{title} Blu-ray")
    return f"https://www.amazon.co.jp/s?k={keyword}&tag={AMAZON_TAG}"


def format_gross(value):
    """2923710708 → '$2,923,710,708（約29.2億ドル）' のように読みやすく。"""
    oku = value / 100_000_000           # 1億 = 100,000,000
    return f"${value:,}（約{oku:.1f}億ドル）"


def now_jst():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y年%m月%d日 %H:%M")


# ---------------------------------------------------------------------
#  共通の見た目（CSS）とページの枠。全ページで使い回す。
# ---------------------------------------------------------------------
def page_shell(title, body):
    """title と 本文(body) を受け取り、ページ全体のHTMLを返す。"""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(SITE_DESC)}">
  <title>{html.escape(title)} | {html.escape(SITE_NAME)}</title>
  <style>
    body {{ font-family:-apple-system,"Segoe UI",sans-serif; background:#0f1115;
            color:#e8e8ea; margin:0; line-height:1.7; }}
    a {{ color:#7db0ff; }}
    header.hero {{ background:linear-gradient(135deg,#1c2333,#0f1115);
            padding:38px 16px 30px; text-align:center; border-bottom:1px solid #232838; }}
    header.hero h1 {{ margin:0 0 8px; font-size:26px; }}
    header.hero p {{ margin:0; color:#9aa3b2; font-size:14px; }}
    nav {{ text-align:center; padding:12px; background:#11151d; font-size:14px; }}
    nav a {{ margin:0 10px; text-decoration:none; }}
    .wrap {{ max-width:760px; margin:0 auto; padding:24px 16px 60px; }}
    .intro {{ color:#b9c0cc; font-size:15px; margin-bottom:26px; }}
    .card {{ display:flex; align-items:center; gap:14px; background:#171b24;
             border:1px solid #232838; border-radius:12px; padding:14px 16px;
             margin-bottom:10px; }}
    .rank {{ font-size:22px; font-weight:bold; color:#ffcd6b; width:40px;
             text-align:center; flex-shrink:0; }}
    .info {{ flex:1; min-width:0; }}
    .title {{ font-weight:600; margin-bottom:3px; }}
    .meta {{ color:#9aa3b2; font-size:13px; }}
    .btn {{ flex-shrink:0; background:#ff9900; color:#111; font-weight:600;
            text-decoration:none; padding:9px 14px; border-radius:8px; font-size:14px; }}
    .btn:hover {{ background:#ffb84d; }}
    h2 {{ margin-top:34px; }}
    footer {{ border-top:1px solid #232838; color:#7a8290; font-size:12px;
              text-align:center; padding:24px 16px; margin-top:30px; }}
    footer a {{ color:#9aa3b2; }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>🎬 {html.escape(SITE_NAME)}</h1>
    <p>{html.escape(SITE_DESC)}</p>
  </header>
  <nav>
    <a href="index.html">ランキング</a>
    <a href="about.html">このサイトについて</a>
    <a href="privacy.html">プライバシーポリシー</a>
  </nav>
  <div class="wrap">
{body}
  </div>
  <footer>
    最終更新: {now_jst()}　/
    <a href="about.html">運営情報</a>・<a href="privacy.html">プライバシーポリシー</a><br>
    当サイトはAmazonアソシエイト・プログラムの参加者です。<br>
    &copy; {SITE_NAME}
  </footer>
</body>
</html>"""


def build_index(movies):
    """トップページ（ランキング）を作る。"""
    cards = []
    for m in movies:
        cards.append(f"""
    <div class="card">
      <div class="rank">{m['rank']}</div>
      <div class="info">
        <div class="title">{html.escape(m['title'])}</div>
        <div class="meta">{m['year']}年公開 ・ 世界興行収入 {format_gross(m['gross'])}</div>
      </div>
      <a class="btn" href="{amazon_link(m['title'])}" target="_blank" rel="noopener sponsored">
        Amazonで観る
      </a>
    </div>""")

    body = f"""    <p class="intro">
      世界中で公開された映画を「興行収入（世界での売上）」の多い順にランキングしました。
      数字で見ると、時代を超えて愛される名作や、社会現象になった大作の凄さがひと目で分かります。
      気になった作品は各カードのボタンから配信・ソフトをチェックできます。
    </p>
    <h2>世界興行収入ランキング TOP {len(movies)}</h2>
{''.join(cards)}
"""
    return page_shell("ランキング", body)


def build_about():
    """サイト紹介ページ（審査で運営者情報を見られるため用意）。"""
    body = """    <h2>このサイトについて</h2>
    <p>
      「歴代映画 興行収入ランキング」は、世界の映画を興行収入というデータの切り口で
      まとめ、名作との出会いをお手伝いするサイトです。話題作から往年の名作まで、
      「数字で見るとどれくらいヒットしたのか」を分かりやすく一覧にしています。
    </p>
    <h2>データについて</h2>
    <p>
      ランキングの興行収入データは、一般に公開されている資料をもとに集計・整形しています。
      数値は集計時点のもので、最新の状況と異なる場合があります。
    </p>
    <h2>運営者</h2>
    <p>
      個人で運営しています。お問い合わせは今後フォームを設置予定です。
    </p>"""
    return page_shell("このサイトについて", body)


def build_privacy():
    """プライバシーポリシー＋アフィリエイト開示（Amazon審査で重要）。"""
    body = """    <h2>プライバシーポリシー</h2>
    <p>当サイトでは、より良いサービス提供のためにアクセス解析ツールを利用する場合があります。
       これらはトラフィックデータの収集のためにCookieを使用することがありますが、
       個人を特定する情報は含まれません。</p>

    <h2>アフィリエイトプログラムについて</h2>
    <p>当サイトは、Amazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を
       提供することを目的に設定されたアフィリエイトプログラムである、
       Amazonアソシエイト・プログラムの参加者です。</p>
    <p>当サイトのリンクを経由して商品が購入された場合、運営者が一定の紹介料を受け取ることが
       あります。これにより利用者に追加の費用が発生することはありません。</p>

    <h2>免責事項</h2>
    <p>当サイトの情報は正確性に努めていますが、内容を保証するものではありません。
       掲載情報の利用によって生じたいかなる損害についても、運営者は責任を負いかねます。</p>

    <h2>お問い合わせ</h2>
    <p>本ポリシーに関するお問い合わせは、今後設置するお問い合わせ窓口よりご連絡ください。</p>"""
    return page_shell("プライバシーポリシー", body)


def main():
    print("1) 映画データを読み込み中...")
    movies = load_movies()
    print(f"   {len(movies)} 件を使います。")

    os.makedirs(OUT_DIR, exist_ok=True)

    pages = {
        "index.html":   build_index(movies),
        "about.html":   build_about(),
        "privacy.html": build_privacy(),
    }

    print("2) サイトを生成中...")
    for filename, content in pages.items():
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write(content)
        print(f"   作成: {path}")

    print("完成! docs/ フォルダにサイトができました。")
    print("→ docs/index.html をダブルクリックすると確認できます。")
    if AMAZON_TAG == "YOURID-22":
        print("※ まだ AMAZON_TAG が仮のままです。登録後に自分のIDへ書き換えてください。")


if __name__ == "__main__":
    main()

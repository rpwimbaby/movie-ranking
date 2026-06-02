# -*- coding: utf-8 -*-
# ======================================================================
#  Amazon売れ筋ピックアップ  サイトビルダー  -  build_site.py
# ----------------------------------------------------------------------
#  products.csv（あなたが選んだ商品リスト）を読んで、
#  「検索・絞り込み・ランキング・星評価・メリデメ・比較表・個別レビュー」
#  付きの本格的な商品紹介サイトを docs/ フォルダに自動生成する。
#
#  作るページ:
#    docs/index.html       ... 一覧(検索/絞り込み/ランキング/星評価)
#    docs/item-1.html ...   ... 商品ごとの個別レビューページ(比較表つき)
#    docs/about.html        ... サイト紹介
#    docs/privacy.html      ... プライバシーポリシー＋アフィリエイト開示
#
#  products.csv の列:
#    genre, name, rating, reason, pros, cons, review, image, (任意)link
#    ・rating … 5点満点の評価（例 4.5）
#    ・reason … 推しポイント（1文）
#    ・pros   … メリット（｜で区切って複数）
#    ・cons   … デメリット（｜で区切って複数）
#    ・review … レビュー本文
#    ・image  … 画像URL（空ならジャンル色サムネ）
#    ・link   … SiteStripeの個別リンク（空なら検索リンクを自動生成）
#    ※同じジャンル内では「CSVに書いた順」がそのまま 1位→2位… になる。
# ======================================================================

import csv
import os
import json
import html
from urllib.parse import quote_plus
from datetime import datetime, timezone, timedelta

# --- 設定 ----------------------------------------------------------------
CSV_PATH = "products.csv"
OUT_DIR = "docs"
AMAZON_TAG = "rpwimbaby-22"     # ★AmazonアソシエイトのトラッキングID★

SITE_NAME = "Amazon売れ筋ピックアップ"
SITE_DESC = "ジャンル別に、Amazonで本当に使える定番アイテムを厳選して紹介します。"

GENRE_ICONS = {
    "ガジェット・スマホ周り": "🔌", "キッチン・便利グッズ": "🍳",
    "美容・健康": "💆", "日用品・消耗品": "🧴", "本・Kindle": "📚",
    "ファッション": "👕", "アウトドア": "⛺", "おもちゃ・ホビー": "🎲",
}
GENRE_COLORS = {
    "ガジェット・スマホ周り": ("#6366f1", "#8b5cf6"),
    "キッチン・便利グッズ": ("#f97316", "#fb923c"),
    "美容・健康": ("#ec4899", "#f472b6"),
    "日用品・消耗品": ("#10b981", "#34d399"),
    "本・Kindle": ("#0ea5e9", "#38bdf8"),
    "ファッション": ("#f43f5e", "#fb7185"),
    "アウトドア": ("#16a34a", "#4ade80"),
    "おもちゃ・ホビー": ("#eab308", "#facc15"),
}


def medal(rank):
    """順位を 🥇🥈🥉 や「4位」で返す。"""
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}位")


def load_products():
    """products.csv を読み、各商品に順位・サムネ色・リンク等を付けて返す。"""
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    products = []
    genre_count = {}     # ジャンルごとの通し番号（=順位）
    idx = 0
    for r in rows:
        genre = (r.get("genre") or "").strip()
        name  = (r.get("name") or "").strip()
        if not genre or not name:
            continue
        idx += 1
        rank = genre_count.get(genre, 0) + 1
        genre_count[genre] = rank

        try:
            rating = float((r.get("rating") or "0").strip())
        except ValueError:
            rating = 0.0

        c1, c2 = GENRE_COLORS.get(genre, ("#64748b", "#94a3b8"))
        products.append({
            "idx":     idx,
            "name":    name,
            "genre":   genre,
            "rank":    rank,
            "medal":   medal(rank),
            "rating":  rating,
            "pct":     round(rating / 5 * 100),
            "reason":  (r.get("reason") or "").strip(),
            "pros":    [p.strip() for p in (r.get("pros") or "").split("｜") if p.strip()],
            "cons":    [c.strip() for c in (r.get("cons") or "").split("｜") if c.strip()],
            "review":  (r.get("review") or "").strip(),
            "image":   (r.get("image") or "").strip(),
            "icon":    GENRE_ICONS.get(genre, "🛒"),
            "grad":    f"{c1}, {c2}",
            "detail":  f"item-{idx}.html",
            "url":     (r.get("link") or "").strip() or _search_link(name),
        })
    return products


def _search_link(name):
    return f"https://www.amazon.co.jp/s?k={quote_plus(name)}&tag={AMAZON_TAG}"


def genre_order(products):
    seen, order = set(), []
    for p in products:
        if p["genre"] not in seen:
            seen.add(p["genre"]); order.append(p["genre"])
    return order


def stars_html(pct):
    """星評価の見た目（金色の★を pct% だけ表示）。"""
    return f'<span class="stars" style="--pct:{pct}%"></span>'


def now_jst():
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y年%m月%d日 %H:%M")


# ---------------------------------------------------------------------
#  共通パーツ
# ---------------------------------------------------------------------
def base_css():
    return """
    :root{--bg:#f6f7fb;--card:#fff;--ink:#1c2230;--sub:#6b7385;--line:#e7e9f0;
      --brand:#4f46e5;--brand-2:#7c74ff;--amazon:#ff9900;--amazon-ink:#1a1a1a;
      --gold:#f5b301;--shadow:0 6px 22px rgba(28,34,48,.08);}
    *{box-sizing:border-box}
    body{font-family:-apple-system,"Segoe UI",system-ui,"Hiragino Sans","Noto Sans JP",sans-serif;
      margin:0;background:var(--bg);color:var(--ink);line-height:1.7;-webkit-font-smoothing:antialiased;}
    a{color:var(--brand);}
    .wrap{max-width:1040px;margin:0 auto;padding:0 18px;}
    header.hero{background:linear-gradient(135deg,#4f46e5 0%,#7c74ff 55%,#9f7bff 100%);
      color:#fff;padding:40px 18px 28px;text-align:center;}
    header.hero h1{margin:0 0 8px;font-size:27px;letter-spacing:.02em;}
    header.hero h1 a{color:#fff;text-decoration:none;}
    header.hero p{margin:0 auto;max-width:560px;color:#eef0ff;font-size:14.5px;}
    nav{background:rgba(255,255,255,.14);display:flex;gap:6px;justify-content:center;
      flex-wrap:wrap;margin-top:18px;}
    nav a{color:#fff;text-decoration:none;font-size:13.5px;padding:7px 14px;border-radius:999px;opacity:.92;}
    nav a:hover{background:rgba(255,255,255,.22);}
    footer{border-top:1px solid var(--line);color:var(--sub);font-size:12.5px;
      text-align:center;padding:26px 16px;margin-top:50px;background:#fff;}
    footer a{color:var(--sub);}
    /* 星評価 */
    .stars{display:inline-block;position:relative;font-family:Arial,sans-serif;
      font-size:15px;line-height:1;letter-spacing:2px;vertical-align:middle;}
    .stars::before{content:"★★★★★";color:#dfe3ec;}
    .stars::after{content:"★★★★★";color:var(--gold);position:absolute;left:0;top:0;
      width:var(--pct,0%);overflow:hidden;white-space:nowrap;}
    .rate-num{font-weight:700;color:#d98a00;font-size:13px;margin-left:7px;vertical-align:middle;}
    /* 順位メダル */
    .rankbadge{position:absolute;top:8px;left:8px;background:rgba(17,20,30,.78);color:#fff;
      font-weight:700;font-size:13px;padding:3px 9px;border-radius:999px;backdrop-filter:blur(2px);}
    """


def nav_html():
    return """  <nav>
    <a href="index.html">売れ筋まとめ</a>
    <a href="about.html">このサイトについて</a>
    <a href="privacy.html">プライバシーポリシー</a>
  </nav>"""


def footer_html():
    return f"""  <footer>
    最終更新: {now_jst()}　/
    <a href="about.html">運営情報</a>・<a href="privacy.html">プライバシーポリシー</a><br>
    当サイトはAmazonアソシエイト・プログラムの参加者です。<br>
    &copy; {html.escape(SITE_NAME)}
  </footer>"""


def html_doc(title, body, extra_css=""):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(SITE_DESC)}">
  <title>{html.escape(title)}</title>
  <style>{base_css()}{extra_css}</style>
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <h1><a href="index.html">🛍️ {html.escape(SITE_NAME)}</a></h1>
      <p>{html.escape(SITE_DESC)}</p>
    </div>
{nav_html()}
  </header>
{body}
{footer_html()}
</body>
</html>"""


# ---------------------------------------------------------------------
#  トップページ（検索・絞り込み・ランキング・星評価）
# ---------------------------------------------------------------------
def index_css():
    return """
    .toolbar{position:sticky;top:0;z-index:20;background:rgba(246,247,251,.92);
      backdrop-filter:saturate(140%) blur(8px);border-bottom:1px solid var(--line);padding:14px 0 10px;}
    .search{position:relative;max-width:560px;margin:0 auto;}
    .search input{width:100%;padding:13px 16px 13px 44px;font-size:15px;border:1px solid var(--line);
      border-radius:999px;background:#fff;box-shadow:var(--shadow);outline:none;}
    .search input:focus{border-color:var(--brand);}
    .search svg{position:absolute;left:15px;top:50%;transform:translateY(-50%);width:18px;height:18px;fill:var(--sub);}
    .chips{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:12px auto 0;max-width:880px;}
    .chip{border:1px solid var(--line);background:#fff;color:var(--ink);padding:7px 14px;border-radius:999px;
      font-size:13px;cursor:pointer;transition:.15s;user-select:none;}
    .chip:hover{border-color:var(--brand-2);}
    .chip.active{background:var(--brand);border-color:var(--brand);color:#fff;}
    .meta-row{display:flex;align-items:center;justify-content:space-between;gap:12px;
      max-width:1040px;margin:16px auto 0;padding:0 2px;flex-wrap:wrap;}
    .count{color:var(--sub);font-size:13px;}
    .sort{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--sub);}
    .sort select{border:1px solid var(--line);border-radius:8px;padding:6px 8px;background:#fff;font-size:13px;color:var(--ink);}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:16px;padding:22px 0 10px;}
    .card{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;
      display:flex;flex-direction:column;box-shadow:var(--shadow);transition:transform .15s,box-shadow .15s;}
    .card:hover{transform:translateY(-4px);box-shadow:0 12px 30px rgba(28,34,48,.13);}
    .thumb{height:148px;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;}
    .thumb span.ico{font-size:58px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.18));}
    .thumb img{width:100%;height:100%;object-fit:cover;display:block;}
    .body{padding:14px 16px 16px;display:flex;flex-direction:column;gap:7px;flex:1;}
    .badge{align-self:flex-start;font-size:11.5px;color:var(--brand);background:#eef0ff;padding:3px 10px;border-radius:999px;}
    .card .name{font-weight:700;font-size:15px;line-height:1.5;}
    .rate-row{display:flex;align-items:center;}
    .reason{font-size:12.5px;color:#0f766e;background:#ecfdf5;border:1px solid #c7f0e2;
      padding:6px 10px;border-radius:9px;line-height:1.45;flex:1;}
    .card .btn{margin-top:4px;text-align:center;background:var(--brand);color:#fff;font-weight:700;
      text-decoration:none;padding:10px 14px;border-radius:10px;font-size:13.5px;transition:.15s;}
    .card .btn:hover{background:#4338ca;}
    .empty{text-align:center;color:var(--sub);padding:60px 16px;display:none;}
    .empty.show{display:block;}
    @media(max-width:520px){.grid{grid-template-columns:1fr 1fr;gap:11px;}
      .thumb{height:108px;}.thumb span.ico{font-size:42px;}.body{padding:11px;}
      .card .name{font-size:13px;}.reason{font-size:11.5px;}}
    """


def build_index(products):
    genres = genre_order(products)
    chips = ['<button class="chip active" data-genre="">すべて</button>']
    for g in genres:
        chips.append(f'<button class="chip" data-genre="{html.escape(g)}">'
                     f'{GENRE_ICONS.get(g,"🛒")} {html.escape(g)}</button>')

    # JS用に必要な項目だけ渡す
    slim = [{"name": p["name"], "genre": p["genre"], "icon": p["icon"], "grad": p["grad"],
             "image": p["image"], "reason": p["reason"], "rating": p["rating"],
             "pct": p["pct"], "medal": p["medal"], "rank": p["rank"],
             "detail": p["detail"]} for p in products]
    data_json = json.dumps(slim, ensure_ascii=False).replace("</", "<\\/")

    body = f"""  <main>
    <div class="toolbar">
      <div class="wrap">
        <div class="search">
          <svg viewBox="0 0 24 24"><path d="M21 20l-5.6-5.6a7 7 0 10-1.4 1.4L20 21zM4 10a6 6 0 1112 0 6 6 0 01-12 0z"/></svg>
          <input id="q" type="search" placeholder="商品名・キーワードで検索（例: モバイルバッテリー）" autocomplete="off">
        </div>
        <div class="chips" id="chips">{''.join(chips)}</div>
      </div>
    </div>
    <div class="wrap">
      <div class="meta-row">
        <div class="count" id="count"></div>
        <label class="sort">並び替え
          <select id="sort">
            <option value="default">ランキング順</option>
            <option value="rating">評価が高い順</option>
            <option value="name">名前順</option>
            <option value="genre">ジャンル順</option>
          </select>
        </label>
      </div>
      <div class="grid" id="grid"></div>
      <div class="empty" id="empty">該当する商品が見つかりませんでした。<br>キーワードを変えてみてください。</div>
    </div>
  </main>

  <script>
    const PRODUCTS = {data_json};
    const grid=document.getElementById('grid'), empty=document.getElementById('empty'),
          count=document.getElementById('count'), q=document.getElementById('q'),
          sortSel=document.getElementById('sort');
    let activeGenre="";
    function esc(s){{return (s||'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}
    function cardHtml(p){{
      const thumb = p.image
        ? `<div class="thumb"><div class="rankbadge">${{p.medal}}</div><img src="${{p.image}}" alt="${{esc(p.name)}}" loading="lazy"></div>`
        : `<div class="thumb" style="background:linear-gradient(135deg, ${{p.grad}})"><div class="rankbadge">${{p.medal}}</div><span class="ico">${{p.icon}}</span></div>`;
      return `
        <div class="card">
          ${{thumb}}
          <div class="body">
            <span class="badge">${{p.icon}} ${{esc(p.genre)}}</span>
            <div class="name">${{esc(p.name)}}</div>
            <div class="rate-row"><span class="stars" style="--pct:${{p.pct}}%"></span><span class="rate-num">${{p.rating.toFixed(1)}}</span></div>
            <div class="reason">${{esc(p.reason)}}</div>
            <a class="btn" href="${{p.detail}}">詳しく見る →</a>
          </div>
        </div>`;
    }}
    function render(){{
      const kw=q.value.trim().toLowerCase();
      let list=PRODUCTS.filter(p=>{{
        const okG=!activeGenre||p.genre===activeGenre;
        const okK=!kw||(p.name+' '+(p.reason||'')).toLowerCase().includes(kw);
        return okG&&okK;
      }});
      const m=sortSel.value;
      if(m==='rating') list=[...list].sort((a,b)=>b.rating-a.rating);
      if(m==='name')   list=[...list].sort((a,b)=>a.name.localeCompare(b.name,'ja'));
      if(m==='genre')  list=[...list].sort((a,b)=>a.genre.localeCompare(b.genre,'ja'));
      grid.innerHTML=list.map(cardHtml).join('');
      count.textContent=`${{list.length}} 件を表示中`;
      empty.classList.toggle('show',list.length===0);
    }}
    q.addEventListener('input',render);
    sortSel.addEventListener('change',render);
    document.getElementById('chips').addEventListener('click',e=>{{
      const b=e.target.closest('.chip'); if(!b) return;
      activeGenre=b.dataset.genre;
      document.querySelectorAll('.chip').forEach(c=>c.classList.remove('active'));
      b.classList.add('active'); render();
    }});
    render();
  </script>"""
    return html_doc(SITE_NAME, body, index_css())


# ---------------------------------------------------------------------
#  個別レビューページ（メリデメ・比較表つき）
# ---------------------------------------------------------------------
def detail_css():
    return """
    .crumb{font-size:12.5px;color:var(--sub);padding:18px 0 0;}
    .crumb a{color:var(--sub);text-decoration:none;}
    .detail{display:grid;grid-template-columns:300px 1fr;gap:26px;padding:18px 0 6px;align-items:start;}
    .dthumb{height:240px;border-radius:16px;display:flex;align-items:center;justify-content:center;
      position:relative;overflow:hidden;box-shadow:var(--shadow);}
    .dthumb span.ico{font-size:96px;filter:drop-shadow(0 6px 12px rgba(0,0,0,.2));}
    .dthumb img{width:100%;height:100%;object-fit:cover;}
    .dhead .badge{display:inline-block;font-size:12px;color:var(--brand);background:#eef0ff;padding:3px 11px;border-radius:999px;}
    .dhead h1{font-size:23px;margin:10px 0 8px;line-height:1.45;}
    .dhead .rate-row{display:flex;align-items:center;margin-bottom:14px;}
    .stars.big{font-size:22px;letter-spacing:3px;}
    .rate-num.big{font-size:16px;}
    .reasonbox{background:#ecfdf5;border:1px solid #c7f0e2;border-radius:12px;padding:13px 15px;
      color:#0f766e;font-size:14.5px;margin-bottom:18px;}
    .reasonbox b{color:#0d9488;}
    .buy{display:inline-block;background:var(--amazon);color:var(--amazon-ink);font-weight:800;
      text-decoration:none;padding:14px 26px;border-radius:12px;font-size:15.5px;box-shadow:var(--shadow);}
    .buy:hover{background:#ffb13d;}
    .proscons{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:30px 0 6px;}
    .pcbox{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow);}
    .pcbox h3{margin:0 0 10px;font-size:15px;}
    .pcbox.good h3{color:#0d9488;} .pcbox.bad h3{color:#e11d48;}
    .pcbox ul{margin:0;padding-left:20px;color:#3c4354;font-size:14px;}
    .pcbox li{margin:5px 0;}
    .sec{margin-top:30px;}
    .sec h2{font-size:18px;margin:0 0 10px;border-left:4px solid var(--brand);padding-left:10px;}
    .review{color:#3c4354;font-size:15px;}
    table.cmp{width:100%;border-collapse:collapse;font-size:13.5px;background:#fff;
      border:1px solid var(--line);border-radius:12px;overflow:hidden;}
    table.cmp th,table.cmp td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle;}
    table.cmp th{background:#f0f1f7;color:var(--sub);font-weight:600;}
    table.cmp tr:last-child td{border-bottom:none;}
    table.cmp tr.cur{background:#eef0ff;}
    table.cmp a{text-decoration:none;font-weight:600;}
    .cmp .mini-rank{font-weight:700;}
    .backlink{display:inline-block;margin:26px 0 0;color:var(--brand);text-decoration:none;font-size:14px;}
    @media(max-width:680px){.detail{grid-template-columns:1fr;}.dthumb{height:200px;}
      .proscons{grid-template-columns:1fr;}}
    """


def build_detail(p, genre_items):
    thumb_inner = (f'<img src="{html.escape(p["image"])}" alt="{html.escape(p["name"])}">'
                   if p["image"] else f'<span class="ico">{p["icon"]}</span>')
    pros = "".join(f"<li>{html.escape(x)}</li>" for x in p["pros"]) or "<li>—</li>"
    cons = "".join(f"<li>{html.escape(x)}</li>" for x in p["cons"]) or "<li>—</li>"

    # 同ジャンルの比較表
    rows = []
    for q in genre_items:
        cur = " class=\"cur\"" if q["idx"] == p["idx"] else ""
        name_cell = (html.escape(q["name"]) if q["idx"] == p["idx"]
                     else f'<a href="{q["detail"]}">{html.escape(q["name"])}</a>')
        rows.append(
            f'<tr{cur}><td class="mini-rank">{q["medal"]}</td>'
            f'<td>{name_cell}</td>'
            f'<td>{stars_html(q["pct"])} <span class="rate-num">{q["rating"]:.1f}</span></td>'
            f'<td>{html.escape(q["reason"])}</td></tr>')
    cmp_table = (
        '<table class="cmp"><thead><tr><th>順位</th><th>商品</th><th>評価</th>'
        '<th>推しポイント</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table>')

    body = f"""  <div class="wrap">
    <div class="crumb">
      <a href="index.html">売れ筋まとめ</a> ›
      <a href="index.html">{html.escape(p["genre"])}</a> ›
      {html.escape(p["name"])}
    </div>

    <div class="detail">
      <div class="dthumb" style="background:linear-gradient(135deg, {p['grad']})">
        <div class="rankbadge">{p['medal']}</div>{thumb_inner}
      </div>
      <div class="dhead">
        <span class="badge">{p['icon']} {html.escape(p['genre'])}　{p['medal']}</span>
        <h1>{html.escape(p['name'])}</h1>
        <div class="rate-row">{stars_html(p['pct'])}<span class="rate-num big">{p['rating']:.1f} / 5.0</span></div>
        <div class="reasonbox"><b>推しポイント</b>：{html.escape(p['reason'])}</div>
        <a class="buy" href="{p['url']}" target="_blank" rel="noopener sponsored">Amazonで価格・在庫を見る</a>
      </div>
    </div>

    <div class="proscons">
      <div class="pcbox good"><h3>👍 メリット</h3><ul>{pros}</ul></div>
      <div class="pcbox bad"><h3>👀 気になる点</h3><ul>{cons}</ul></div>
    </div>

    <div class="sec">
      <h2>レビュー</h2>
      <p class="review">{html.escape(p['review'])}</p>
    </div>

    <div class="sec">
      <h2>同じジャンルの商品と比較</h2>
      {cmp_table}
    </div>

    <a class="backlink" href="index.html">← 売れ筋まとめ一覧へ戻る</a>
  </div>"""
    return html_doc(f"{p['name']}のレビュー | {SITE_NAME}", body, detail_css())


# ---------------------------------------------------------------------
def build_about():
    body = """  <div class="wrap" style="padding:30px 0;">
    <h2>このサイトについて</h2>
    <p>「Amazon売れ筋ピックアップ」は、Amazonで買えるアイテムの中から「長く使える」
      「買ってよかった」と思える定番を、ジャンル別に厳選して紹介するサイトです。
      数ある商品から選ぶ手間を少しでも減らせるよう、実用性を重視してまとめています。</p>
    <h2>評価・選び方について</h2>
    <p>掲載している評価・メリット・デメリットは、用途や使い勝手をもとにした編集部の目安です。
      価格・在庫・最新のレビューは各リンク先のAmazonのページでご確認ください。</p>
    <h2>運営者</h2>
    <p>個人で運営しています。お問い合わせは今後フォームを設置予定です。</p>
  </div>"""
    return html_doc("このサイトについて | " + SITE_NAME, body)


def build_privacy():
    body = """  <div class="wrap" style="padding:30px 0;">
    <h2>プライバシーポリシー</h2>
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
    <p>本ポリシーに関するお問い合わせは、今後設置するお問い合わせ窓口よりご連絡ください。</p>
  </div>"""
    return html_doc("プライバシーポリシー | " + SITE_NAME, body)


def main():
    print("1) 商品データを読み込み中...")
    products = load_products()
    genres = genre_order(products)
    print(f"   {len(genres)} ジャンル / {len(products)} 商品")

    # ジャンルごとの商品（比較表用）
    by_genre = {g: [p for p in products if p["genre"] == g] for g in genres}

    os.makedirs(OUT_DIR, exist_ok=True)
    pages = {
        "index.html":   build_index(products),
        "about.html":   build_about(),
        "privacy.html": build_privacy(),
    }
    for p in products:
        pages[p["detail"]] = build_detail(p, by_genre[p["genre"]])

    print("2) サイトを生成中...")
    for filename, content in pages.items():
        with open(os.path.join(OUT_DIR, filename), "w", encoding="utf-8-sig") as f:
            f.write(content)
    print(f"   {len(pages)} ページを作成（個別レビュー {len(products)} ページ含む）")
    print("完成! docs/index.html をブラウザで開くと確認できます。")


if __name__ == "__main__":
    main()

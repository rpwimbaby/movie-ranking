# -*- coding: utf-8 -*-
# ======================================================================
#  Amazon売れ筋ピックアップ  サイトビルダー  -  build_site.py
# ----------------------------------------------------------------------
#  products.csv（あなたが選んだ商品リスト）を読んで、
#  「検索・ジャンル絞り込み・並び替え」付きの本格的な商品紹介サイトを
#  docs/ フォルダに自動生成する。
#
#  特徴:
#   ・商品データはページ内に埋め込み → ブラウザ側JSで瞬時に検索/絞り込み(サーバー不要)
#   ・スマホ対応のレスポンシブなカードグリッド
#   ・ジャンルチップで絞り込み、キーワード検索、並び替え、件数表示
#
#  作るページ:
#    docs/index.html    ... 売れ筋まとめ（検索・絞り込みUI付き）
#    docs/about.html    ... サイト紹介
#    docs/privacy.html  ... プライバシーポリシー＋アフィリエイト開示
# ======================================================================

import csv
import os
import json
import html
from urllib.parse import quote_plus
from datetime import datetime, timezone, timedelta

# --- 設定（ここを書き換えるだけで挙動が変わる）---------------------------
CSV_PATH = "products.csv"
OUT_DIR = "docs"

# ★AmazonアソシエイトのトラッキングID★ これ経由で売れると報酬が入る。
AMAZON_TAG = "rpwimbaby-22"

SITE_NAME = "Amazon売れ筋ピックアップ"
SITE_DESC = "ジャンル別に、Amazonで本当に使える定番アイテムを厳選して紹介します。"

# ジャンルごとの絵文字（見た目のアクセント）。無いジャンルは🛒になる。
GENRE_ICONS = {
    "ガジェット・スマホ周り": "🔌",
    "キッチン・便利グッズ": "🍳",
    "美容・健康": "💆",
    "日用品・消耗品": "🧴",
    "本・Kindle": "📚",
    "ファッション": "👕",
    "アウトドア": "⛺",
    "おもちゃ・ホビー": "🎲",
}

# ジャンルごとのサムネイル背景グラデ（画像が無いときに使う色）。無いジャンルはグレー。
GENRE_COLORS = {
    "ガジェット・スマホ周り": ("#6366f1", "#8b5cf6"),
    "キッチン・便利グッズ": ("#f97316", "#fb923c"),
    "美容・健康":           ("#ec4899", "#f472b6"),
    "日用品・消耗品":       ("#10b981", "#34d399"),
    "本・Kindle":           ("#0ea5e9", "#38bdf8"),
    "ファッション":         ("#f43f5e", "#fb7185"),
    "アウトドア":           ("#16a34a", "#4ade80"),
    "おもちゃ・ホビー":     ("#eab308", "#facc15"),
}


def load_products():
    """products.csv を読んで商品リスト（辞書のリスト）を返す。CSVの順を保つ。"""
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    products = []
    for r in rows:
        genre = (r.get("genre") or "").strip()
        name  = (r.get("name") or "").strip()
        if not genre or not name:
            continue
        c1, c2 = GENRE_COLORS.get(genre, ("#64748b", "#94a3b8"))
        products.append({
            "name":    name,
            "reason":  (r.get("reason") or "").strip(),
            "comment": (r.get("comment") or "").strip(),
            "genre":   genre,
            # link列(SiteStripeの個別リンク)があれば優先、無ければ検索リンクを生成
            "url":     (r.get("link") or "").strip() or _search_link(name),
            # image列に画像URLを入れれば本物画像に。空ならジャンル色サムネ。
            "image":   (r.get("image") or "").strip(),
            "icon":    GENRE_ICONS.get(genre, "🛒"),
            "grad":    f"{c1}, {c2}",
        })
    return products


def _search_link(name):
    """商品名で Amazon を検索するアフィリエイトリンク（規約OK・すぐ動く）。"""
    return f"https://www.amazon.co.jp/s?k={quote_plus(name)}&tag={AMAZON_TAG}"


def genre_order(products):
    """商品の登場順でジャンル名の一覧を返す（重複なし）。"""
    seen, order = set(), []
    for p in products:
        if p["genre"] not in seen:
            seen.add(p["genre"])
            order.append(p["genre"])
    return order


def now_jst():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).strftime("%Y年%m月%d日 %H:%M")


# ---------------------------------------------------------------------
#  共通パーツ（全ページで使い回すCSS・ナビ・フッター）
# ---------------------------------------------------------------------
def base_css():
    return """
    :root{
      --bg:#f6f7fb; --card:#ffffff; --ink:#1c2230; --sub:#6b7385;
      --line:#e7e9f0; --brand:#4f46e5; --brand-2:#7c74ff;
      --amazon:#ff9900; --amazon-ink:#1a1a1a; --shadow:0 6px 22px rgba(28,34,48,.08);
    }
    *{box-sizing:border-box}
    body{font-family:-apple-system,"Segoe UI",system-ui,"Hiragino Sans",
         "Noto Sans JP",sans-serif; margin:0; background:var(--bg); color:var(--ink);
         line-height:1.7; -webkit-font-smoothing:antialiased;}
    a{color:var(--brand);}
    .wrap{max-width:1040px; margin:0 auto; padding:0 18px;}
    header.hero{background:linear-gradient(135deg,#4f46e5 0%,#7c74ff 55%,#9f7bff 100%);
         color:#fff; padding:42px 18px 30px; text-align:center;}
    header.hero h1{margin:0 0 8px; font-size:28px; letter-spacing:.02em;}
    header.hero p{margin:0 auto; max-width:560px; color:#eef0ff; font-size:14.5px;}
    nav{background:rgba(255,255,255,.14); display:flex; gap:6px; justify-content:center;
        flex-wrap:wrap; margin-top:18px;}
    nav a{color:#fff; text-decoration:none; font-size:13.5px; padding:7px 14px;
        border-radius:999px; opacity:.92;}
    nav a:hover{background:rgba(255,255,255,.22);}
    footer{border-top:1px solid var(--line); color:var(--sub); font-size:12.5px;
        text-align:center; padding:26px 16px; margin-top:50px; background:#fff;}
    footer a{color:var(--sub);}
    .page{padding:30px 0;}
    .page h2{margin-top:30px; font-size:20px;}
    .page p{color:#3c4354;}
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


def page_shell(title, body, extra_head="", extra_css=""):
    """about/privacy など通常ページ用の枠。"""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(SITE_DESC)}">
  <title>{html.escape(title)} | {html.escape(SITE_NAME)}</title>
  <style>{base_css()}{extra_css}</style>
{extra_head}
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <h1>🛍️ {html.escape(SITE_NAME)}</h1>
      <p>{html.escape(SITE_DESC)}</p>
    </div>
{nav_html()}
  </header>
{body}
{footer_html()}
</body>
</html>"""


# ---------------------------------------------------------------------
#  トップページ（検索・絞り込み・並び替え付き）
# ---------------------------------------------------------------------
def index_css():
    return """
    .toolbar{position:sticky; top:0; z-index:20; background:rgba(246,247,251,.92);
        backdrop-filter:saturate(140%) blur(8px); border-bottom:1px solid var(--line);
        padding:14px 0 10px;}
    .search{position:relative; max-width:560px; margin:0 auto;}
    .search input{width:100%; padding:13px 16px 13px 44px; font-size:15px;
        border:1px solid var(--line); border-radius:999px; background:#fff;
        box-shadow:var(--shadow); outline:none;}
    .search input:focus{border-color:var(--brand);}
    .search svg{position:absolute; left:15px; top:50%; transform:translateY(-50%);
        width:18px; height:18px; fill:var(--sub);}
    .chips{display:flex; gap:8px; flex-wrap:wrap; justify-content:center;
        margin:12px auto 0; max-width:880px;}
    .chip{border:1px solid var(--line); background:#fff; color:var(--ink);
        padding:7px 14px; border-radius:999px; font-size:13px; cursor:pointer;
        transition:.15s; user-select:none;}
    .chip:hover{border-color:var(--brand-2);}
    .chip.active{background:var(--brand); border-color:var(--brand); color:#fff;}
    .meta-row{display:flex; align-items:center; justify-content:space-between;
        gap:12px; max-width:1040px; margin:16px auto 0; padding:0 2px; flex-wrap:wrap;}
    .count{color:var(--sub); font-size:13px;}
    .sort{display:flex; align-items:center; gap:6px; font-size:13px; color:var(--sub);}
    .sort select{border:1px solid var(--line); border-radius:8px; padding:6px 8px;
        background:#fff; font-size:13px; color:var(--ink);}
    .grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(248px,1fr));
        gap:16px; padding:22px 0 10px;}
    .card{background:var(--card); border:1px solid var(--line); border-radius:16px;
        overflow:hidden; display:flex; flex-direction:column;
        box-shadow:var(--shadow); transition:transform .15s, box-shadow .15s;}
    .card:hover{transform:translateY(-4px); box-shadow:0 12px 30px rgba(28,34,48,.13);}
    .thumb{height:148px; display:flex; align-items:center; justify-content:center;
        position:relative; overflow:hidden;}
    .thumb span{font-size:58px; filter:drop-shadow(0 4px 8px rgba(0,0,0,.18));}
    .thumb img{width:100%; height:100%; object-fit:cover; display:block;}
    .body{padding:15px 16px 17px; display:flex; flex-direction:column; gap:8px; flex:1;}
    .badge{align-self:flex-start; font-size:11.5px; color:var(--brand);
        background:#eef0ff; padding:3px 10px; border-radius:999px;}
    .card .name{font-weight:700; font-size:15.5px; line-height:1.5;}
    .reason{font-size:13px; color:#0f766e; background:#ecfdf5; border:1px solid #c7f0e2;
        padding:7px 10px; border-radius:9px; line-height:1.45;}
    .reason b{color:#0d9488;}
    .card .comment{color:var(--sub); font-size:13px; flex:1; line-height:1.6;}
    .card .btn{margin-top:4px; text-align:center; background:var(--amazon);
        color:var(--amazon-ink); font-weight:700; text-decoration:none;
        padding:11px 14px; border-radius:10px; font-size:14px; transition:.15s;}
    .card .btn:hover{background:#ffb13d;}
    .empty{text-align:center; color:var(--sub); padding:60px 16px; display:none;}
    .empty.show{display:block;}
    @media(max-width:520px){
      .grid{grid-template-columns:1fr 1fr; gap:11px;}
      .thumb{height:110px;} .thumb span{font-size:44px;}
      .body{padding:12px;}
      .card .name{font-size:13.5px;}
      .reason{font-size:12px;}
    }
    """


def build_index(products):
    """検索・絞り込み・並び替え付きトップページを作る。"""
    genres = genre_order(products)

    # ジャンルチップ（「すべて」＋各ジャンル）
    chips = ['<button class="chip active" data-genre="">すべて</button>']
    for g in genres:
        icon = GENRE_ICONS.get(g, "🛒")
        chips.append(
            f'<button class="chip" data-genre="{html.escape(g)}">'
            f'{icon} {html.escape(g)}</button>'
        )

    # 商品データをJSONとしてページに埋め込む（JSがこれを検索/描画する）
    data_json = json.dumps(products, ensure_ascii=False).replace("</", "<\\/")

    body = f"""  <main>
    <div class="toolbar">
      <div class="wrap">
        <div class="search">
          <svg viewBox="0 0 24 24"><path d="M21 20l-5.6-5.6a7 7 0 10-1.4 1.4L20 21zM4 10a6 6 0 1112 0 6 6 0 01-12 0z"/></svg>
          <input id="q" type="search" placeholder="商品名・キーワードで検索（例: モバイルバッテリー）" autocomplete="off">
        </div>
        <div class="chips" id="chips">
          {''.join(chips)}
        </div>
      </div>
    </div>

    <div class="wrap">
      <div class="meta-row">
        <div class="count" id="count"></div>
        <label class="sort">並び替え
          <select id="sort">
            <option value="default">おすすめ順</option>
            <option value="name">名前順（あ→ん / A→Z）</option>
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
    const grid  = document.getElementById('grid');
    const empty = document.getElementById('empty');
    const count = document.getElementById('count');
    const q     = document.getElementById('q');
    const sortSel = document.getElementById('sort');
    let activeGenre = "";

    function escapeHtml(s){{
      return s.replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    }}

    function cardHtml(p){{
      const thumb = p.image
        ? `<div class="thumb"><img src="${{p.image}}" alt="${{escapeHtml(p.name)}}" loading="lazy"></div>`
        : `<div class="thumb" style="background:linear-gradient(135deg, ${{p.grad}})"><span>${{p.icon}}</span></div>`;
      const reason = p.reason
        ? `<div class="reason"><b>推しポイント</b>：${{escapeHtml(p.reason)}}</div>` : '';
      return `
        <div class="card">
          ${{thumb}}
          <div class="body">
            <span class="badge">${{p.icon}} ${{escapeHtml(p.genre)}}</span>
            <div class="name">${{escapeHtml(p.name)}}</div>
            ${{reason}}
            <div class="comment">${{escapeHtml(p.comment || '')}}</div>
            <a class="btn" href="${{p.url}}" target="_blank" rel="noopener sponsored">Amazonで見る</a>
          </div>
        </div>`;
    }}

    function render(){{
      const kw = q.value.trim().toLowerCase();
      let list = PRODUCTS.filter(p => {{
        const okGenre = !activeGenre || p.genre === activeGenre;
        const okKw = !kw || (p.name + ' ' + (p.comment||'')).toLowerCase().includes(kw);
        return okGenre && okKw;
      }});

      const mode = sortSel.value;
      if(mode === 'name')  list = [...list].sort((a,b)=>a.name.localeCompare(b.name,'ja'));
      if(mode === 'genre') list = [...list].sort((a,b)=>a.genre.localeCompare(b.genre,'ja'));

      grid.innerHTML = list.map(cardHtml).join('');
      count.textContent = `${{list.length}} 件を表示中`;
      empty.classList.toggle('show', list.length === 0);
    }}

    // 検索（入力するたびに即フィルタ）
    q.addEventListener('input', render);
    sortSel.addEventListener('change', render);

    // ジャンルチップ
    document.getElementById('chips').addEventListener('click', e => {{
      const btn = e.target.closest('.chip');
      if(!btn) return;
      activeGenre = btn.dataset.genre;
      document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      render();
    }});

    render();
  </script>"""

    extra_css = index_css()
    # index は page_shell の .page を使わず main を直接入れるので、専用に組む
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(SITE_DESC)}">
  <title>{html.escape(SITE_NAME)}</title>
  <style>{base_css()}{extra_css}</style>
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <h1>🛍️ {html.escape(SITE_NAME)}</h1>
      <p>{html.escape(SITE_DESC)}</p>
    </div>
{nav_html()}
  </header>
{body}
{footer_html()}
</body>
</html>"""


def build_about():
    body = """  <div class="wrap page">
    <h2>このサイトについて</h2>
    <p>
      「Amazon売れ筋ピックアップ」は、Amazonで買えるアイテムの中から
      「長く使える」「買ってよかった」と思える定番を、ジャンル別に厳選して
      紹介するサイトです。数ある商品から選ぶ手間を少しでも減らせるよう、
      実用性を重視してまとめています。
    </p>
    <h2>選び方について</h2>
    <p>
      掲載しているアイテムは、定番として広く使われているものや、用途がはっきりした
      ものを中心に選んでいます。価格・在庫・最新のレビューは、各リンク先の
      Amazonのページでご確認ください。
    </p>
    <h2>運営者</h2>
    <p>個人で運営しています。お問い合わせは今後フォームを設置予定です。</p>
  </div>"""
    return page_shell("このサイトについて", body)


def build_privacy():
    body = """  <div class="wrap page">
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
    return page_shell("プライバシーポリシー", body)


def main():
    print("1) 商品データを読み込み中...")
    products = load_products()
    print(f"   {len(genre_order(products))} ジャンル / {len(products)} 商品 を使います。")

    os.makedirs(OUT_DIR, exist_ok=True)
    pages = {
        "index.html":   build_index(products),
        "about.html":   build_about(),
        "privacy.html": build_privacy(),
    }

    print("2) サイトを生成中...")
    for filename, content in pages.items():
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write(content)
        print(f"   作成: {path}")

    print("完成! docs/index.html をブラウザで開くと確認できます。")


if __name__ == "__main__":
    main()

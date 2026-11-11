#!/usr/bin/env python3
"""Build the anti-ghostsec.github.io site.

Pulls each project's description and rendered README from GitHub (through the
`gh` CLI) and writes static HTML pages, sitemap.xml and robots.txt into the
repository root. Run from anywhere:  python3 tools/build.py
"""
import datetime
import html
import json
import re
import subprocess
from pathlib import Path

OWNER = "anti-ghostsec"
SITE = f"https://{OWNER}.github.io"
GH = f"https://github.com/{OWNER}"
ROOT = Path(__file__).resolve().parent.parent
SITE_NAME = "anti-ghostsec"
TAGLINE = "Private, open-source software for people who'd rather not be watched"
HOME_DESC = ("Open-source privacy software, mostly in Rust: FerroOS (a hardened Linux with a "
             "Windows 95 desktop), a private web browser, Matrix client, text editor, PDF app, "
             "video editor, encrypted Android vault and Tor tools. No telemetry.")
# Optional: paste the content="..." value of Google's or Bing's verification meta tag here.
GOOGLE_VERIFY = ""
BING_VERIFY = ""

# slug, repo, emoji, group, SEO title (what people would search for), extra keywords
PROJECTS = [
    ("ferroos", "FerroOS", "⭐", "flagship",
     "FerroOS: privacy-first hardened Linux with a Windows 95 desktop",
     "privacy linux distro, windows 95 linux, hardened debian, duress pin, full disk encryption, tor, steam proton"),
    ("wisp", "wisp", "🌐", "apps",
     "Wisp: small privacy-focused web browser for Linux (Rust, WebKitGTK, GTK 4)",
     "private browser, privacy browser linux, rust web browser, webkitgtk browser, gtk4 browser"),
    ("whisker", "whisker", "💬", "apps",
     "Whisker: privacy-focused Matrix client in Rust with multiple accounts",
     "matrix client, rust matrix client, multi account matrix, encrypted chat, linux windows android"),
    ("folio", "folio", "📝", "apps",
     "Folio: calm, private text editor for Linux (GTK 4)",
     "text editor linux, distraction free editor, private text editor, writing app linux"),
    ("leaflet", "leaflet", "📄", "apps",
     "Leaflet: private PDF reader, form filler and annotator for Linux",
     "pdf reader linux, annotate pdf linux, fill pdf forms, docx odt editor, remove pdf metadata"),
    ("flicker", "Flicker", "🎬", "apps",
     "Flicker: light, private video editor in Rust with a Windows 95 look",
     "video editor rust, lightweight video editor linux, remove video metadata, encrypted video projects"),
    ("enclave", "Enclave", "🗄️", "apps",
     "Enclave: encrypted file vault for Android with no internet permission",
     "android encrypted vault, file locker android, duress password, decoy vault, no internet permission"),
    ("sentinel-protocol", "The-Sentinel-Protocol", "🛡️", "networks",
     "The Sentinel Protocol: social network and messenger over Tor, no phone number",
     "tor messenger, anonymous social network, decentralized messenger, no phone number messenger"),
    ("torus", "Torus", "🍩", "networks",
     "Torus: host a website as a Tor onion service from your PC or Android phone",
     "host onion site, tor hidden service windows, onion website android, self host tor"),
    ("anoncode", "AnonCode", "🤖", "tools",
     "AnonCode: private AI coding agent with an encrypted project vault",
     "private ai coding agent, opencode, encrypted vault, local ai coding assistant"),
    ("bettersearch", "BetterSearch", "🖼️", "tools",
     "BetterSearch: desktop booru search in Rust with boolean queries",
     "booru search app, booru desktop client, rust image search, encrypted local vault"),
    ("nuba", "nuba", "🌙", "tools",
     "Nuba: fast, privacy-friendly anime tracker with no email and no JavaScript",
     "anime tracker, myanimelist alternative, anilist alternative, private anime list"),
    ("vidgrab", "vidgrab", "⬇️", "tools",
     "vidgrab: LibreWolf and Firefox add-on to download videos with yt-dlp",
     "firefox video downloader, librewolf addon, yt-dlp extension, youtube downloader addon"),
    ("cutframe", "CutFrame", "✂️", "tools",
     "CutFrame: cross-platform Rust video tool for subtitles and editing",
     "embed subtitles video, burn subtitles, rust video tool, windows linux android"),
]
GROUPS = [
    ("flagship", "Flagship"),
    ("apps", "Apps"),
    ("networks", "Networks without a company in the middle"),
    ("tools", "Tools"),
]


def gh(path, accept=None):
    cmd = ["gh", "api", path]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def repo_info(repo):
    info = json.loads(gh(f"repos/{OWNER}/{repo}"))
    rel = gh(f"repos/{OWNER}/{repo}/releases/latest")
    info["_release"] = json.loads(rel) if rel else None
    info["_readme"] = gh(f"repos/{OWNER}/{repo}/readme", "application/vnd.github.html+json") or ""
    return info


def clean_readme(raw, repo, branch):
    blob = f"{GH}/{repo}/blob/{branch}/"
    rawbase = f"https://raw.githubusercontent.com/{OWNER}/{repo}/{branch}/"
    s = raw
    # drop the README's own <h1> block; the page supplies its own
    s = re.sub(r'<div class="markdown-heading"[^>]*><h1.*?</div>', "", s, count=1, flags=re.S)
    s = re.sub(r'<svg[^>]*class="octicon[^"]*".*?</svg>', "", s, flags=re.S)
    s = s.replace('id="user-content-', 'id="')
    s = re.sub(r'(src)="(?!https?:|data:|#|/)([^"]+)"', lambda m: f'{m[1]}="{rawbase}{m[2]}"', s)
    s = re.sub(r'(href)="(?!https?:|mailto:|#|/)([^"]+)"', lambda m: f'{m[1]}="{blob}{m[2]}"', s)
    s = re.sub(r'(src)="/([^"]+)"', lambda m: f'{m[1]}="https://github.com/{m[2]}"', s)
    s = re.sub(r'<img ', '<img loading="lazy" decoding="async" ', s)
    return s


def first_image(readme_html):
    m = re.search(r'<img[^>]+src="(https://raw\.githubusercontent\.com/[^"]+\.(?:png|jpe?g|webp))"', readme_html)
    return m[1] if m else None


def esc(s):
    return html.escape(s or "", quote=True)


def trim(s, n=158):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


CSS = """
:root{--bg:#fbfbf8;--fg:#1d1f21;--muted:#5d6166;--card:#fff;--line:#e3e3dc;--accent:#007a7a;--accent-ink:#fff;--code:#f1f1ec}
@media (prefers-color-scheme:dark){:root{--bg:#121416;--fg:#e8e8e3;--muted:#9ea3a8;--card:#1a1d20;--line:#2b2f33;--accent:#3cbcbc;--accent-ink:#071414;--code:#202428}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}img{max-width:100%;height:auto}
.wrap{max-width:960px;margin:0 auto;padding:0 16px}
header.top{border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;gap:16px;align-items:center;justify-content:space-between;padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.brand{font-weight:700;color:var(--fg);text-decoration:none;letter-spacing:.2px}
nav a{margin-left:14px;color:var(--muted);text-decoration:none}nav a:hover{color:var(--accent)}
.hero{padding:48px 0 24px}.hero h1{font-size:clamp(28px,5vw,42px);line-height:1.15;margin:0 0 12px}
.hero p{color:var(--muted);font-size:18px;max-width:680px;margin:0}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.chip{border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:14px;color:var(--muted)}
h2.group{margin:40px 0 14px;font-size:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;display:flex;flex-direction:column;gap:6px;text-decoration:none;color:var(--fg)}
.card:hover{border-color:var(--accent)}.card h3{margin:0;font-size:17px}.card p{margin:0;color:var(--muted);font-size:15px}
.card .meta{font-size:13px;color:var(--muted);margin-top:auto;padding-top:6px}
.flag{display:grid;grid-template-columns:1fr;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;text-decoration:none;color:var(--fg)}
@media(min-width:760px){.flag{grid-template-columns:1.3fr 1fr;align-items:center}}
.flag img{border-radius:8px;border:1px solid var(--line)}.flag h3{margin:0 0 6px;font-size:22px}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.btn{display:inline-block;padding:9px 16px;border-radius:8px;border:1px solid var(--accent);text-decoration:none;font-weight:600}
.btn.primary{background:var(--accent);color:var(--accent-ink)}
.crumbs{font-size:14px;color:var(--muted);padding-top:20px}.crumbs a{color:var(--muted)}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 0}
article.readme{border-top:1px solid var(--line);margin-top:24px;padding-top:8px;overflow-wrap:anywhere}
article.readme table{border-collapse:collapse;display:block;overflow-x:auto;max-width:100%}
article.readme th,article.readme td{border:1px solid var(--line);padding:6px 10px;vertical-align:top}
article.readme pre{background:var(--code);padding:12px;border-radius:8px;overflow-x:auto}
article.readme code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:.92em}article.readme pre code{padding:0;background:none}
article.readme blockquote{margin:0;padding:4px 16px;border-left:3px solid var(--line);color:var(--muted)}
article.readme .markdown-heading{position:relative}article.readme a.anchor{display:none}
.principles li{margin:6px 0}
footer{border-top:1px solid var(--line);margin-top:56px;padding:22px 0;color:var(--muted);font-size:14px}
"""


def page(path, title, desc, body, jsonld, image=None, keywords=""):
    url = SITE + path
    image = image or f"https://raw.githubusercontent.com/{OWNER}/FerroOS/ferro-os/docs/screenshots/heavy-desktop.png"
    verify = ""
    if GOOGLE_VERIFY:
        verify += f'<meta name="google-site-verification" content="{esc(GOOGLE_VERIFY)}">\n'
    if BING_VERIFY:
        verify += f'<meta name="msvalidate.01" content="{esc(BING_VERIFY)}">\n'
    kw = f'<meta name="keywords" content="{esc(keywords)}">\n' if keywords else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{kw}<meta name="author" content="{SITE_NAME}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}">
{verify}<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{esc(image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(image)}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/">{SITE_NAME}</a>
<nav><a href="/#projects">Projects</a><a href="{GH}">GitHub</a></nav></div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">Open source, no telemetry. Source code on <a href="{GH}">GitHub</a>.</div></footer>
</body>
</html>
"""


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    data = {}
    for slug, repo, *_ in PROJECTS:
        print("fetching", repo)
        data[slug] = repo_info(repo)

    person = {"@type": "Person", "@id": SITE + "/#author", "name": SITE_NAME, "url": SITE + "/",
              "sameAs": [GH]}
    lastmods = {}

    # ---- project pages
    for slug, repo, emoji, group, seo_title, kw in PROJECTS:
        d = data[slug]
        name = seo_title.split(":")[0]
        desc = trim(d.get("description"))
        branch = d["default_branch"]
        readme = clean_readme(d["_readme"], repo, branch)
        img = first_image(readme)
        lang = d.get("language") or ""
        rel = d["_release"]
        repo_url = d["html_url"]
        lastmods[f"/{slug}/"] = d["pushed_at"][:10]

        facts = [f'<span class="chip">{esc(lang)}</span>'] if lang else []
        lic = (d.get("license") or {}).get("spdx_id")
        if lic and lic != "NOASSERTION":
            facts.append(f'<span class="chip">{esc(lic)}</span>')
        if rel:
            facts.append(f'<span class="chip">Latest: {esc(rel["tag_name"])}</span>')
        facts.append(f'<span class="chip">Updated {d["pushed_at"][:10]}</span>')

        btns = [f'<a class="btn primary" href="{repo_url}">View source on GitHub</a>']
        if rel:
            btns.append(f'<a class="btn" href="{repo_url}/releases/latest">Download</a>')

        body = f"""<p class="crumbs"><a href="/">Home</a> › {esc(name)}</p>
<section class="hero" style="padding-top:12px">
<h1>{emoji} {esc(seo_title)}</h1>
<p>{esc(d.get("description"))}</p>
<div class="facts">{''.join(facts)}</div>
<div class="btns">{''.join(btns)}</div>
</section>
<article class="readme">
{readme}
</article>
<p><a href="{repo_url}">{esc(repo)} on GitHub</a> · <a href="/#projects">More projects</a></p>"""

        app = {"@type": "SoftwareApplication", "name": name, "description": d.get("description"),
               "url": f"{SITE}/{slug}/", "applicationCategory": "UtilitiesApplication",
               "operatingSystem": "Linux", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
               "author": {"@id": SITE + "/#author"}, "sameAs": [repo_url]}
        if slug == "enclave":
            app["operatingSystem"] = "Android"
        elif slug in ("whisker", "cutframe"):
            app["operatingSystem"] = "Linux, Windows, Android"
        elif slug == "torus":
            app["operatingSystem"] = "Windows, Android"
        elif slug == "vidgrab":
            app["operatingSystem"] = "Firefox, LibreWolf"
        elif slug == "nuba":
            app["@type"] = "WebApplication"
            app["operatingSystem"] = "Any"
        if img:
            app["screenshot"] = img
        if rel:
            app["softwareVersion"] = rel["tag_name"]
            app["downloadUrl"] = f"{repo_url}/releases/latest"
        code = {"@type": "SoftwareSourceCode", "name": repo, "codeRepository": repo_url,
                "programmingLanguage": lang or None, "author": {"@id": SITE + "/#author"},
                "targetProduct": {"@id": f"{SITE}/{slug}/#app"}}
        app["@id"] = f"{SITE}/{slug}/#app"
        crumbs = {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": f"{SITE}/{slug}/"}]}
        ld = {"@context": "https://schema.org", "@graph": [app, code, crumbs, person]}
        write(f"{slug}/index.html", page(f"/{slug}/", seo_title, desc, body, ld, img, kw))

    # ---- home page
    sections = []
    for gkey, gname in GROUPS:
        items = [p for p in PROJECTS if p[3] == gkey]
        if gkey == "flagship":
            slug, repo, emoji, _, seo_title, _ = items[0]
            d = data[slug]
            sections.append(f"""<h2 class="group">⭐ {gname}</h2>
<a class="flag" href="/{slug}/"><img src="https://raw.githubusercontent.com/{OWNER}/FerroOS/ferro-os/docs/screenshots/heavy-desktop.png" alt="The FerroOS desktop, styled like Windows 95" width="1280" height="800">
<div><h3>FerroOS</h3><p>{esc(d.get("description"))}</p><p class="meta">{esc(d.get("language") or "")}</p></div></a>""")
            continue
        cards = []
        for slug, repo, emoji, _, seo_title, _ in items:
            d = data[slug]
            name = seo_title.split(":")[0]
            cards.append(f"""<a class="card" href="/{slug}/"><h3>{emoji} {esc(name)}</h3>
<p>{esc(d.get("description"))}</p><span class="meta">{esc(d.get("language") or "")}</span></a>""")
        sections.append(f'<h2 class="group">{esc(gname)}</h2>\n<div class="grid">{"".join(cards)}</div>')

    body = f"""<section class="hero">
<h1>{esc(TAGLINE)}</h1>
<p>Small, fast, open-source programs, mostly written in Rust. Nothing phones home, files are saved without hidden metadata, and most of it runs fine on a 1&nbsp;GB machine.</p>
<div class="chips"><span class="chip">Rust</span><span class="chip">No telemetry</span><span class="chip">Tor built in</span><span class="chip">Open source</span></div>
<div class="btns"><a class="btn primary" href="/ferroos/">Try FerroOS</a><a class="btn" href="{GH}">Everything on GitHub</a></div>
</section>
<div id="projects">
{chr(10).join(sections)}
</div>
<h2 class="group">How everything here is built</h2>
<ul class="principles">
<li><strong>Nothing leaves your machine unless you ask.</strong> No telemetry, no analytics, no update pings behind your back.</li>
<li><strong>No traces in your files.</strong> Saved documents, photos and videos are stripped of author names, dates, GPS and program versions.</li>
<li><strong>Light by design.</strong> Most of it runs comfortably on a 1&nbsp;GB machine.</li>
<li><strong>Verifiable releases.</strong> Builds come from public CI, with checksums or signatures you can check.</li>
<li><strong>Honest about limits.</strong> Every README says what a project doesn't do yet.</li>
</ul>"""
    item_list = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{p[0]}/", "name": p[4].split(":")[0]}
        for i, p in enumerate(PROJECTS)]}
    website = {"@type": "WebSite", "@id": SITE + "/#site", "name": SITE_NAME, "url": SITE + "/",
               "description": HOME_DESC, "publisher": {"@id": SITE + "/#author"}}
    ld = {"@context": "https://schema.org", "@graph": [website, person, item_list]}
    home_kw = "privacy software, open source privacy apps, rust privacy, windows 95 linux, tor apps, no telemetry"
    write("index.html", page("/", f"{SITE_NAME}: {TAGLINE}", HOME_DESC, body, ld, keywords=home_kw))

    # ---- 404
    write("404.html", page("/404.html", f"Page not found · {SITE_NAME}", "This page doesn't exist.",
                           '<section class="hero"><h1>Page not found</h1><p><a href="/">Back to all projects</a></p></section>',
                           {"@context": "https://schema.org", "@type": "WebPage"}).replace(
        '<meta name="robots" content="index,follow,max-image-preview:large">', '<meta name="robots" content="noindex">'))

    # ---- sitemap + robots
    newest = max(lastmods.values())
    urls = [("/", newest, "1.0")] + [(f"/{p[0]}/", lastmods[f"/{p[0]}/"], "0.9" if p[3] == "flagship" else "0.8")
                                      for p in PROJECTS]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, lm, pr in urls:
        sm.append(f"  <url><loc>{SITE}{u}</loc><lastmod>{lm}</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print("built", len(PROJECTS) + 1, "pages at", datetime.date.today())


if __name__ == "__main__":
    main()

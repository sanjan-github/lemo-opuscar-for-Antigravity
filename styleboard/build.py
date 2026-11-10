# Lemo-Opuscar gallery: styles/*/style.json → catalog.json, index.html, and the generated parts of README.md, styles/README.md, AGENTS.md
# Local:          python3 styleboard/build.py                 (also refreshes each style.json "dur" from its mp4)
# GitHub Pages:   python3 styleboard/build.py --site _site
# README frames:  python3 styleboard/build.py --frames <slug>… (docs/frames/<slug>.jpg at the style's frame_sec)
import argparse, json, re, html, os, glob, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
CATALOG = os.path.join(HERE, 'catalog.json')   # generated; CI and tools/release.py read it

REPO = 'lemomo-ai/lemo-opuscar'
FILMS_URL = f'https://github.com/{REPO}/releases/download/films'   # full films live on the "films" release as <slug>.mp4
BLOB_URL = f'https://github.com/{REPO}/blob/main'

# The categories in gallery order. A style.json must name one of them.
CATEGORIES = [
    'Edit & Documentary', 'Evidence Films', 'Hand-drawn & Painting', 'East Asian Traditions', 'Print & Printmaking',
    'Graphic & Type', 'Information & Keynote', 'Cartoon & Anime',
    'Games', 'Cinema & Eras', 'Materials & 3D'
]
# The latest release's styles: the README shows them in a group of their own above the categories. Empty it to drop the group.
NEWEST = ('2026-10-29', ['memphis-diorama', 'transit-map', 'chalkboard', 'isometric-picture-book', 'printed-long-take', 'circuit-board', 'desktop-flythrough'])
FIELDS = ('slug', 'num', 'en', 'category_en', 'film', 'line', 'uses', 'frame_sec', 'dur')


def film_seconds(mp4):
    """Length of a film in seconds, or None when ffprobe can't read it (a half-rendered file, no ffprobe installed)."""
    try:
        d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4], capture_output=True, text=True).stdout)
    except (ValueError, OSError): return None
    return d if d > 0 else None


def load_styles(refresh_dur):
    """Every styles/<slug>/style.json (folders starting with _ are templates). Fails loudly on a missing field or an unknown category."""
    out, bad = [], []
    for p in sorted(glob.glob(os.path.join(ROOT, 'styles', '*', 'style.json'))):
        slug = os.path.basename(os.path.dirname(p))
        if slug.startswith('_'): continue
        j = json.load(open(p, encoding='utf-8'))
        miss = [f for f in FIELDS if f not in j]
        if miss: bad.append(f'styles/{slug}/style.json: missing {", ".join(miss)}'); continue
        if j['slug'] != slug: bad.append(f'styles/{slug}/style.json: slug is "{j["slug"]}", folder is "{slug}"')
        if j['category_en'] not in CATEGORIES:
            bad.append(f'styles/{slug}/style.json: unknown category "{j["category_en"]}" (see CATEGORIES in styleboard/build.py)')
        mp4 = os.path.join(ROOT, 'styles', slug, slug + '.mp4')
        if refresh_dur and os.path.exists(mp4):
            d = film_seconds(mp4)
            if d is None:
                print(f'WARNING: styles/{slug}/{slug}.mp4 exists but ffprobe cannot read its duration; keeping dur={j["dur"]}')
            elif round(d, 1) != j['dur']:
                j['dur'] = round(d, 1)
                open(p, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=1) + '\n')
        out.append(dict(slug=slug, num=j['num'], en=j['en'], cat_en=j['category_en'],
                        film=j['film'], line=j['line'], uses=j['uses'], dur=j['dur'], frame_sec=j['frame_sec'],
                        **({'by': j['by']} if j.get('by') else {})))
    if bad: raise SystemExit('styleboard/build.py:\n  ' + '\n  '.join(bad))
    order = {c: i for i, c in enumerate(CATEGORIES)}
    out.sort(key=lambda s: (order.get(s['cat_en'], 99), int(re.match(r'\d+', s['num']).group()), s['num']))
    return out


def grab_frames(styles, slugs):
    """docs/frames/<slug>.jpg for the README grid: one frame of the film at the style's frame_sec."""
    by = {s['slug']: s for s in styles}
    os.makedirs(os.path.join(ROOT, 'docs', 'frames'), exist_ok=True)
    for slug in slugs:
        s = by.get(slug) or exit(f'no style "{slug}"')
        mp4 = os.path.join(ROOT, 'styles', slug, slug + '.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s['frame_sec']), '-i', mp4, '-frames:v', '1', '-vf', 'scale=800:450', '-q:v', '3',
                        os.path.join(ROOT, 'docs', 'frames', slug + '.jpg')], check=True)
        print(f'docs/frames/{slug}.jpg ← {slug}.mp4 @ {s["frame_sec"]}s')


ap = argparse.ArgumentParser()
ap.add_argument('--site', help='build the GitHub Pages site into this folder (films from Releases)')
ap.add_argument('--frames', nargs='+', metavar='SLUG', help='only re-grab docs/frames/<slug>.jpg from the film at frame_sec, then stop')
args = ap.parse_args()
site = args.site

styles = load_styles(refresh_dur=not site and not args.frames)
if args.frames: grab_frames(styles, args.frames); raise SystemExit
if not site:
    json.dump([{k: v for k, v in s.items() if k != 'frame_sec'} for s in styles], open(CATALOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

if site:   # the public gallery only lists finished styles (with a STYLE.md)
    styles = [s for s in styles if os.path.exists(os.path.join(ROOT, 'styles', s['slug'], 'STYLE.md'))]
for s in styles:
    slug = s['slug']
    s['imgs'] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(HERE, 'img', slug + '_*.jpg')))
    has_poster = os.path.exists(os.path.join(ROOT, 'styles', slug, 'poster.jpg'))
    has_md = os.path.exists(os.path.join(ROOT, 'styles', slug, 'STYLE.md'))
    if site:
        s['video'] = f'films/{slug}.mp4' if s['dur'] else ''          # 720p web cut, served by Pages as video/mp4
        s['full'] = f'{FILMS_URL}/{slug}.mp4' if s['dur'] else ''       # full quality on Releases
        s['poster'] = f'posters/{slug}.jpg' if has_poster else ''
        s['stylemd'] = f'{BLOB_URL}/styles/{slug}/STYLE.md' if has_md else ''
    else:
        s['video'] = f'../styles/{slug}/{slug}.mp4' if os.path.exists(os.path.join(ROOT, 'styles', slug, slug + '.mp4')) else ''
        s['poster'] = f'../styles/{slug}/poster.jpg' if has_poster else ''
        s['stylemd'] = f'../styles/{slug}/STYLE.md' if has_md else ''

esc = lambda t: html.escape(t or '')

def laurel_symbol():
    import math
    leaves = []
    for side in (-1, 1):
        for i in range(9):
            a = math.radians(200 - i * 17) if side < 0 else math.radians(-20 + i * 17)
            cx, cy = 59 + 44 * math.cos(a), 34 + 27 * math.sin(a)
            rot = math.degrees(a) + (90 if side > 0 else -90) + side * 28
            leaves.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="2.3" ry="5.6" transform="rotate({rot:.1f} {cx:.1f} {cy:.1f})"/>')
    stems = '<path d="M22 50 Q10 30 24 10" fill="none" stroke="currentColor" stroke-width="1"/><path d="M96 50 Q108 30 94 10" fill="none" stroke="currentColor" stroke-width="1"/>'
    return f'<symbol id="laurel" viewBox="0 0 118 62"><g fill="currentColor">{"".join(leaves)}</g>{stems}</symbol>'

def mmss(d): r = round(d); return f'{r // 60}:{r % 60:02d}'

def by_line(s):
    b = s.get('by')
    if not b: return ''
    a = f'<a href="{esc(b["url"])}" target="_blank" rel="noopener">@{esc(b["name"])}</a>'
    return f'    <p class="by">Contributed by {a}</p>\n'

def card(s):
    img = f'img/{s["imgs"][0]}' if s['imgs'] else s.get('poster', '')
    vid = bool(s.get('video'))
    film = s.get('film') or s['en']
    main = f'<img class="still" src="{esc(img)}" alt="{esc(s["en"])} — {esc(film)}" loading="lazy">' if img else '<div class="empty">Coming soon</div>'
    play = (f'<button class="play" type="button" data-src="{esc(s["video"])}" data-poster="{esc(s.get("poster", ""))}" '
            f'aria-label="Play {esc(film)}"><i></i><span>{mmss(s["dur"])}</span></button>') if vid else ''
    uses = ''.join(f'<li>{esc(u)}</li>' for u in s.get('uses', []))
    links = []
    if vid: links.append(f'<a class="watch" href="{esc(s.get("full") or s["video"])}" data-play>Watch the film</a>')
    if s.get('stylemd'): links.append(f'<a href="{esc(s["stylemd"])}" target="_blank" rel="noopener">STYLE.md</a>')
    return (f'<article class="nominee" data-slug="{esc(s["slug"])}" data-en="{esc(s["en"])}" data-film="{esc(film)}">\n'
            f'  <div class="screen">{main}{play}</div>\n'
            f'  <div class="plate">\n'
            f'    <h3>{esc(s["en"])}</h3>\n'
            f'    <p class="for">for <em>{esc(film)}</em></p>\n'
            f'    <p class="line">{esc(s.get("line", ""))}</p>\n'
            f'{by_line(s)}'
            f'    {f"<ul class=uses aria-label=\"Best for\">{uses}</ul>" if uses else ""}\n'
            f'    <nav class="links">{"".join(links)}</nav>\n'
            f'  </div>\n</article>')

cats = [c for c in CATEGORIES if any(s['cat_en'] == c for s in styles)]
sections, tabs = [], []
for i, en in enumerate(cats, 1):
    group = [s for s in styles if s['cat_en'] == en]
    sid = re.sub(r'[^a-z0-9]+', '-', en.lower()).strip('-')
    tabs.append(f'<button data-f="{sid}">{esc(en)}</button>')
    sections.append(
        f'<section class="category" id="{sid}">\n'
        f'  <header class="cat-head"><svg class="lf"><use href="#laurel"/></svg>'
        f'<div><p class="cat-no">Category {i:02d}</p><h2>{esc(en)}</h2><p class="cat-count">{len(group)} nominees</p></div>'
        f'<svg class="lf"><use href="#laurel"/></svg></header>\n'
        f'  <div class="grid">\n' + '\n'.join(map(card, group)) + '\n  </div>\n</section>')

FEATURE = dict(poster='img/feature_opuscar98.jpg', dur='6:31',
               src='films/opuscar98.mp4' if site else '../.release/web/opuscar98.mp4', full=f'{FILMS_URL}/opuscar98.mp4')
n_vid = sum(bool(s.get('video')) for s in styles)
minutes = sum(s.get('dur', 0) for s in styles) / 60
n_all = len(styles)

SITE_URL = 'https://lemomo-ai.github.io/lemo-opuscar/'
REPO_URL = f'https://github.com/{REPO}'
AUTHOR = {'@type': 'Person', '@id': 'https://github.com/lemomo-ai', 'name': 'Lemomo', 'url': 'https://github.com/lemomo-ai',
          'sameAs': ['https://x.com/lemomo_ai', 'https://github.com/lemomo-ai']}
GALLERY_DESC = (f'Lemo-Opuscar: {n_all} film styles for Antigravity. Each style is a reusable prompt plus a short film made entirely in code. '
                'Includes OPUSCAR 98, 98 years of Best Picture. Official site of github.com/' + REPO + '.')
FILM_URL = SITE_URL + 'opuscar98/'
FILM_DESC = ('OPUSCAR 98: 98 Best Picture winners (1927 – 2025), each redrawn in a style that fits the film. '
             'Every frame, note and cut was written in code, with no video model.')
REPO_LD = {'@type': 'SoftwareSourceCode', '@id': REPO_URL, 'name': 'Lemo-Opuscar', 'url': REPO_URL, 'codeRepository': REPO_URL,
           'description': f'{n_all} film styles, each a style prompt plus a demo film made entirely in code, packaged for Antigravity.',
           'license': 'https://opensource.org/licenses/MIT', 'author': {'@id': AUTHOR['@id']},
           'keywords': ['Antigravity skill', 'film styles', 'no video model', 'motion graphics', 'creative coding']}

def head_meta(url, title, desc, image, ld):
    e = html.escape
    tags = [f'<link rel="canonical" href="{url}">',
            '<meta property="og:type" content="website">', '<meta property="og:site_name" content="Lemo-Opuscar">',
            f'<meta property="og:url" content="{url}">', f'<meta property="og:title" content="{e(title)}">',
            f'<meta property="og:description" content="{e(desc)}">', f'<meta property="og:image" content="{image}">',
            '<meta name="twitter:card" content="summary_large_image">', '<meta name="twitter:site" content="@lemomo_ai">',
            f'<meta name="twitter:title" content="{e(title)}">', f'<meta name="twitter:description" content="{e(desc)}">',
            f'<meta name="twitter:image" content="{image}">']
    data = json.dumps({'@context': 'https://schema.org', '@graph': ld}, ensure_ascii=False, indent=1).replace('</', '<\\/')
    return '\n'.join(tags) + f'\n<script type="application/ld+json">\n{data}\n</script>'

def mm_ss_iso(t):
    m, s = t.split(':'); return f'PT{int(m)}M{int(s)}S'

poster_abs = SITE_URL + FEATURE['poster']
gallery_meta = head_meta(SITE_URL, f'Lemo-Opuscar · {n_all} film styles for Antigravity, made in code', GALLERY_DESC, poster_abs,
                         [{'@type': 'CollectionPage', '@id': SITE_URL, 'url': SITE_URL, 'name': 'Lemo-Opuscar gallery', 'description': GALLERY_DESC,
                           'about': {'@id': REPO_URL}, 'author': {'@id': AUTHOR['@id']}, 'hasPart': {'@id': FILM_URL}}, REPO_LD, AUTHOR])
film_meta = head_meta(FILM_URL, 'OPUSCAR 98 · 98 Years of Best Picture, made in code', FILM_DESC, poster_abs,
                      [{'@type': 'VideoObject', '@id': FILM_URL, 'url': FILM_URL, 'name': 'OPUSCAR 98 · 98 Years of Best Picture',
                        'description': FILM_DESC, 'thumbnailUrl': poster_abs, 'uploadDate': '2026-09-29', 'duration': mm_ss_iso(FEATURE['dur']),
                        'contentUrl': FEATURE['full'], 'embedUrl': FILM_URL, 'inLanguage': 'en', 'creator': {'@id': AUTHOR['@id']},
                        'isBasedOn': {'@id': REPO_URL}}, REPO_LD, AUTHOR])

def fill(name, extra):
    page = open(os.path.join(HERE, name), encoding='utf-8').read()
    for k, v in {**extra, '{{N_ALL}}': str(n_all), '{{N_VID}}': str(n_vid), '{{N_CAT}}': str(len(cats)), '{{MIN}}': f'{minutes:.0f}',
                 '{{REPO_URL}}': REPO_URL, '{{REPO}}': REPO, '{{FEATURE_FULL}}': FEATURE['full'], '{{FEATURE_DUR}}': FEATURE['dur']}.items():
        page = page.replace(k, v)
    return page

out_dir = site or HERE
os.makedirs(os.path.join(out_dir, 'opuscar98'), exist_ok=True)
open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(fill('template.html', {
    '{{LAUREL}}': laurel_symbol(), '{{SECTIONS}}': '\n'.join(sections), '{{TABS}}': ''.join(tabs),
    '{{DESC}}': html.escape(GALLERY_DESC), '{{HEAD_META}}': gallery_meta,
    '{{FEATURE_POSTER}}': FEATURE['poster'], '{{FEATURE_SRC}}': FEATURE['src']}))

BOOK = json.load(open(os.path.join(HERE, 'opuscar98_styles.json'), encoding='utf-8'))

def stylebook():
    e = html.escape
    def hexes(t):
        return re.sub(r'#[0-9A-Fa-f]{6}\b', lambda m: f'<code><i style="background:{m[0]}"></i>{m[0]}</code>', e(t))
    def tc(t): return f'{int(t // 60)}:{int(t % 60):02d}'
    chs = {c['id']: c for c in BOOK['chapters']}
    def kind(dim):
        k = re.match(r'[\d.]+D', dim)[0]; return k, dim[len(k):].strip(' ·()')
    KIND_TIP = {'2D': 'Drawn flat, in layers', '2.5D': '3D models rendered into flat 2D layers', '3D': 'A real 3D scene and camera'}
    def short(y):
        a, b = y.split('–'); return f'{a}s' if a.endswith('0') and b.endswith('9') and a[:3] == b[:3] else f'{a}–{b[2:]}'
    buttons = ['<button type="button" data-ch="all" class="on"><b>98</b><span>All films</span></button>']
    buttons += [f'<button type="button" data-ch="{c["id"]}" title="{e(c["en"])}"><b>{short(c["years"])}</b><span>{e(c["en"])}</span></button>'
                for c in BOOK['chapters']]
    n_kind = {k: sum(kind(f['dim'])[0] == k for f in BOOK['films']) for k in KIND_TIP}
    kinds = '<button type="button" data-k="all" class="on">All</button>' + ''.join(
        f'<button type="button" data-k="{k}" title="{e(KIND_TIP[k])}">{k}<small>{n_kind[k]}</small></button>' for k in KIND_TIP)
    arts, last = [], None
    for f in BOOK['films']:
        if f['chapter'] != last:
            c = chs[f['chapter']]; last = f['chapter']
            arts.append(f'<h3 class="decade" data-ch="{c["id"]}"><span>{e(c["en"])}</span><small>{e(c["years"])}</small></h3>')
        no = f['no']; k, tone = kind(f['dim'])
        badge = (f'<span class="kind" data-k="{k}" title="{e(KIND_TIP[k])}">{k}'
                 + (f'<small>{e(tone)}</small>' if tone else '') + '</span>')
        q = ' '.join([f['title'], f['year'], f'no.{no}', k.lower(), f['style_en'], *f['blend_en'], *f['refs']]).lower()
        shots = ''.join(f'<li><p class="cam"><b>{e(s["cam"])}</b><i>{s["sec"]:.1f}s</i></p><p>{e(s["en"])}</p></li>' for s in f['shots'])
        arts.append(
            f'<article class="film" id="no-{no}" data-ch="{f["chapter"]}" data-k="{k}" data-tone="{e(tone)}" data-t0="{f["t0"]}" data-dur="{f["dur"]}" data-q="{e(q)}">\n'
            f' <button class="shot" type="button" data-t="{f["t0"]}" aria-label="Play No.{no} in the film">'
            f'<img loading="lazy" decoding="async" width="960" height="400" src="../img/opuscar98/{no:02d}.jpg" '
            f'alt="No.{no} {e(f["title"])} ({f["year"]}) in OPUSCAR 98, {e(f["style_en"])}"><span class="tc">▶ {tc(f["t0"])}</span></button>\n'
            f' <div class="txt">\n'
            f'  <p class="meta"><a class="no" href="#no-{no}">No.{no}</a><span>{e(f["year"])}</span>'
            f'<button class="qcopy copy-btn" type="button" title="Copy the style prompt">Copy prompt</button></p>\n'
            f'  <h4>{e(f["title"])}</h4>\n'
            f'  <p class="style">{badge}{e(f["style_en"])}</p>\n'
            f'  <ul class="blend">' + ''.join(f'<li>{e(a)}</li>' for a in f['blend_en']) + '</ul>\n'
            f'  <p class="desc">{e(f["desc_en"])}</p>\n'
            f'  <details><summary>Style prompt</summary>'
            f'<div class="prompt"><p>{hexes(f["prompt_en"])}</p><button class="copy copy-btn" type="button">Copy</button></div></details>\n'
            f'  <details><summary>Shots & direction</summary><ol class="shots">{shots}</ol>'
            f'<p class="dir">{e(f["direction_en"])}</p>'
            f'<p class="refs">References: {e(" · ".join(f["refs"]))}</p></details>\n'
            f' </div>\n</article>')
    return ''.join(buttons), kinds, '\n'.join(arts)

book_tabs, book_kinds, book_films = stylebook()
open(os.path.join(out_dir, 'opuscar98', 'index.html'), 'w', encoding='utf-8').write(fill('opuscar98.html', {
    '{{DESC}}': html.escape(FILM_DESC), '{{HEAD_META}}': film_meta,
    '{{FEATURE_POSTER}}': '../' + FEATURE['poster'], '{{FEATURE_SRC}}': '../' + FEATURE['src'],
    '{{BOOK_TABS}}': book_tabs, '{{BOOK_KINDS}}': book_kinds, '{{BOOK_FILMS}}': book_films}))

THANKS_REL = f'https://github.com/{REPO}/releases/download/thanks'
THANKS = [
    ('stars6000', '6,000 stars · The Quilt', '0:50', '2026-10-24',
     'One star, one patch: 6,000 stargazers sew a quilt for a library not yet a month old. A tiny figure falls asleep under it and dreams in the library\'s styles.'),
    ('stars3000', '3,000 stars · Class Photo', '0:48', '2026-10-19',
     'Figures in 25 of the library\'s styles squeeze into one class photo; it develops in the darkroom with every stargazer\'s name printed under it.'),
    ('stars2000', '2,000 stars · Refresh', '0:50', '2026-10-12',
     'One screen, seventeen days. Every count, name and timestamp is real: from the first git push to the 2,000th star, and a reply to the first issue.'),
    ('stars800', '800 stars · Reverse Shot', '0:39', '2026-10-03',
     'Watching the library\'s films in the projector beam until the film burns through; a reverse shot reveals 800 seats, each with a stargazer\'s name.'),
    ('stars300', '300 stars · The Lamplighter', '0:18', '2026-09-28',
     'In one continuous shot 300 stars are lit, each in a different style; pulled back, they spell 300.')
]
THANKS_URL = SITE_URL + 'thanks/'
THANKS_ALIAS = {'stars6000': 'stars5000'}
THANKS_DESC = 'Lemo-Opuscar thank-you films at 300, 800, 2,000, 3,000 and 6,000 GitHub stars, each made entirely in code, with no video model.'

def thanks_films():
    e = html.escape
    def one(f):
        fid, en, dur, day, d_en = f
        src = f'../films/{fid}.mp4' if site else f'../../.release/web/{fid}.mp4'
        alias = f'<span id="{THANKS_ALIAS[fid]}"></span>' if fid in THANKS_ALIAS else ''
        return (f'<section class="film" id="{fid}">{alias}<div class="frame"><video controls preload="metadata" playsinline poster="../img/thanks/{fid}.jpg" src="{src}"></video></div>\n'
                f' <div class="cap"><h2>{e(en)}</h2><span class="meta">{dur} · {day} · <a href="{THANKS_REL}/{fid}.mp4">1080p ↓</a></span></div>\n'
                f' <p class="desc">{e(d_en)}</p></section>')
    return one(THANKS[0]) + '\n<div class="pair">\n' + '\n'.join(one(f) for f in THANKS[1:]) + '\n</div>'

def iso(t): m, s_ = t.split(':'); return f'PT{int(m)}M{int(s_)}S'
thanks_meta = head_meta(THANKS_URL, 'Thank you for every star · Lemo-Opuscar', THANKS_DESC, SITE_URL + 'img/thanks/stars6000.jpg',
                        [{'@type': 'CollectionPage', '@id': THANKS_URL, 'url': THANKS_URL, 'name': 'Lemo-Opuscar thank-you films', 'description': THANKS_DESC,
                          'about': {'@id': REPO_URL}, 'author': {'@id': AUTHOR['@id']},
                          'hasPart': [{'@type': 'VideoObject', 'name': f[1], 'description': f[4], 'thumbnailUrl': SITE_URL + f'img/thanks/{f[0]}.jpg',
                                       'uploadDate': f[3], 'duration': iso(f[2]), 'contentUrl': f'{THANKS_REL}/{f[0]}.mp4', 'embedUrl': THANKS_URL + '#' + f[0]}
                                      for f in THANKS]}, REPO_LD, AUTHOR])
os.makedirs(os.path.join(out_dir, 'thanks'), exist_ok=True)
open(os.path.join(out_dir, 'thanks', 'index.html'), 'w', encoding='utf-8').write(fill('thanks.html', {
    '{{DESC}}': html.escape(THANKS_DESC), '{{HEAD_META}}': thanks_meta, '{{FILMS}}': thanks_films()}))

if site: shutil.copy(os.path.join(HERE, 'opuscar98_styles.json'), os.path.join(out_dir, 'opuscar98', 'styles.json'))

def llms_txt():
    out = ['# Lemo-Opuscar', '',
           f'> {n_all} film styles for Antigravity. Each style is a reusable style prompt (STYLE.md) plus a short demo film made entirely in code, with no video model.', '',
           f'Official repository: {REPO_URL} (by Lemomo, https://x.com/lemomo_ai).', '',
           '## Start here', '',
           f'- [README]({BLOB_URL}/README.md): what it is, how to use it, the style grid',
           f'- [Agent instructions]({BLOB_URL}/AGENTS.md): how an agent directs a film in one of the styles',
           f'- [Gallery]({SITE_URL}): every style with its demo film',
           f'- [OPUSCAR 98]({FILM_URL}): 98 Years of Best Picture ({FEATURE["dur"]})',
           f'- [Thank-you films]({THANKS_URL}): films made at 300, 800, 2,000, 3,000 and 6,000 stars', '']
    for en in cats:
        group = [x for x in styles if x['cat_en'] == en and x['stylemd']]
        if not group: continue
        out += [f'## {en}', '']
        out += [f'- [{s["en"]}]({BLOB_URL}/styles/{s["slug"]}/STYLE.md): {s["line"]}' for s in group]
        out.append('')
    return '\n'.join(out)

if site:
    shutil.copytree(os.path.join(HERE, 'img'), os.path.join(site, 'img'), dirs_exist_ok=True)
    os.makedirs(os.path.join(site, 'posters'), exist_ok=True)
    for s in styles:
        if s['poster']: shutil.copy(os.path.join(ROOT, 'styles', s['slug'], 'poster.jpg'), os.path.join(site, 'posters', s['slug'] + '.jpg'))
    open(os.path.join(site, 'llms.txt'), 'w', encoding='utf-8').write(llms_txt())
    open(os.path.join(site, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in (SITE_URL, FILM_URL, THANKS_URL)) + '</urlset>\n')

def readme_by(s):
    b = s.get('by')
    if not b: return ''
    a = f'<a href="{html.escape(b["url"])}">@{html.escape(b["name"])}</a>'
    return f'<br><sub>Contributed by {a}</sub>'

def readme_grid():
    out = []
    newest = [next(x for x in styles if x['slug'] == slug) for slug in NEWEST[1]]
    groups = [((f'🆕 New · {NEWEST[0]}'), newest)] if newest else []
    groups += [(en, [x for x in styles if x['cat_en'] == en and x['stylemd'] and x['slug'] not in NEWEST[1]]) for en in cats]
    for title, group in groups:
        if not group: continue
        out.append(f'\n### {title}\n\n<table>')
        for i in range(0, len(group), 3):
            out.append('<tr>')
            for s in group[i:i + 3]:
                name, alt, line = f'<b>{html.escape(s["en"])}</b>', s['en'], s['line']
                out.append(f'<td width="33%" valign="top"><a href="styles/{s["slug"]}/STYLE.md"><img src="docs/frames/{s["slug"]}.jpg" alt="{html.escape(alt)}"></a><br>'
                           f'{name}<br><i>{html.escape(s["film"])}</i><br><sub>{html.escape(line)}</sub>{readme_by(s)}</td>')
            out.append('</tr>')
        out.append('</table>')
    return '\n'.join(out) + '\n'

p = os.path.join(ROOT, 'README.md')
if os.path.exists(p) and not site:
    t = open(p, encoding='utf-8').read()
    t2 = re.sub(r'(<!-- styles:start -->\n).*?(<!-- styles:end -->)', lambda m: m.group(1) + readme_grid() + m.group(2), t, flags=re.S)
    t2 = re.sub(r'<!--n-->\d+<!--/n-->', f'<!--n-->{sum(1 for x in styles if x["stylemd"])}<!--/n-->', t2)
    if t2 != t: open(p, 'w', encoding='utf-8').write(t2)

def style_index():
    out = ['# Style index', '',
           'Users name a style by its gallery name in English or by its folder. Find it here, then read `styles/<folder>/STYLE.md`.', '',
           '<!-- generated by styleboard/build.py from styles/*/style.json; do not edit by hand -->', '']
    for en in cats:
        group = [x for x in styles if x['cat_en'] == en and x['stylemd']]
        if not group: continue
        out += [f'## {en}', '', '| Style | Folder | Our demo |', '|---|---|---|']
        out += [f'| {s["en"]} | [`{s["slug"]}`]({s["slug"]}/STYLE.md) | *{s["film"]}* |' for s in group]
        out.append('')
    return '\n'.join(out)

def style_list():
    out = [f'All {sum(1 for x in styles if x["stylemd"])} styles:', '']
    for en in cats:
        group = [x for x in styles if x['cat_en'] == en and x['stylemd']]
        if not group: continue
        names = ', '.join(s['en'] for s in group)
        out.append(f'- **{en}** ({len(group)}): {names}')
    return '\n'.join(out) + '\n'

if not site:
    open(os.path.join(ROOT, 'styles', 'README.md'), 'w', encoding='utf-8').write(style_index())
    p = os.path.join(ROOT, 'AGENTS.md')
    t = open(p, encoding='utf-8').read()
    t2 = re.sub(r'(<!-- style-list:start -->\n).*?(<!-- style-list:end -->)', lambda m: m.group(1) + style_list() + m.group(2), t, flags=re.S)
    if t2 != t: open(p, 'w', encoding='utf-8').write(t2)

print(f'{len(styles)} styles ({n_vid} with film, {minutes:.0f} min) → {os.path.relpath(os.path.join(out_dir, "index.html"), ROOT)}')

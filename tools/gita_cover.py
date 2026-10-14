"""गीता शृंखला के लिए line-art cover (1200x675) बनाता है और JSON में featured_image भरता है।

उपयोग (repo root से):
  python3 tools/gita_cover.py reports/<file>.json "अध्याय 1 · भाग 1" "छोटा शीर्षक" "श्लोक 1–11 · अर्जुनविषादयोग"
"""
import html, json, math, os, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "tools", "fonts", "NotoSansDevanagari.ttf")
INK, BG, ACC = "#5b1d0f", "#fbf3e2", "#b4471f"


def chariot():
    s = []
    cx, cy, R = 330, 478, 92
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}"/><circle cx="{cx}" cy="{cy}" r="{R-12}"/>'
             f'<circle cx="{cx}" cy="{cy}" r="16"/><circle cx="{cx}" cy="{cy}" r="5"/>')
    for i in range(16):
        a = 2 * math.pi * i / 16
        s.append(f'<line x1="{cx+16*math.cos(a):.1f}" y1="{cy+16*math.sin(a):.1f}" '
                 f'x2="{cx+(R-12)*math.cos(a):.1f}" y2="{cy+(R-12)*math.sin(a):.1f}"/>')
    s.append('<path d="M190 400 L500 400 L500 300 Q500 262 462 258 L238 258 Q200 262 200 300 Z"/>')
    s.append('<path d="M214 388 L486 388"/><path d="M230 370 Q260 320 290 370 M300 370 Q330 320 360 370 '
             'M370 370 Q400 320 430 370 M440 370 Q462 330 482 370"/>')
    s.append('<path d="M206 258 Q350 140 494 258"/><path d="M232 258 Q350 168 468 258"/>')
    for x in (230, 290, 350, 410, 470):
        s.append(f'<path d="M{x} 258 l0 12 m-6 0 a6 6 0 0 0 12 0"/>')
    s.append('<line x1="350" y1="186" x2="350" y2="70"/><path d="M350 74 Q395 62 440 80 Q408 92 446 112 Q398 98 350 112"/>')
    s.append('<circle cx="350" cy="66" r="5"/>')
    s.append('<path d="M190 380 Q120 372 52 352"/><path d="M190 392 Q120 386 52 366"/><path d="M52 340 L52 378"/>')
    s.append('<path d="M520 230 Q590 330 520 430"/><line x1="520" y1="230" x2="520" y2="430" stroke-width="1.6"/>')
    s.append('<path d="M30 572 L650 572"/>')
    for x in range(48, 640, 46):
        s.append(f'<path d="M{x} 572 q4 -14 10 -18 M{x+8} 572 q2 -10 -4 -14"/>')
    s.append('<circle cx="560" cy="120" r="34"/>')
    for i in range(12):
        a = 2 * math.pi * i / 12
        s.append(f'<line x1="{560+44*math.cos(a):.1f}" y1="{120+44*math.sin(a):.1f}" '
                 f'x2="{560+60*math.cos(a):.1f}" y2="{120+60*math.sin(a):.1f}"/>')
    return "".join(s)


def lotus(x, y, sc=1.0):
    return (f'<g transform="translate({x},{y}) scale({sc})"><path d="M0 0 Q-10 -22 0 -40 Q10 -22 0 0 Z '
            f'M0 0 Q-26 -12 -32 -30 Q-12 -26 0 0 M0 0 Q26 -12 32 -30 Q12 -26 0 0 M-40 4 Q0 14 40 4"/></g>')


def build(label, title, sub):
    border = ('<rect x="18" y="18" width="1164" height="639" rx="6"/>'
              '<rect x="30" y="30" width="1140" height="615" rx="4" stroke-width="1.2"/>'
              + lotus(600, 52, 0.7) + lotus(600, 640, 0.7))
    tsize = 44 if len(title) <= 28 else 36
    return f"""<html><head><meta charset="utf-8"><style>
@font-face{{font-family:'Noto';src:url('file://{FONT}');}}
body{{margin:0;width:1200px;height:675px;background:{BG};font-family:'Noto','DejaVu Sans',sans-serif;color:{INK};overflow:hidden}}
svg{{position:absolute;left:0;top:0}} .t{{position:absolute;left:690px;right:70px}}
</style></head><body>
<svg width="1200" height="675" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{border}
<g transform="translate(20,20)">{chariot()}</g>
<line x1="672" y1="110" x2="672" y2="565" stroke="{ACC}" stroke-width="1.5" stroke-dasharray="2 8"/></svg>
<div class="t" style="top:110px;font-size:26px;color:{ACC};font-weight:700">श्रीमद्भगवद्गीता</div>
<div class="t" style="top:160px;font-size:46px;font-weight:700">{html.escape(label)}</div>
<div class="t" style="top:250px;font-size:{tsize}px;font-weight:700;line-height:1.3">{html.escape(title)}</div>
<div class="t" style="top:445px;font-size:28px;border-top:2px solid {INK};padding-top:14px">{html.escape(sub)}</div>
<div class="t" style="top:555px;font-size:24px;color:{ACC}">देसी ललकार · गीता शृंखला</div>
</body></html>"""


def main(path, label, title, sub):
    base = os.path.splitext(os.path.basename(path))[0]
    out_rel = f"images/{base}-cover.png"
    out = os.path.join(os.path.dirname(os.path.abspath(path)), out_rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 675})
        pg.set_content(build(label, title, sub))
        pg.wait_for_timeout(300)
        pg.screenshot(path=out)
        b.close()
    r = json.load(open(path, encoding="utf-8"))
    r["featured_image"] = out_rel
    r.pop("image_search", None)  # line-art cover ही दिखे, Wikimedia तस्वीर नहीं
    json.dump(r, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("✅", "reports/" + out_rel)


if __name__ == "__main__":
    main(*sys.argv[1:5])

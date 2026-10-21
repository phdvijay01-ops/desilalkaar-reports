"""भक्ति कथा के लिए line-art cover (1200x675) — गीता शृंखला वाली शैली में, पर सामान्य motif के साथ।

उपयोग (repo root से):
  python3 tools/bhakti_lineart_cover.py reports/<file>.json "<ग्रंथ/परंपरा>" "<छोटा शीर्षक, ~28 अक्षर>" "<उप-पंक्ति>" [motif]
motif: moon (चाँद-बाँसुरी, default) | temple (शिखर-मंदिर) | diya (दीपक) | river (नदी-घाट)
उदाहरण:
  python3 tools/bhakti_lineart_cover.py reports/x-bhakti.json "श्रीमद्भागवत" "शरद पूर्णिमा की रास-लीला" "दशम स्कंध · अध्याय 29–33" moon
यह reports/images/<file>-cover.png लिखता है, JSON में featured_image भरता है और image_search हटा देता है।
"""
import html, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gita_cover import FONT, INK, BG, ACC, lotus  # same palette & font as गीता cover
from playwright.sync_api import sync_playwright


def ground():
    s = ['<path d="M30 572 L650 572"/>']
    for x in range(48, 640, 46):
        s.append(f'<path d="M{x} 572 q4 -14 10 -18 M{x+8} 572 q2 -10 -4 -14"/>')
    return "".join(s)


def moon():
    s = ['<circle cx="430" cy="150" r="70"/><circle cx="430" cy="150" r="56" stroke-width="1.4"/>']
    for x, y in ((300, 90), (560, 110), (520, 230), (330, 220), (600, 60)):  # तारे (सूरज जैसी किरणें नहीं)
        s.append(f'<path d="M{x} {y-9} L{x} {y+9} M{x-9} {y} L{x+9} {y}" stroke-width="1.6"/>')
    # kadamba tree
    s.append('<path d="M150 572 L150 360 M150 430 Q120 400 96 392 M150 400 Q182 370 212 366"/>')
    for cx, cy, r in ((150, 300, 70), (92, 360, 44), (214, 350, 46)):
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')
        for k in range(6):
            a = 2 * math.pi * k / 6
            s.append(f'<circle cx="{cx+r*0.5*math.cos(a):.1f}" cy="{cy+r*0.5*math.sin(a):.1f}" r="4"/>')
    # flute with peacock feather
    s.append('<path d="M250 470 L560 400"/><path d="M252 480 L562 410"/>')
    for t in range(6):
        x = 330 + t * 36; y = 455 - t * 8
        s.append(f'<circle cx="{x}" cy="{y}" r="3.5"/>')
    s.append('<path d="M560 405 Q610 360 600 300 Q580 340 560 405"/><ellipse cx="596" cy="318" rx="12" ry="18"/>'
             '<circle cx="596" cy="320" r="6"/>')
    # river waves
    for y in (520, 540):
        s.append(f'<path d="M260 {y} q20 -10 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0"/>')
    return "".join(s) + ground()


def temple():
    s = ['<path d="M200 572 L200 360 L500 360 L500 572"/><path d="M180 360 L520 360"/>',
         '<path d="M230 360 Q260 200 350 110 Q440 200 470 360"/><path d="M270 360 Q290 240 350 160 Q410 240 430 360"/>',
         '<line x1="350" y1="110" x2="350" y2="50"/><path d="M350 54 L392 66 L350 80"/><circle cx="350" cy="104" r="8"/>',
         '<path d="M310 572 L310 450 Q350 400 390 450 L390 572"/>']
    for x in (230, 270, 430, 470):
        s.append(f'<path d="M{x} 572 L{x} 400"/>')
    for y in (200, 250, 300):
        s.append(f'<path d="M{350-(y-110)*0.75:.0f} {y} L{350+(y-110)*0.75:.0f} {y}" stroke-width="1.4"/>')
    s.append('<circle cx="580" cy="120" r="30"/>')
    return "".join(s) + ground()


def diya():
    s = ['<path d="M220 440 Q350 540 480 440 Q350 470 220 440 Z"/><path d="M250 470 Q350 530 450 470"/>',
         '<path d="M350 436 Q320 380 350 300 Q380 380 350 436 Z"/><path d="M350 420 Q338 390 350 350 Q362 390 350 420 Z"/>',
         '<path d="M300 520 L400 520 L380 560 L320 560 Z"/>']
    for i in range(10):
        a = math.pi + math.pi * i / 9
        s.append(f'<line x1="{350+120*math.cos(a):.1f}" y1="{360+120*math.sin(a):.1f}" '
                 f'x2="{350+150*math.cos(a):.1f}" y2="{360+150*math.sin(a):.1f}"/>')
    s.append(lotus(150, 560, 1.1) + lotus(550, 560, 1.1))
    return "".join(s) + ground()


def river():
    s = ['<path d="M90 300 L90 190 L170 190 L170 300 M70 190 L190 190 M100 190 Q130 120 160 190"/>',
         '<line x1="130" y1="140" x2="130" y2="100"/><path d="M130 104 L160 112 L130 120"/>']
    for i, y in enumerate(range(300, 420, 24)):
        s.append(f'<path d="M{40+i*10} {y} L{260+i*30} {y}"/>')
    for y in (440, 470, 500, 530):
        s.append(f'<path d="M60 {y} q25 -12 50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0"/>')
    s.append('<circle cx="500" cy="140" r="40"/>' + lotus(470, 470, 0.9))
    return "".join(s) + '<path d="M30 572 L650 572"/>'


MOTIFS = {"moon": moon, "temple": temple, "diya": diya, "river": river}


def build(label, title, sub, motif):
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
<g transform="translate(20,20)">{MOTIFS.get(motif, moon)()}</g>
<line x1="672" y1="110" x2="672" y2="565" stroke="{ACC}" stroke-width="1.5" stroke-dasharray="2 8"/></svg>
<div class="t" style="top:110px;font-size:26px;color:{ACC};font-weight:700">भक्ति · कथा</div>
<div class="t" style="top:160px;font-size:42px;font-weight:700">{html.escape(label)}</div>
<div class="t" style="top:250px;font-size:{tsize}px;font-weight:700;line-height:1.3">{html.escape(title)}</div>
<div class="t" style="top:445px;font-size:28px;border-top:2px solid {INK};padding-top:14px">{html.escape(sub)}</div>
<div class="t" style="top:555px;font-size:24px;color:{ACC}">देसी ललकार · भक्ति</div>
</body></html>"""


def main(path, label, title, sub, motif="moon"):
    base = os.path.splitext(os.path.basename(path))[0]
    out_rel = f"images/{base}-cover.png"
    out = os.path.join(os.path.dirname(os.path.abspath(path)), out_rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 675})
        pg.set_content(build(label, title, sub, motif))
        pg.wait_for_timeout(300)
        pg.screenshot(path=out)
        b.close()
    r = json.load(open(path, encoding="utf-8"))
    r["featured_image"] = out_rel
    r.pop("image_search", None)  # line-art cover ही दिखे
    json.dump(r, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("✅", "reports/" + out_rel)


if __name__ == "__main__":
    main(*sys.argv[1:6])

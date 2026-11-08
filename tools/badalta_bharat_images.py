#!/usr/bin/env python3
""""बदलता भारत" शृंखला की images (देसी ललकार branding के साथ) बनाता है।

python3 tools/badalta_bharat_images.py <spec.json>

spec.json का रूप (कोई भी image छोड़नी हो तो उसकी key हटा दें):
{
 "prefix": "2026-10-30-ujjwala-yojana",          # images/<prefix>-<name>.png
 "part": 2,                                        # शृंखला का भाग
 "featured": {"title": "उज्ज्वला योजना", "subtitle": "...", "scene": "dbt",   # line-art cover; scene = SCENES की key
              "stats": [["10 करोड़+", "कनेक्शन"], ["..", ".."], ["..", ".."]], "source": "..."},
 "timeline": {"title": "...", "items": [["मई 2016", "शुरुआत"], ...], "source": "..."},   # 4–6 items
 "chart": {"title": "...", "subtitle": "...", "legend": ["2016", "2025"], "unit": "%",
           "groups": [["ग्रामीण", 37, 65], ...], "source": "..."},                    # 2–4 groups; या "values": [["label", 12], ...] एक series के लिए
 "asar": {"title": "...", "tiles": [["₹50,000", "विवरण", "स्रोत"], ...], "source": "..."},  # 4 tiles
 "mp": {"title": "...", "tiles": [["8वीं बार", "विवरण", ""], ...], "source": "..."}          # 4 tiles
}
Images reports/images/ में बनती हैं; हर PNG खोलकर जाँचें।
"""
import html
import json
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "tools", "fonts", "NotoSansDevanagari.ttf")
LOGO = "file://" + os.path.join(ROOT, "tools", "brand", "logo.png")
OUT = os.path.join(ROOT, "reports", "images")
e = html.escape

CSS = f"""
@font-face{{font-family:N;src:url('file://{FONT}')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1200px;height:675px;font-family:N,sans-serif;overflow:hidden;position:relative}}
.light{{background:#fbf7f2;color:#2a1414}}
.logo{{position:absolute;right:40px;top:24px;height:96px}}
.kicker{{position:absolute;left:56px;top:34px;font-weight:800;font-size:18px;color:#b8232a}}
.title{{position:absolute;left:56px;top:58px;width:920px;font-weight:800;font-size:36px;line-height:1.2;color:#5c0f12}}
.strip{{position:absolute;left:0;right:0;bottom:0;height:52px;background:#5c0f12;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 40px;font-size:17px}}
.strip b{{font-weight:800;font-size:19px;color:#ffcf3f}}
.rule{{position:absolute;left:0;right:0;bottom:52px;height:4px;background:linear-gradient(90deg,#ff9933 0 33%,#fff 33% 66%,#138808 66%)}}
.tile{{position:absolute;width:534px;height:180px;background:#fff;border:1px solid #ead9d2;border-left:7px solid #b8232a;border-radius:10px;padding:18px 26px}}
"""


def strip(src):
    return f'<div class="rule"></div><div class="strip"><span>{e(src)}</span><b>desilalkaar.com</b></div>'


def head(kicker, title, sub=""):
    s = f'<img class="logo" src="{LOGO}"><div class="kicker">बदलता भारत · {e(kicker)}</div><div class="title">{e(title)}</div>'
    if sub:
        s += f'<div style="position:absolute;left:58px;top:110px;font-size:20px;color:#5a4646">{e(sub)}</div>'
    return s


def featured(f, part):
    stats = "".join(
        f'<div style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.22);border-radius:10px;padding:12px 22px">'
        f'<div style="font-weight:800;font-size:38px;color:#ffcf3f">{e(a)}</div><div style="font-size:19px">{e(b)}</div></div>'
        for a, b in f["stats"][:3])
    return f"""<body style="background:linear-gradient(120deg,#4a0b0e 0%,#7d151a 50%,#a81f26 100%);color:#fff">
<div style="position:absolute;inset:0;background:radial-gradient(circle at 82% 55%,rgba(255,207,63,.16),transparent 40%)"></div>
<img src="{LOGO}" style="position:absolute;right:40px;top:28px;height:104px">
<div style="position:absolute;left:56px;top:48px;background:#ffcf3f;color:#4a0b0e;font-weight:800;font-size:22px;padding:5px 16px;border-radius:5px">बदलता भारत · भाग {part}</div>
<div style="position:absolute;left:56px;top:118px;width:900px;font-weight:800;font-size:{88 if len(f['title']) <= 18 else 68}px;line-height:1.05">{e(f['title'])}</div>
<div style="position:absolute;left:58px;top:236px;font-weight:700;font-size:42px;color:#ffe9b0">{e(f['subtitle'])}</div>
<div style="position:absolute;left:58px;top:300px;font-size:25px;opacity:.9">{e(f.get('line', ''))}</div>
<div style="position:absolute;left:56px;top:378px;display:flex;gap:20px">{stats}</div>
{strip(f['source'])}</body>"""


# ---------- line-art featured (prompts/line-art-featured-image-style.md) ----------
INK = "#3a1a12"


def _person(x, y, skin, cloth, scale=1.0, saree=False):
    """सरल खड़ा व्यक्ति; (x, y) = पैरों के बीच ज़मीन का बिंदु।"""
    k = scale
    head = f'<circle cx="{x}" cy="{y-190*k:.0f}" r="{24*k:.0f}" fill="{skin}"/>'
    if saree:
        body = (f'<path d="M{x-34*k:.0f} {y-160*k:.0f} Q{x} {y-176*k:.0f} {x+34*k:.0f} {y-160*k:.0f} '
                f'L{x+52*k:.0f} {y} L{x-52*k:.0f} {y} Z" fill="{cloth}"/>'
                f'<path d="M{x-30*k:.0f} {y-158*k:.0f} Q{x+10*k:.0f} {y-100*k:.0f} {x+48*k:.0f} {y-30*k:.0f}" fill="none"/>'
                f'<path d="M{x-24*k:.0f} {y-205*k:.0f} Q{x} {y-232*k:.0f} {x+24*k:.0f} {y-205*k:.0f} L{x+30*k:.0f} {y-150*k:.0f}" fill="none"/>')
    else:
        body = (f'<path d="M{x-32*k:.0f} {y-160*k:.0f} Q{x} {y-174*k:.0f} {x+32*k:.0f} {y-160*k:.0f} '
                f'L{x+28*k:.0f} {y-80*k:.0f} L{x-28*k:.0f} {y-80*k:.0f} Z" fill="{cloth}"/>'
                f'<path d="M{x-24*k:.0f} {y-80*k:.0f} L{x-20*k:.0f} {y} M{x+24*k:.0f} {y-80*k:.0f} L{x+20*k:.0f} {y} '
                f'M{x-26*k:.0f} {y-80*k:.0f} L{x+26*k:.0f} {y-80*k:.0f} L{x+22*k:.0f} {y-40*k:.0f} L{x-22*k:.0f} {y-40*k:.0f} Z" fill="#fff"/>')
    return body + head


def scene_dbt():
    s = []
    # आसमान के तत्व
    s.append('<circle cx="96" cy="96" r="40" fill="#ffd54f"/>')
    for i in range(10):
        a = 2 * 3.14159 * i / 10
        import math
        s.append(f'<line x1="{96+50*math.cos(a):.0f}" y1="{96+50*math.sin(a):.0f}" x2="{96+64*math.cos(a):.0f}" y2="{96+64*math.sin(a):.0f}"/>')
    s.append('<path d="M180 150 q20 -24 46 -8 q26 -22 50 4 q24 2 22 20 h-118 q-14 -8 0 -16 Z" fill="#fff"/>')
    # पहाड़ियाँ और ज़मीन
    s.append('<path d="M0 470 Q120 400 240 450 Q360 380 500 440 Q580 410 660 440 L660 580 L0 580 Z" fill="#e6f1d8"/>')
    s.append('<path d="M0 580 L660 580"/>')
    for x in range(20, 650, 52):
        s.append(f'<path d="M{x} 580 q4 -14 10 -18 M{x+8} 580 q2 -10 -4 -14"/>')
    # सरकारी भवन (₹ के साथ)
    s.append('<path d="M40 300 L160 236 L280 300 Z" fill="#90caf9"/><path d="M44 300 L276 300 L276 316 L44 316 Z" fill="#fff"/>')
    for x in (64, 112, 160, 208, 256):
        s.append(f'<rect x="{x-9}" y="316" width="18" height="214" fill="#fff"/>')
    s.append('<path d="M34 530 L286 530 L286 552 L34 552 Z" fill="#ffe0b2"/><path d="M24 552 L296 552 L296 580 L24 580 Z" fill="#fff"/>')
    s.append('<text x="160" y="290" text-anchor="middle" font-size="34" font-weight="800" fill="#b8232a" stroke="none">₹</text>')
    # पैसे का रास्ता: भवन से फ़ोन तक
    s.append('<path d="M250 250 Q430 60 610 280" fill="none" stroke="#b8232a" stroke-width="3.2" stroke-dasharray="10 9"/>')
    s.append('<path d="M598 266 L611 284 L620 262" fill="none" stroke="#b8232a" stroke-width="3.2"/>')
    for cx, cy in ((318, 172), (402, 132), (488, 160)):
        s.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="#ffca28"/><text x="{cx}" y="{cy+9}" text-anchor="middle" font-size="24" font-weight="800" fill="{INK}" stroke="none">₹</text>')
    # पहचान कार्ड (सामान्य, कोई लोगो नहीं)
    s.append('<rect x="306" y="236" width="128" height="80" rx="9" fill="#fff"/><rect x="318" y="250" width="34" height="42" rx="4" fill="#ffccbc"/>')
    s.append('<path d="M362 256 h56 M362 270 h44 M362 284 h52" stroke-width="2"/>')
    for r in (6, 11, 16):
        s.append(f'<path d="M{404-r} 304 a{r} {r} 0 0 1 {2*r} 0" fill="none" stroke-width="1.8"/>')
    # CSC/बैंक मित्र मेज़ और फ़िंगरप्रिंट मशीन; बुज़ुर्ग अंगूठा लगाते हुए
    s.append('<rect x="372" y="468" width="120" height="16" fill="#a1887f"/><path d="M384 484 L384 580 M480 484 L480 580"/>')
    s.append('<rect x="392" y="446" width="44" height="22" rx="5" fill="#cfd8dc"/><circle cx="426" cy="457" r="4" fill="#66bb6a"/>')
    s.append('<rect x="444" y="422" width="40" height="46" rx="4" fill="#fff"/><path d="M452 436 h24 M452 448 h16" stroke-width="2"/>')
    s.append(_person(330, 580, "#b97850", "#ffffff", 0.82))
    s.append('<path d="M356 448 Q384 446 404 452" fill="none"/>')
    # महिला, कान के पास फ़ोन पर पैसा आने का संदेश
    s.append(_person(580, 580, "#d49a6a", "#ffb74d", 1.0, saree=True))
    s.append('<path d="M612 422 Q630 400 622 372" fill="none"/>')
    s.append('<rect x="606" y="300" width="46" height="78" rx="8" fill="#e3f2fd"/><rect x="612" y="310" width="34" height="50" rx="3" fill="#bbdefb"/>')
    s.append('<text x="629" y="342" text-anchor="middle" font-size="22" font-weight="800" fill="#1b5e20" stroke="none">₹</text>')
    s.append('<path d="M598 286 q-10 8 0 16 M588 278 q-16 16 0 32" fill="none" stroke-width="2"/>')
    return "".join(s)


def scene_ujala():
    """उजाला: शाम का गांव-घर, छत से लटका LED बल्ब, पढ़ता बच्चा, पुराना बल्ब बनाम LED, बाहर LED स्ट्रीटलाइट।"""
    import math
    s = []
    # शाम का आसमान: चांद और तारे
    s.append('<rect x="0" y="0" width="660" height="580" fill="#e8ecf6" stroke="none"/>')
    s.append('<path d="M70 70 a34 34 0 1 0 40 46 a28 28 0 1 1 -40 -46 Z" fill="#fff3c4"/>')
    for x, y in ((170, 60), (240, 110), (130, 160), (300, 50)):
        s.append(f'<path d="M{x} {y-9} L{x} {y+9} M{x-9} {y} L{x+9} {y}" stroke-width="2.4"/>')
    # ज़मीन
    s.append('<path d="M0 580 L660 580" />')
    s.append('<path d="M0 560 Q160 548 330 560 Q500 572 660 556 L660 580 L0 580 Z" fill="#dfe9cf"/>')
    # LED स्ट्रीटलाइट (बाएं)
    s.append('<path d="M70 580 L70 250 Q70 222 100 222 L150 222" stroke-width="5"/>')
    s.append('<rect x="130" y="214" width="62" height="16" rx="5" fill="#cfd8dc"/>')
    s.append('<path d="M136 232 L112 330 L214 330 L186 232 Z" fill="#fff59d" stroke="none" opacity=".75"/>')
    s.append('<rect x="56" y="566" width="28" height="14" fill="#bdbdbd"/>')
    # घर: दीवार, छत, खुली खिड़कीनुमा कटाव
    s.append('<path d="M232 300 L432 190 L640 300 Z" fill="#e57373"/>')
    s.append('<rect x="248" y="300" width="380" height="270" fill="#fff8e1"/>')
    s.append('<path d="M248 570 L628 570"/>')
    # छत से लटका LED बल्ब और रोशनी
    s.append('<path d="M438 300 L438 344"/>')
    s.append('<path d="M370 380 L300 560 L580 560 L506 380 Z" fill="#fff176" stroke="none" opacity=".55"/>')
    s.append('<rect x="428" y="344" width="20" height="12" rx="2" fill="#b0bec5"/>')
    s.append('<path d="M424 356 Q410 372 422 388 Q438 400 454 388 Q466 372 452 356 Z" fill="#fffde7"/>')
    for i in range(7):
        a = math.pi * (0.15 + 0.7 * i / 6)
        s.append(f'<line x1="{438+38*math.cos(a):.0f}" y1="{374+38*math.sin(a)-0:.0f}" x2="{438+56*math.cos(a):.0f}" y2="{374+56*math.sin(a):.0f}" stroke="#f9a825" stroke-width="3"/>')
    # मेज़, किताब और पढ़ता बच्चा
    s.append('<rect x="370" y="486" width="170" height="14" fill="#a1887f"/><path d="M384 500 L384 566 M526 500 L526 566"/>')
    s.append('<path d="M410 486 L440 474 L470 486 L440 480 Z" fill="#fff"/><path d="M440 474 L440 486" stroke-width="2"/>')
    s.append('<circle cx="356" cy="452" r="18" fill="#c68b59"/>')
    s.append('<path d="M334 474 Q356 464 378 474 L384 540 L330 540 Z" fill="#64b5f6"/>')
    s.append('<path d="M374 486 Q392 484 412 480" fill="none"/>')
    s.append('<path d="M336 540 L330 566 M378 540 L384 566" />')
    # मां (साड़ी), हाथ में पुराना बल्ब
    s.append(_person(580, 566, "#d49a6a", "#ba68c8", 0.92, saree=True))
    # पुराना बल्ब बनाम LED (ऊपर दाएं, घर के बाहर)
    s.append('<circle cx="300" cy="240" r="0" />')
    s.append('<path d="M478 120 Q458 100 470 78 Q488 58 508 78 Q520 100 500 120 Z" fill="#ffe0b2"/><rect x="478" y="120" width="22" height="12" fill="#b0bec5"/>')
    s.append('<path d="M482 98 l6 -8 l6 8 l6 -8" stroke-width="2"/>')
    s.append('<path d="M458 70 L522 136" stroke="#b8232a" stroke-width="5"/>')
    s.append('<text x="489" y="160" text-anchor="middle" font-size="22" font-weight="800" fill="#7a6a64" stroke="none">60W</text>')
    s.append('<path d="M534 100 L580 100 M570 90 L582 100 L570 110" stroke="#2e7d32" stroke-width="4"/>')
    s.append('<path d="M602 120 Q588 104 598 86 Q612 72 626 86 Q636 104 620 120 Z" fill="#fffde7"/><rect x="600" y="120" width="20" height="12" fill="#b0bec5"/>')
    s.append('<text x="611" y="160" text-anchor="middle" font-size="22" font-weight="800" fill="#2e7d32" stroke="none">7W</text>')
    return "".join(s)


def scene_vaccine():
    """मिशन इंद्रधनुष: आंगनवाड़ी के बाहर टीकाकरण सत्र — मां की गोद में बच्चा, टीका लगाती ANM, ऊपर इंद्रधनुष।"""
    s = []
    # इंद्रधनुष (सात रंग)
    cols = ["#e53935", "#fb8c00", "#fdd835", "#43a047", "#1e88e5", "#3949ab", "#8e24aa"]
    for i, c in enumerate(cols):
        r = 300 - i * 14
        s.append(f'<path d="M{330-r} 330 A{r} {r} 0 0 1 {330+r} 330" stroke="{c}" stroke-width="12" fill="none" opacity=".85"/>')
    s.append('<path d="M30 330 q-20 -30 14 -40 q10 -26 40 -14 q30 -6 34 22 q20 14 0 32 Z" fill="#fff"/>')
    s.append('<path d="M570 330 q-14 -30 18 -38 q12 -24 40 -10 q28 0 26 26 q18 14 -2 26 Z" fill="#fff"/>')
    # ज़मीन
    s.append('<path d="M0 548 Q160 536 330 548 Q500 560 660 544 L660 580 L0 580 Z" fill="#dfe9cf"/>')
    s.append('<path d="M0 580 L660 580"/>')
    # आंगनवाड़ी भवन (पीछे बाएं)
    s.append('<rect x="20" y="372" width="200" height="176" fill="#fff3e0"/><path d="M8 376 L120 318 L232 376 Z" fill="#ffab91"/>')
    s.append('<rect x="92" y="440" width="56" height="108" fill="#a1887f"/><rect x="40" y="410" width="36" height="34" fill="#b3e5fc"/><rect x="166" y="410" width="36" height="34" fill="#b3e5fc"/>')
    s.append('<text x="120" y="398" text-anchor="middle" font-size="19" font-weight="800" fill="#b8232a" stroke="none">आंगनवाड़ी</text>')
    # मेज़, टीका-बक्सा (vaccine carrier) और रजिस्टर
    s.append('<rect x="236" y="470" width="150" height="14" fill="#a1887f"/><path d="M248 484 L248 560 M374 484 L374 560"/>')
    s.append('<rect x="250" y="424" width="56" height="46" rx="8" fill="#4fc3f7"/><path d="M262 424 q16 -18 32 0" fill="none"/>')
    s.append('<path d="M278 436 v22 M267 447 h22" stroke="#fff" stroke-width="5"/>')
    s.append('<rect x="318" y="448" width="54" height="22" rx="3" fill="#fff"/><path d="M345 448 L345 470" stroke-width="2"/>')
    # ANM (स्वास्थ्यकर्मी) — सिरिंज के साथ
    s.append(_person(450, 566, "#c68b59", "#e3f2fd", 0.96, saree=True))
    s.append('<path d="M470 412 Q500 420 520 432" fill="none"/>')
    s.append('<rect x="516" y="424" width="30" height="9" rx="2" fill="#fff" transform="rotate(20 516 424)"/>')
    s.append('<path d="M544 437 L556 442" stroke-width="2"/>')
    # मां (बैठी), गोद में बच्चा
    s.append('<rect x="548" y="500" width="92" height="16" fill="#bcaaa4"/><path d="M558 516 L558 566 M630 516 L630 566"/>')
    s.append('<circle cx="604" cy="378" r="22" fill="#d49a6a"/>')
    s.append('<path d="M578 404 Q604 392 630 404 L640 500 L566 500 Z" fill="#f06292"/>')
    s.append('<path d="M582 402 Q604 360 628 402" fill="none"/>')
    s.append('<path d="M566 500 L556 560 M640 500 L646 560" stroke-width="5"/>')
    s.append('<ellipse cx="574" cy="452" rx="34" ry="20" fill="#fff59d"/>')
    s.append('<circle cx="548" cy="446" r="15" fill="#e0a878"/>')
    s.append('<path d="M590 470 Q610 476 624 462" fill="none"/>')
    # टीकाकरण कार्ड का प्रतीक (ऊपर दाएं, ✓)
    s.append('<rect x="500" y="250" width="92" height="66" rx="8" fill="#fff"/><path d="M512 266 h50 M512 280 h40 M512 294 h46" stroke-width="2"/>')
    s.append('<circle cx="574" cy="296" r="14" fill="#66bb6a"/><path d="M567 296 l5 5 l9 -10" stroke="#fff" stroke-width="3"/>')
    return "".join(s)


def scene_svamitva():
    """स्वामित्व: गांव की आबादी के घर, ऊपर ड्रोन और सर्वे-ग्रिड, नीचे संपत्ति कार्ड थामे दंपती, पास में बैंक।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#eef5fb" stroke="none"/>')
    # ड्रोन (ऊपर बीच) और नीचे जाती स्कैन-किरणें
    s.append('<path d="M250 150 L180 330 L470 330 L400 150 Z" fill="#fff59d" stroke="none" opacity=".45"/>')
    s.append('<rect x="290" y="96" width="70" height="30" rx="10" fill="#90a4ae"/><circle cx="325" cy="132" r="9" fill="#37474f"/>')
    s.append('<path d="M290 104 L250 84 M360 104 L400 84 M290 118 L250 138 M360 118 L400 138"/>')
    for cx, cy in ((242, 82), (408, 82), (242, 140), (408, 140)):
        s.append(f'<ellipse cx="{cx}" cy="{cy}" rx="26" ry="6" fill="#cfd8dc"/>')
    # ज़मीन और सर्वे ग्रिड (लाल डैश वाली प्लॉट सीमाएं)
    s.append('<path d="M0 330 L660 330 L660 580 L0 580 Z" fill="#e6f1d8"/>')
    for x in (60, 190, 330, 470, 600):
        s.append(f'<path d="M{x} 330 L{x-20} 430" stroke="#b8232a" stroke-width="2.4" stroke-dasharray="8 7"/>')
    s.append('<path d="M30 380 L640 380 M10 430 L650 430" stroke="#b8232a" stroke-width="2.4" stroke-dasharray="8 7"/>')
    # गांव के घर (खपरैल छत)
    for x, col in ((70, "#ef9a9a"), (200, "#ffcc80"), (340, "#a5d6a7"), (480, "#ce93d8")):
        s.append(f'<rect x="{x}" y="276" width="96" height="70" fill="#fff8e1"/><path d="M{x-10} 280 L{x+48} 236 L{x+106} 280 Z" fill="{col}"/>'
                 f'<rect x="{x+36}" y="306" width="24" height="40" fill="#a1887f"/>')
    # पेड़
    s.append('<rect x="604" y="250" width="12" height="90" fill="#8d6e63"/><circle cx="610" cy="236" r="40" fill="#81c784"/>')
    # बैंक भवन (बाएं नीचे)
    s.append('<path d="M20 470 L100 430 L180 470 Z" fill="#90caf9"/><rect x="28" y="470" width="144" height="86" fill="#fff"/>')
    for x in (46, 82, 118, 154):
        s.append(f'<rect x="{x-6}" y="478" width="12" height="70" fill="#e3f2fd"/>')
    s.append('<text x="100" y="463" text-anchor="middle" font-size="22" font-weight="800" fill="#b8232a" stroke="none">₹ बैंक</text>')
    s.append('<path d="M10 556 L190 556" stroke-width="4"/>')
    # दंपती, महिला के हाथ में संपत्ति कार्ड
    s.append(_person(330, 572, "#c68b59", "#ffffff", 0.9))
    s.append(_person(450, 572, "#d49a6a", "#4db6ac", 0.92, saree=True))
    s.append('<rect x="472" y="408" width="124" height="96" rx="8" fill="#fff"/>')
    s.append('<text x="534" y="432" text-anchor="middle" font-size="17" font-weight="800" fill="#5c0f12" stroke="none">संपत्ति कार्ड</text>')
    s.append('<path d="M484 448 h60 M484 462 h48 M484 476 h56" stroke-width="2"/>')
    s.append('<rect x="558" y="446" width="26" height="26" fill="#ffe0b2" stroke-width="2"/><path d="M484 492 l18 -8 l14 8 l18 -10" stroke="#b8232a" stroke-width="2"/>')
    s.append('<path d="M478 434 Q468 426 470 412" fill="none"/>')
    s.append('<path d="M0 580 L660 580"/>')
    return "".join(s)


def scene_shg():
    """लखपति दीदी/DAY-NRLM: पेड़ के नीचे स्वयं सहायता समूह की बैठक (बचत रजिस्टर, गुल्लक), पास में दीदी की दुकान, ऊपर बढ़ती कमाई का तीर।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#fdf6ea" stroke="none"/>')
    # सूरज
    s.append('<circle cx="560" cy="80" r="34" fill="#ffd54f"/>')
    # बढ़ती कमाई का तीर और सिक्के (ऊपर बाएं से दाएं)
    s.append('<path d="M60 230 L170 190 L260 205 L380 120" fill="none" stroke="#2e7d32" stroke-width="6"/>')
    s.append('<path d="M356 116 L384 118 L374 144" fill="none" stroke="#2e7d32" stroke-width="6"/>')
    for i, (cx, h) in enumerate(((80, 2), (130, 3), (180, 4), (230, 5))):
        for j in range(h):
            s.append(f'<ellipse cx="{cx}" cy="{300-j*12}" rx="18" ry="6" fill="#ffca28"/>')
    s.append('<text x="150" y="150" text-anchor="middle" font-size="32" font-weight="800" fill="#2e7d32" stroke="none">₹1 लाख+</text>')
    # ज़मीन
    s.append('<path d="M0 470 Q160 452 330 466 Q500 480 660 460 L660 580 L0 580 Z" fill="#e6f1d8"/>')
    s.append('<path d="M0 580 L660 580"/>')
    # पेड़ (बीच-पीछे)
    s.append('<rect x="312" y="300" width="22" height="170" fill="#8d6e63"/>')
    s.append('<circle cx="292" cy="290" r="54" fill="#81c784"/><circle cx="356" cy="282" r="58" fill="#66bb6a"/><circle cx="324" cy="236" r="52" fill="#81c784"/>')
    # दरी, बचत रजिस्टर और गुल्लक
    s.append('<ellipse cx="250" cy="540" rx="190" ry="26" fill="#ffccbc"/>')
    s.append('<rect x="196" y="508" width="70" height="26" rx="3" fill="#fff"/><path d="M231 508 L231 534" stroke-width="2"/><path d="M204 516 h20 M238 516 h20 M204 524 h18 M238 524 h18" stroke-width="1.6"/>')
    s.append('<path d="M286 532 Q286 506 306 504 Q326 506 326 532 Z" fill="#ef9a9a"/><path d="M300 510 h12" stroke-width="3"/>')
    # समूह की दीदियां (साड़ी)
    s.append(_person(110, 560, "#c68b59", "#f06292", 0.78, saree=True))
    s.append(_person(170, 562, "#d49a6a", "#ffb74d", 0.74, saree=True))
    s.append(_person(380, 562, "#b97850", "#4db6ac", 0.76, saree=True))
    s.append(_person(440, 560, "#d49a6a", "#9575cd", 0.8, saree=True))
    # दीदी की दुकान (दाएं)
    s.append('<rect x="490" y="330" width="150" height="200" fill="#fff8e1"/>')
    s.append('<path d="M480 330 L650 330 L636 296 L494 296 Z" fill="#e57373"/>')
    for x in (500, 530, 560, 590, 620):
        s.append(f'<path d="M{x} 330 q15 18 30 0" fill="#fff"/>')
    s.append('<path d="M500 390 L630 390 M500 450 L630 450" stroke-width="3"/>')
    for x in (510, 540, 570, 600):
        s.append(f'<rect x="{x}" y="362" width="18" height="28" rx="4" fill="#ffcc80"/><rect x="{x+2}" y="356" width="14" height="8" fill="#a1887f"/>')
        s.append(f'<rect x="{x}" y="424" width="20" height="26" rx="2" fill="#90caf9"/>')
    s.append('<rect x="490" y="470" width="150" height="60" fill="#bcaaa4"/>')
    s.append('<text x="565" y="508" text-anchor="middle" font-size="20" font-weight="800" fill="#5c0f12" stroke="none">दीदी स्टोर</text>')
    # बैंक पासबुक (दुकान के ऊपर)
    s.append('<rect x="430" y="180" width="96" height="64" rx="6" fill="#bbdefb"/><path d="M478 180 L478 244" stroke-width="2"/>')
    s.append('<text x="454" y="220" text-anchor="middle" font-size="22" font-weight="800" fill="#b8232a" stroke="none">₹</text><path d="M486 200 h30 M486 212 h24 M486 224 h28" stroke-width="1.8"/>')
    return "".join(s)


def scene_matru():
    """मातृ वंदना: आंगनवाड़ी के बाहर गोद में बच्चा लिए मां, MCP कार्ड, पोषण की थाली और खाते में आती राशि।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#fdf3f4" stroke="none"/>')
    # ज़मीन
    s.append('<path d="M0 520 Q170 506 330 518 Q500 530 660 512 L660 580 L0 580 Z" fill="#e6f1d8"/><path d="M0 580 L660 580"/>')
    # आंगनवाड़ी भवन (बाएं)
    s.append('<rect x="24" y="300" width="230" height="220" fill="#fff3e0"/><path d="M10 304 L139 236 L268 304 Z" fill="#f48fb1"/>')
    s.append('<rect x="110" y="400" width="58" height="120" fill="#a1887f"/><rect x="44" y="350" width="44" height="40" fill="#b3e5fc"/><rect x="190" y="350" width="44" height="40" fill="#b3e5fc"/>')
    s.append('<text x="139" y="330" text-anchor="middle" font-size="21" font-weight="800" fill="#b8232a" stroke="none">आंगनवाड़ी</text>')
    # आंगनवाड़ी कार्यकर्ता, हाथ में रजिस्टर
    s.append(_person(300, 540, "#c68b59", "#ffcc80", 0.86, saree=True))
    s.append('<rect x="318" y="398" width="44" height="54" rx="4" fill="#fff"/><path d="M326 412 h28 M326 424 h22 M326 436 h26" stroke-width="2"/>')
    # मां (साड़ी) और गोद में बच्चा
    s.append(_person(470, 546, "#d49a6a", "#ba68c8", 1.0, saree=True))
    s.append('<ellipse cx="440" cy="420" rx="40" ry="22" fill="#fff59d"/><circle cx="410" cy="410" r="17" fill="#e0a878"/>')
    s.append('<path d="M456 440 Q478 444 496 430" fill="none"/>')
    # पोषण की थाली (नीचे बीच)
    s.append('<ellipse cx="380" cy="556" rx="58" ry="14" fill="#cfd8dc"/>')
    for cx, col in ((354, "#ffb74d"), (380, "#81c784"), (406, "#ef5350")):
        s.append(f'<circle cx="{cx}" cy="550" r="11" fill="{col}"/>')
    # MCP कार्ड (ऊपर बीच) ✓ के साथ
    s.append('<rect x="290" y="170" width="120" height="84" rx="8" fill="#fff"/>')
    s.append('<text x="350" y="196" text-anchor="middle" font-size="17" font-weight="800" fill="#5c0f12" stroke="none">MCP कार्ड</text>')
    s.append('<path d="M302 214 h60 M302 230 h46" stroke-width="2"/><circle cx="388" cy="230" r="13" fill="#66bb6a"/><path d="M381 230 l5 5 l9 -10" stroke="#fff" stroke-width="3"/>')
    # खाते में राशि: पासबुक और सिक्कों का रास्ता (ऊपर दाएं)
    s.append('<rect x="520" y="140" width="110" height="74" rx="7" fill="#bbdefb"/><path d="M575 140 L575 214" stroke-width="2"/>')
    s.append('<text x="548" y="186" text-anchor="middle" font-size="26" font-weight="800" fill="#b8232a" stroke="none">₹</text><path d="M584 160 h36 M584 174 h28 M584 188 h32" stroke-width="1.8"/>')
    s.append('<path d="M420 200 Q470 120 516 168" fill="none" stroke="#b8232a" stroke-width="3" stroke-dasharray="9 8"/>')
    s.append('<circle cx="458" cy="148" r="18" fill="#ffca28"/><text x="458" y="156" text-anchor="middle" font-size="20" font-weight="800" fill="#3a1a12" stroke="none">₹</text>')
    # दिल का प्रतीक (मां-बच्चे की देखभाल)
    s.append('<path d="M140 120 C140 96 172 92 176 116 C180 92 212 96 212 120 C212 146 176 166 176 172 C176 166 140 146 140 120 Z" fill="#ef9a9a"/>')
    return "".join(s)


def scene_road():
    """ग्राम सड़क: पहाड़ियों के बीच गांव से निकलती बारहमासी पक्की सड़क, बस, ट्रैक्टर, और दूर अस्पताल-स्कूल-मंडी।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#eaf4fb" stroke="none"/>')
    s.append('<circle cx="580" cy="80" r="34" fill="#ffd54f"/>')
    s.append('<path d="M0 260 Q120 180 240 240 Q360 170 480 230 Q570 190 660 220 L660 330 L0 330 Z" fill="#c5e1a5"/>')
    s.append('<path d="M0 330 L660 330 L660 580 L0 580 Z" fill="#dcedc8"/>')
    # दूर के भवन: अस्पताल, स्कूल, मंडी
    s.append('<rect x="420" y="250" width="70" height="60" fill="#fff"/><path d="M448 262 v24 M436 274 h24" stroke="#e53935" stroke-width="5"/>')
    s.append('<rect x="500" y="262" width="66" height="48" fill="#fff8e1"/><path d="M494 264 L533 238 L572 264 Z" fill="#ffcc80"/><text x="533" y="294" text-anchor="middle" font-size="15" font-weight="800" fill="#5c0f12" stroke="none">स्कूल</text>')
    s.append('<rect x="580" y="270" width="64" height="40" fill="#ffe0b2"/><path d="M576 272 L612 252 L648 272 Z" fill="#a5d6a7"/><text x="612" y="298" text-anchor="middle" font-size="15" font-weight="800" fill="#5c0f12" stroke="none">मंडी</text>')
    # घुमावदार सड़क (आगे चौड़ी, दूर पतली)
    s.append('<path d="M120 580 Q260 470 330 420 Q420 360 470 316 L500 316 Q450 370 380 430 Q300 500 300 580 Z" fill="#78909c"/>')
    s.append('<path d="M210 580 Q290 480 360 425 Q430 368 485 316" fill="none" stroke="#fff" stroke-width="4" stroke-dasharray="18 14"/>')
    # गांव के घर (बाएं)
    for x, col in ((30, "#ef9a9a"), (130, "#ffcc80")):
        s.append(f'<rect x="{x}" y="380" width="84" height="64" fill="#fff8e1"/><path d="M{x-8} 384 L{x+42} 344 L{x+92} 384 Z" fill="{col}"/><rect x="{x+30}" y="408" width="22" height="36" fill="#a1887f"/>')
    s.append('<rect x="250" y="300" width="12" height="70" fill="#8d6e63"/><circle cx="256" cy="290" r="32" fill="#81c784"/>')
    # बस (सड़क पर)
    s.append('<rect x="300" y="430" width="110" height="52" rx="8" fill="#ffca28"/>')
    for x in (310, 336, 362, 386):
        s.append(f'<rect x="{x}" y="440" width="18" height="16" fill="#e3f2fd"/>')
    s.append('<circle cx="324" cy="484" r="10" fill="#37474f"/><circle cx="390" cy="484" r="10" fill="#37474f"/>')
    # ट्रैक्टर-ट्रॉली में अनाज (आगे बाएं)
    s.append('<rect x="150" y="500" width="70" height="40" rx="4" fill="#e57373"/><circle cx="168" cy="546" r="16" fill="#37474f"/><circle cx="208" cy="550" r="10" fill="#37474f"/>')
    s.append('<rect x="70" y="510" width="72" height="30" fill="#a1887f"/><path d="M74 510 Q106 486 138 510 Z" fill="#ffd54f"/><circle cx="104" cy="546" r="9" fill="#37474f"/>')
    # स्कूल जाती बच्ची (दाएं आगे)
    s.append(_person(520, 560, "#d49a6a", "#4fc3f7", 0.62))
    s.append('<rect x="534" y="450" width="20" height="26" rx="3" fill="#ef5350"/>')
    s.append('<path d="M0 580 L660 580"/>')
    return "".join(s)


def scene_bharatnet():
    """भारतनेट: खंभों पर दौड़ती फ़ाइबर लाइन, Wi-Fi वाला पंचायत भवन, टैबलेट पर पढ़ती बच्ची और फ़ोन पर किसान।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#eaf4fb" stroke="none"/>')
    s.append('<circle cx="84" cy="86" r="34" fill="#ffd54f"/>')
    s.append('<path d="M0 300 Q140 230 280 280 Q420 220 560 270 Q610 255 660 262 L660 360 L0 360 Z" fill="#c5e1a5"/>')
    s.append('<path d="M0 360 L660 360 L660 580 L0 580 Z" fill="#dcedc8"/>')
    # खेत की क्यारियाँ
    for y in (390, 420, 450):
        s.append(f'<path d="M20 {y} Q120 {y-8} 220 {y}" fill="none" stroke="#7cb342" stroke-width="2.4"/>')
    # खंभे और फ़ाइबर केबल (नारंगी)
    poles = [(40, 250), (190, 232), (340, 220), (490, 214)]
    for x, top in poles:
        s.append(f'<path d="M{x} {top} L{x} 360" stroke-width="4"/><path d="M{x-14} {top+8} L{x+14} {top+8}"/>')
    pts = " ".join(f"Q{(poles[i][0]+poles[i+1][0])/2:.0f} {max(poles[i][1], poles[i+1][1])+34} {poles[i+1][0]} {poles[i+1][1]+8}" for i in range(len(poles)-1))
    s.append(f'<path d="M{poles[0][0]} {poles[0][1]+8} {pts} Q540 250 560 262" fill="none" stroke="#ef6c00" stroke-width="4"/>')
    # ग्राम पंचायत भवन + Wi-Fi
    s.append('<rect x="400" y="262" width="230" height="140" fill="#fff8e1"/><path d="M388 266 L515 210 L642 266 Z" fill="#ef9a9a"/>')
    s.append('<text x="515" y="296" text-anchor="middle" font-size="20" font-weight="800" fill="#5c0f12" stroke="none">ग्राम पंचायत</text>')
    s.append('<rect x="490" y="340" width="50" height="62" fill="#a1887f"/><rect x="420" y="320" width="44" height="36" fill="#e3f2fd"/><rect x="566" y="320" width="44" height="36" fill="#e3f2fd"/>')
    s.append('<rect x="560" y="234" width="40" height="20" rx="4" fill="#fff"/><circle cx="590" cy="244" r="3.5" fill="#43a047"/><path d="M570 234 l-6 -16 M590 234 l6 -16"/>')
    for r in (14, 26, 38):
        s.append(f'<path d="M{580-r} {206-r*0.2:.0f} a{r} {r} 0 0 1 {2*r} 0" fill="none" stroke="#1e88e5" stroke-width="3.2"/>')
    s.append('<circle cx="580" cy="208" r="4.5" fill="#1e88e5" stroke="none"/>')
    # बरगद का पेड़
    s.append('<rect x="290" y="300" width="14" height="70" fill="#8d6e63"/><circle cx="297" cy="292" r="36" fill="#81c784"/>')
    # टैबलेट पर पढ़ती बच्ची
    s.append(_person(150, 572, "#d49a6a", "#4fc3f7", 0.78))
    s.append('<rect x="176" y="430" width="58" height="42" rx="6" fill="#fff"/><rect x="182" y="436" width="46" height="30" rx="3" fill="#bbdefb"/>')
    s.append('<path d="M190 446 h30 M190 456 h20" stroke-width="2"/><path d="M168 454 Q172 446 178 446" fill="none"/>')
    # फ़ोन पर वीडियो कॉल करता किसान, साफ़ा
    s.append(_person(420, 572, "#b97850", "#ffffff", 0.95))
    s.append('<path d="M396 378 Q420 360 444 378 L444 386 L396 386 Z" fill="#ffb74d"/>')
    s.append('<path d="M446 452 Q470 430 466 400" fill="none"/>')
    s.append('<rect x="452" y="352" width="40" height="66" rx="7" fill="#e3f2fd"/><rect x="458" y="360" width="28" height="44" rx="3" fill="#c8e6c9"/>')
    s.append('<circle cx="472" cy="376" r="7" fill="#ffccbc"/><path d="M462 398 q10 -12 20 0" fill="#90caf9"/>')
    s.append('<path d="M0 580 L660 580"/>')
    return "".join(s)


def scene_sarovar():
    """अमृत सरोवर: सीढ़ीदार घाट वाला भरा तालाब, किनारे तिरंगा, नीम-पीपल, पानी पीते मवेशी, नाव से जाल डालती महिला और सरोवर का बोर्ड।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#eaf4fb" stroke="none"/>')
    s.append('<circle cx="560" cy="80" r="34" fill="#ffd54f"/>')
    s.append('<path d="M0 220 Q140 160 280 200 Q420 150 560 196 Q610 186 660 190 L660 300 L0 300 Z" fill="#c5e1a5"/>')
    s.append('<path d="M0 260 L660 260 L660 580 L0 580 Z" fill="#dcedc8"/>')
    # तालाब (अंडाकार) और लहरें
    s.append('<ellipse cx="350" cy="430" rx="280" ry="110" fill="#81d4fa"/>')
    s.append('<ellipse cx="350" cy="430" rx="240" ry="86" fill="#4fc3f7" stroke="none"/>')
    for x, y in ((230, 410), (330, 450), (440, 420), (290, 480), (480, 470)):
        s.append(f'<path d="M{x} {y} q12 -8 24 0 q12 8 24 0" stroke="#e1f5fe" stroke-width="2.4"/>')
    # सीढ़ीदार घाट (बाएं)
    s.append('<path d="M60 350 L110 412 L190 400 L170 350 Z" fill="#ffe0b2" stroke-width="2.6"/>')
    for i in range(1, 4):
        s.append(f'<path d="M{60+i*12.5:.0f} {350+i*15.5:.0f} L{170+i*6.7:.0f} {350+i*12.5:.0f}" stroke-width="2.4"/>')
    # तिरंगा
    s.append('<path d="M110 340 L110 220" stroke-width="4"/>')
    s.append('<rect x="112" y="222" width="64" height="14" fill="#ff9933"/><rect x="112" y="236" width="64" height="14" fill="#fff"/><rect x="112" y="250" width="64" height="14" fill="#138808"/>')
    s.append('<circle cx="144" cy="243" r="4.5" fill="none" stroke="#1a237e" stroke-width="1.8"/>')
    # सरोवर का बोर्ड
    s.append('<rect x="210" y="262" width="150" height="54" rx="6" fill="#fff8e1"/><path d="M240 316 L240 342 M330 316 L330 342" stroke-width="3.4"/>')
    s.append('<text x="285" y="296" text-anchor="middle" font-size="22" font-weight="800" fill="#5c0f12" stroke="none">अमृत सरोवर</text>')
    # नीम / पीपल
    s.append('<rect x="560" y="250" width="14" height="80" fill="#8d6e63"/><circle cx="567" cy="236" r="42" fill="#81c784"/>')
    s.append('<rect x="420" y="232" width="12" height="66" fill="#8d6e63"/><circle cx="426" cy="222" r="30" fill="#a5d6a7"/>')
    # पानी पीती गाय (दाएं किनारे)
    s.append('<g transform="translate(-50,-80)"><path d="M528 388 L526 410 M548 392 L548 412 M574 392 L574 412 M594 386 L596 408"/><ellipse cx="560" cy="372" rx="44" ry="22" fill="#fff"/>')
    s.append('<path d="M516 370 Q496 376 492 392 Q500 398 508 392 Q514 382 522 380" fill="#fff"/><path d="M512 364 l-6 -10 M522 364 l2 -10"/></g>')
    # नाव पर जाल डालती महिला
    s.append('<path d="M300 440 Q350 470 410 440 Z" fill="#a1887f"/>')
    s.append(_person(356, 446, "#c68a5e", "#ef5350", 0.36, saree=True))
    s.append('<path d="M366 400 Q410 384 430 420 Q404 432 378 424" fill="none" stroke-dasharray="4 4" stroke-width="2"/>')
    # कमल
    for x, y in ((470, 400), (230, 460)):
        s.append(f'<path d="M{x} {y} q-8 -14 0 -22 q8 8 0 22 q-14 -4 -16 -14 q12 0 16 14 q4 -12 16 -14 q-2 10 -16 14" fill="#f8bbd0" stroke-width="2"/>')
    s.append('<path d="M0 580 L660 580"/>')
    return "".join(s)


def scene_ganga():
    """नमामि गंगे: मंदिर वाला सीढ़ीदार घाट, बहती गंगा, उछलती डॉल्फ़िन, नाव, किनारे सीवेज शोधन संयंत्र (STP) के गोल टैंक और घाट पर गंगा प्रहरी।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#eaf4fb" stroke="none"/>')
    s.append('<circle cx="320" cy="84" r="34" fill="#ffd54f"/>')
    for x, y in ((420, 70), (470, 92)):
        s.append(f'<path d="M{x} {y} q10 -10 20 0 q10 -10 20 0" fill="none" stroke-width="2.4"/>')
    s.append('<path d="M0 250 Q160 200 330 236 Q500 206 660 230 L660 320 L0 320 Z" fill="#c5e1a5"/>')
    # नदी
    s.append('<path d="M0 330 Q330 300 660 330 L660 580 L0 580 Z" fill="#81d4fa"/>')
    s.append('<path d="M0 380 Q330 350 660 380 L660 580 L0 580 Z" fill="#4fc3f7" stroke="none"/>')
    for x, y in ((250, 420), (380, 470), (520, 430), (150, 500), (470, 530)):
        s.append(f'<path d="M{x} {y} q12 -8 24 0 q12 8 24 0" stroke="#e1f5fe" stroke-width="2.4"/>')
    # बाएं: मंदिर और सीढ़ीदार घाट
    s.append('<rect x="40" y="200" width="90" height="110" fill="#ffe0b2"/>')
    s.append('<path d="M30 204 L85 120 L140 204 Z" fill="#ef9a9a"/><path d="M85 120 L85 96"/><path d="M85 96 l22 8 l-22 8 Z" fill="#ff9933"/>')
    s.append('<path d="M70 310 L70 262 Q85 244 100 262 L100 310" fill="#a1887f"/>')
    s.append('<path d="M0 310 L210 310 L250 400 L0 400 Z" fill="#ffe0b2" stroke-width="2.6"/>')
    for i in range(1, 5):
        s.append(f'<path d="M0 {310+i*18} L{210+i*8} {310+i*18}" stroke-width="2.2"/>')
    # घाट पर दीया और गंगा प्रहरी (हरी जैकेट)
    s.append('<path d="M180 318 q12 10 24 0 Z" fill="#ff9800"/><path d="M192 316 q-5 -10 0 -16 q5 6 0 16" fill="#ffd54f" stroke-width="2"/>')
    s.append(_person(120, 392, "#c68a5e", "#43a047", 0.5))
    s.append('<path d="M134 330 L150 300" stroke-width="3"/><rect x="146" y="286" width="30" height="20" rx="3" fill="#fff"/>')
    # दाएं किनारे: STP के गोल टैंक और भवन
    s.append('<rect x="520" y="210" width="110" height="70" fill="#fff8e1"/><path d="M512 214 L575 182 L638 214 Z" fill="#b0bec5"/>')
    s.append('<text x="575" y="254" text-anchor="middle" font-size="22" font-weight="800" fill="#5c0f12" stroke="none">STP</text>')
    s.append('<ellipse cx="430" cy="262" rx="52" ry="16" fill="#b3e5fc"/><path d="M378 262 L378 284 Q430 300 482 284 L482 262" fill="#cfd8dc"/>')
    s.append('<ellipse cx="430" cy="262" rx="52" ry="16" fill="#80deea"/>')
    s.append('<path d="M482 280 L520 270 M560 280 L560 312 Q560 326 574 330" stroke="#546e7a" stroke-width="5"/>')
    s.append('<path d="M574 332 q6 10 0 20 M586 332 q6 10 0 20" stroke="#29b6f6" stroke-width="3"/>')
    # नाव और नाविक
    s.append('<path d="M300 452 Q370 486 450 452 Z" fill="#a1887f"/>')
    s.append(_person(380, 458, "#b97850", "#ffffff", 0.34))
    s.append('<path d="M396 400 L430 486" stroke-width="3.4"/>')
    # उछलती डॉल्फ़िन
    s.append('<path d="M500 500 Q530 440 590 470 Q570 462 556 470 Q548 484 540 486 Q528 486 518 506 Z" fill="#90a4ae"/>')
    s.append('<path d="M548 468 l-6 -12 l14 6" fill="#90a4ae"/><circle cx="578" cy="468" r="2.4" fill="' + INK + '" stroke="none"/>')
    s.append('<path d="M500 512 q10 -8 20 0 q10 8 20 0" stroke="#e1f5fe" stroke-width="2.4"/>')
    # पेड़
    s.append('<rect x="250" y="236" width="12" height="64" fill="#8d6e63"/><circle cx="256" cy="226" r="32" fill="#81c784"/>')
    s.append('<rect x="320" y="250" width="10" height="50" fill="#8d6e63"/><circle cx="325" cy="242" r="24" fill="#a5d6a7"/>')
    s.append('<path d="M0 580 L660 580"/>')
    return "".join(s)


def scene_ration():
    """गरीब कल्याण अन्न योजना: उचित मूल्य की दुकान, अनाज की बोरियां, ePoS मशीन पर अंगूठा लगाती महिला, थैला लिए बुज़ुर्ग, गेहूं की बालियां।"""
    s = []
    s.append('<rect x="0" y="0" width="660" height="580" fill="#fdf3e1" stroke="none"/>')
    s.append('<circle cx="90" cy="80" r="34" fill="#ffd54f"/>')
    s.append('<path d="M0 470 Q160 430 330 456 Q500 428 660 452 L660 580 L0 580 Z" fill="#e6f1d8"/>')
    # दुकान का भवन
    s.append('<rect x="150" y="170" width="380" height="300" fill="#fff8e1"/>')
    s.append('<path d="M130 176 L340 104 L550 176 Z" fill="#ffccbc"/>')
    s.append('<rect x="190" y="132" width="300" height="0" />')
    s.append('<rect x="200" y="186" width="280" height="46" rx="6" fill="#b8232a"/>')
    s.append('<text x="340" y="219" text-anchor="middle" font-size="26" font-weight="800" fill="#fff" stroke="none">उचित मूल्य दुकान</text>')
    # धारीदार छज्जा
    for i in range(7):
        col = "#ff9933" if i % 2 == 0 else "#ffffff"
        s.append(f'<path d="M{150+i*54.3:.0f} 240 L{204+i*54.3:.0f} 240 L{204+i*54.3:.0f} 262 Q{177+i*54.3:.0f} 276 {150+i*54.3:.0f} 262 Z" fill="{col}"/>')
    # काउंटर और बोरियां
    s.append('<rect x="170" y="380" width="340" height="24" fill="#a1887f"/>')
    for x, lab in ((210, "गेहूं"), (300, "चावल"), (390, "गेहूं")):
        s.append(f'<path d="M{x-34} 380 Q{x-40} 310 {x-22} 296 L{x+22} 296 Q{x+40} 310 {x+34} 380 Z" fill="#f5deb3"/>')
        s.append(f'<path d="M{x-22} 296 q22 -14 44 0" fill="none"/>')
        s.append(f'<text x="{x}" y="350" text-anchor="middle" font-size="18" font-weight="800" fill="#5c0f12" stroke="none">{lab}</text>')
    # तराज़ू
    s.append('<path d="M470 300 L470 380 M440 310 L500 310" stroke-width="3"/><path d="M432 310 l-10 26 h28 Z M508 310 l-10 26 h28 Z" fill="#ffe082"/>')
    # ePoS मशीन और महिला
    s.append('<rect x="80" y="388" width="52" height="34" rx="6" fill="#cfd8dc"/><circle cx="118" cy="405" r="6" fill="#66bb6a"/>')
    s.append(_person(70, 580, "#c68a5e", "#ef5350", 0.78, saree=True))
    s.append('<path d="M96 450 Q108 430 110 414" fill="none"/>')
    # थैला लिए बुज़ुर्ग
    s.append(_person(590, 580, "#b97850", "#ffffff", 0.86))
    s.append('<path d="M560 470 L548 520" /><path d="M520 516 L576 516 L570 566 L526 566 Z" fill="#c5e1a5"/>')
    s.append('<path d="M534 516 q14 -24 28 0" fill="none"/>')
    # गेहूं की बालियां
    for x in (20, 36, 628, 644):
        s.append(f'<path d="M{x} 580 L{x} 500" stroke="#8d6e63"/>')
        for k in range(4):
            s.append(f'<ellipse cx="{x-5}" cy="{506+k*12}" rx="4" ry="7" fill="#ffca28" stroke-width="1.6"/><ellipse cx="{x+5}" cy="{510+k*12}" rx="4" ry="7" fill="#ffca28" stroke-width="1.6"/>')
    s.append('<path d="M0 580 L660 580"/>')
    return "".join(s)


SCENES = {"dbt": scene_dbt, "ujala": scene_ujala, "vaccine": scene_vaccine, "svamitva": scene_svamitva, "shg": scene_shg,
          "matru": scene_matru, "road": scene_road, "bharatnet": scene_bharatnet, "sarovar": scene_sarovar, "ganga": scene_ganga,
          "ration": scene_ration}


def featured_lineart(f, part):
    scene = SCENES.get(f.get("scene", ""), scene_dbt)()
    stats = "".join(
        f'<div style="border:2px solid {INK};border-left:7px solid #b8232a;border-radius:8px;background:#fff;padding:6px 16px;margin-top:10px">'
        f'<div style="font-weight:800;font-size:30px;line-height:1.15;color:#8f1a1f">{e(a)}</div>'
        f'<div style="font-size:18px">{e(b)}</div></div>'
        for a, b in f["stats"][:3])
    return f"""<body style="background:#fbf7f2;color:{INK}">
<svg width="1200" height="675" style="position:absolute;left:0;top:0" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" font-family="N">{scene}</svg>
<img src="{LOGO}" style="position:absolute;right:36px;top:24px;height:88px">
<div style="position:absolute;left:690px;top:40px;background:#b8232a;color:#fff;font-weight:800;font-size:20px;padding:4px 14px;border-radius:5px">बदलता भारत · भाग {part}</div>
<div style="position:absolute;left:690px;right:40px;top:128px">
<div style="font-weight:800;font-size:{64 if len(f['title']) <= 14 else 50}px;line-height:1.08;color:#5c0f12">{e(f['title'])}</div>
<div style="font-weight:700;font-size:28px;line-height:1.25;margin-top:10px;color:#8f1a1f">{e(f['subtitle'])}</div>
<div style="margin-top:8px">{stats}</div></div>
<div style="position:absolute;left:0;right:0;bottom:0;height:6px;background:linear-gradient(90deg,#ff9933 0 33%,#fff 33% 66%,#138808 66%)"></div>
<div style="position:absolute;right:40px;bottom:18px;font-weight:800;font-size:19px;color:#8f1a1f">desilalkaar.com</div>
<div style="position:absolute;left:24px;bottom:18px;font-size:14px;color:#7a6a64">{e(f['source'])}</div></body>"""


def timeline(t):
    items = t["items"]
    n, x0, x1, ly = len(items), 160, 1040, 350
    d = ""
    for i, (dt, tx) in enumerate(items):
        x = x0 + (x1 - x0) * i / max(n - 1, 1)
        up = i % 2 == 0
        d += f'<div style="position:absolute;left:{x-9}px;top:{ly-7}px;width:18px;height:18px;border-radius:50%;background:#b8232a;border:4px solid #fbf7f2;box-shadow:0 0 0 2px #b8232a"></div>'
        d += f'<div style="position:absolute;left:{x}px;top:{ly-40 if up else ly+15}px;width:2px;height:28px;background:#c9b8b0"></div>'
        d += (f'<div style="position:absolute;left:{x-95}px;top:{ly-140 if up else ly+50}px;width:190px;text-align:center">'
              f'<div style="font-weight:800;font-size:22px;color:#8f1a1f">{e(dt)}</div><div style="font-size:18px;line-height:1.3;margin-top:4px">{e(tx)}</div></div>')
    return f"""<body class="light">{head("समयरेखा", t['title'])}
<div style="position:absolute;left:{x0}px;top:{ly}px;width:{x1-x0}px;height:4px;background:#e2cfc7"></div>{d}{strip(t['source'])}</body>"""


def chart(c):
    unit = c.get("unit", "")
    if "groups" in c:
        groups = c["groups"]
        cols = ["#c9b8b0", "#b8232a"]
        legend = c.get("legend", ["", ""])
    else:
        groups = [[lab, v] for lab, v in c["values"]]
        cols = ["#b8232a"]
        legend = []
    k = len(groups[0]) - 1
    vmax = max(max(g[1:]) for g in groups) or 1
    H, base = 300, 540
    gw = 940 / len(groups)
    bw = min(100, gw * 0.7 / k)
    b = ""
    for i, g in enumerate(groups):
        gx = 150 + gw * i + (gw - bw * k - 16 * (k - 1)) / 2
        for j, v in enumerate(g[1:]):
            h = v / vmax * H
            x = gx + j * (bw + 16)
            col = cols[j] if k > 1 else cols[0]
            lab = f"{v:,}".replace(",", ",") + unit
            b += (f'<div style="position:absolute;left:{x}px;top:{base-h}px;width:{bw}px;height:{h}px;background:{col};border-radius:5px 5px 0 0"></div>'
                  f'<div style="position:absolute;left:{x-20}px;top:{base-h-38}px;width:{bw+40}px;text-align:center;font-weight:800;font-size:24px;color:{"#7a6a64" if (k > 1 and j == 0) else "#8f1a1f"}">{e(lab)}</div>')
        b += f'<div style="position:absolute;left:{150+gw*i}px;top:{base+8}px;width:{gw}px;text-align:center;font-weight:700;font-size:21px">{e(g[0])}</div>'
    leg = ""
    if legend:
        leg = ('<div style="position:absolute;left:58px;top:158px;display:flex;gap:10px;font-size:19px;align-items:center">'
               + "".join(f'<span style="width:16px;height:16px;background:{cols[i]};border-radius:3px;display:inline-block;margin-left:{16 if i else 0}px"></span>{e(l)}' for i, l in enumerate(legend))
               + "</div>")
    return f"""<body class="light">{head("आंकड़े", c['title'], c.get('subtitle', ''))}{leg}
<div style="position:absolute;left:150px;top:{base}px;width:940px;height:2px;background:#8a7a74"></div>{b}{strip(c['source'])}</body>"""


def tiles(t, kicker):
    s = ""
    for i, tile in enumerate(t["tiles"][:4]):
        n, tx = tile[0], tile[1]
        src = tile[2] if len(tile) > 2 else ""
        x, y = 56 + (i % 2) * 554, 150 + (i // 2) * 200
        s += (f'<div class="tile" style="left:{x}px;top:{y}px"><div style="font-weight:800;font-size:50px;line-height:1.1;color:#8f1a1f">{e(n)}</div>'
              f'<div style="font-size:21px;line-height:1.3;margin-top:10px">{e(tx)}</div>'
              + (f'<div style="font-size:15px;color:#7a6a64;margin-top:6px">{e(src)}</div>' if src else "") + "</div>")
    return f'<body class="light">{head(kicker, t["title"])}{s}{strip(t["source"])}</body>'


def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    pages = {}
    if "featured" in spec:
        f = spec["featured"]
        # line-art default (prompts/line-art-featured-image-style.md); पुराना gradient सिर्फ़ "style": "gradient" पर
        pages["featured"] = (featured(f, spec.get("part", "")) if f.get("style") == "gradient"
                             else featured_lineart(f, spec.get("part", "")))
    if "timeline" in spec:
        pages["timeline"] = timeline(spec["timeline"])
    if "chart" in spec:
        pages["chart"] = chart(spec["chart"])
    if "asar" in spec:
        pages["asar"] = tiles(spec["asar"], "असर")
    if "mp" in spec:
        pages["madhya-pradesh"] = tiles(spec["mp"], "मध्य प्रदेश")
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        exe = os.environ.get("CHROME_PATH")
        br = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = br.new_page(viewport={"width": 1200, "height": 675})
        for name, body in pages.items():
            pg.goto("file://" + os.path.join(ROOT, "tools", "brand", "blank.html"))  # file:// page ताकि logo/font लोड हों
            pg.set_content(f"<html><head><meta charset=utf-8><style>{CSS}</style></head>{body}</html>")
            pg.wait_for_timeout(500)
            path = os.path.join(OUT, f"{spec['prefix']}-{name}.png")
            pg.screenshot(path=path)
            print("images/" + os.path.basename(path))
        br.close()


if __name__ == "__main__":
    main(sys.argv[1])

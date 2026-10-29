#!/usr/bin/env python3
"""नई रिपोर्टों के लिए charts और रंगीन line-art cover बनाता है।"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_charts as mc
from playwright.sync_api import sync_playwright

ROOT = mc.ROOT
W, H = 1280, 720


REPORTS = os.path.join(ROOT, "reports")


def img_exists(rel):
    # JSON में image path reports/ के सापेक्ष होता है (images/<file>.png)
    return bool(rel) and os.path.isfile(os.path.join(REPORTS, rel))


def charts_missing(r):
    for c in r.get("charts") or []:
        if not img_exists(c.get("file") or ""):
            return True
    return False


def cover_html(r):
    title = re.sub(r"^विश्लेषण:\s*", "", r.get("title", "")).strip()
    title = title if len(title) <= 72 else title[:69].rstrip() + "…"
    category = r.get("category") or "समाज"
    font = os.path.join(ROOT, "tools", "fonts", "NotoSansDevanagari.ttf")
    svg = f'''<svg width="1280" height="720" viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
<rect width="1280" height="720" fill="#fffdf7"/>
<path d="M0 520Q180 470 350 520T700 510T1050 515T1280 500V720H0Z" fill="#e9f3df"/>
<path d="M0 540Q180 490 350 540T700 530T1050 535T1280 520" fill="none" stroke="#263238" stroke-width="6"/>
<circle cx="1090" cy="105" r="58" fill="#ffd54f" stroke="#263238" stroke-width="6"/>
<g stroke="#263238" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
<path d="M80 515V285H270V515Z" fill="#f7cfa8"/><path d="M60 285L175 195L290 285Z" fill="#e57373"/>
<path d="M360 515V315H550V515Z" fill="#d7e9f7"/><path d="M335 315L455 225L575 315Z" fill="#81c784"/>
<path d="M780 515V320H1035V515Z" fill="#ffe0b2"/><path d="M750 320L905 220L1065 320Z" fill="#90caf9"/>
<path d="M1110 520V365"/><path d="M1110 405C1060 360 1055 325 1085 305C1120 335 1145 365 1110 405Z" fill="#66bb6a"/><path d="M1110 450C1160 410 1180 375 1150 350C1115 380 1095 415 1110 450Z" fill="#43a047"/>
<circle cx="615" cy="365" r="34" fill="#d49a6a"/><path d="M575 410Q615 385 655 410L675 535H555Z" fill="#f5f5f5"/><path d="M575 425L525 485M650 425L700 475M585 535L570 620M645 535L660 620" fill="none"/>
<circle cx="735" cy="385" r="32" fill="#b97850"/><path d="M700 425Q735 405 770 425L790 535H680Z" fill="#fff"/><path d="M705 440L660 490M770 440L815 485M710 535L695 620M760 535L775 620" fill="none"/>
<circle cx="450" cy="475" r="27" fill="#8d5a3b"/><path d="M420 510Q450 495 480 510L495 600H405Z" fill="#64b5f6"/><circle cx="520" cy="485" r="22" fill="#d49a6a"/><path d="M495 515Q520 502 545 515L555 585H485Z" fill="#ffb74d"/>
<path d="M820 535H1050L1025 650H845Z" fill="#fff"/><rect x="870" y="505" width="55" height="65" rx="8" fill="#ef5350"/><rect x="940" y="505" width="55" height="65" rx="8" fill="#42a5f5"/>
<path d="M575 500H665V530H575Z" fill="#42a5f5"/><path d="M590 470H680V500H590Z" fill="#ffca28"/>
<path d="M285 600Q320 555 350 600Q320 625 285 600Z" fill="#66bb6a"/><path d="M350 600Q385 550 415 600Q385 625 350 600Z" fill="#43a047"/>
</g>
<g font-family="Noto,sans-serif" fill="#263238">
<rect x="42" y="38" width="180" height="52" rx="8" fill="#fff" stroke="#b71c1c" stroke-width="4"/><text x="132" y="74" text-anchor="middle" font-size="27" font-weight="700" fill="#b71c1c">{html.escape(category)}</text>
<rect x="38" y="112" width="1204" height="142" rx="16" fill="#fff" opacity=".94" stroke="#263238" stroke-width="4"/><text x="72" y="168" font-size="45" font-weight="800">{html.escape(title)}</text><text x="72" y="215" font-size="24" fill="#5f6368">सेवा • समाज • सहभागिता • भारत</text>
<rect x="1110" y="655" width="118" height="42" rx="7" fill="#e53935"/><text x="1169" y="684" text-anchor="middle" font-size="22" font-weight="700" fill="#fff">AI चित्र</text>
</g></svg>'''
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>@font-face{{font-family:Noto;src:url('file://{font}');}}*{{box-sizing:border-box;margin:0;padding:0}}body{{width:1280px;height:720px;overflow:hidden;background:#fffdf7;font-family:Noto,sans-serif}}</style></head><body>{svg}</body></html>'''


def make_lineart_cover(path, r):
    base = os.path.basename(path)[:-5]
    os.makedirs(mc.IMG_DIR, exist_ok=True)
    out = os.path.join(mc.IMG_DIR, f"{base}-cover.png")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(cover_html(r))
        page.evaluate("document.fonts.ready")
        page.screenshot(path=out)
        browser.close()
    r["featured_image"] = f"images/{base}-cover.png"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    print("🖼 line-art cover:", out)


def main(paths):
    made = bad = 0
    for path in paths:
        if not path.endswith(".json") or not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                r = json.load(f)
            if not r.get("title"):
                continue
            # make_charts.py writes chart.file into the JSON. Reload afterwards;
            # otherwise the line-art writer would overwrite those new fields.
            if charts_missing(r):
                mc.main(path)
                with open(path, encoding="utf-8") as f:
                    r = json.load(f)
            # जिस रिपोर्ट में पहले से असली cover है (जैसे "बदलता भारत" की branded image), उसे न बदलें
            if img_exists(r.get("featured_image") or "") or r.get("image_search"):
                print("✔ cover पहले से है:", path)
                continue
            make_lineart_cover(path, r)
            made += 1
        except (Exception, SystemExit) as e:
            print(f"::error file={path}::cover/chart generation failed — {e}")
            bad += 1
    print(f"कुल: {made} line-art cover बने, {bad} असफल JSON")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

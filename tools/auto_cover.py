#!/usr/bin/env python3
"""नई रिपोर्टों के लिए line-art cover और charts अपने आप बनाता है।

python3 tools/auto_cover.py reports/a.json reports/b.json ...

Cover अब पुराने red-gradient title card की जगह 16:9 रंगीन line-art editorial
illustration के रूप में बनाया जाता है। यह deterministic SVG/HTML artwork है;
किसी external AI image API या secret की जरूरत नहीं है।
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_charts as mc  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

REPORTS = os.path.join(mc.ROOT, "reports")
W, H = 1280, 720


def needs_cover(r):
    if r.get("image_search"):
        return False
    fi = r.get("featured_image") or ""
    return not (fi.endswith(".png") and os.path.isfile(os.path.join(REPORTS, fi)))


def charts_missing(r):
    return any(not (c.get("file") and os.path.isfile(os.path.join(REPORTS, c["file"])))
               for c in (r.get("charts") or []))


def lineart_cover_html(r):
    title = re.sub(r"^विश्लेषण:\s*", "", r.get("title", "")).strip()
    if len(title) > 72:
        title = title[:69].rstrip() + "…"
    category = r.get("category") or "समाज"

    # साफ SVG editorial scene: volunteers, families, books, health table and plants.
    # Dark outlines + selected colour fills are intentional and consistent across articles.
    svg = f'''<svg width="1280" height="720" viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg">
      <rect width="1280" height="720" fill="#fffdf7"/>
      <path d="M0 520 Q170 470 330 520 T660 510 T990 515 T1280 500 V720 H0Z" fill="#e9f3df"/>
      <path d="M0 540 Q160 490 320 540 T640 530 T960 535 T1280 520" fill="none" stroke="#263238" stroke-width="6"/>
      <circle cx="1080" cy="105" r="58" fill="#ffd54f" stroke="#263238" stroke-width="6"/>
      <path d="M1060 45 Q1100 20 1138 48" fill="none" stroke="#ff8f00" stroke-width="10" stroke-linecap="round"/>
      <g stroke="#263238" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M95 515 V270 H260 V515" fill="#f7cfa8"/>
        <path d="M75 270 L178 190 L280 270 Z" fill="#e57373"/>
        <rect x="145" y="350" width="55" height="165" fill="#fff"/>
        <path d="M345 520 V300 H535 V520" fill="#d7e9f7"/>
        <path d="M325 300 L440 215 L555 300 Z" fill="#81c784"/>
        <rect x="390" y="365" width="65" height="155" fill="#fff"/>
        <path d="M780 520 V315 H1020 V520" fill="#ffe0b2"/>
        <path d="M755 315 L900 220 L1045 315 Z" fill="#90caf9"/>
        <rect x="855" y="385" width="70" height="135" fill="#fff"/>
        <path d="M1110 520 V365"/><path d="M1110 390 C1060 350 1050 320 1080 300 C1120 330 1145 350 1110 390Z" fill="#66bb6a"/>
        <path d="M1110 430 C1160 390 1180 360 1150 340 C1115 370 1095 395 1110 430Z" fill="#43a047"/>
      </g>
      <g stroke="#263238" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
        <!-- volunteer 1 -->
        <circle cx="610" cy="365" r="34" fill="#d49a6a"/><path d="M570 410 Q610 385 650 410 L670 535 H550 Z" fill="#f5f5f5"/>
        <path d="M570 420 L525 485 M650 420 L700 475" fill="none"/>
        <path d="M580 535 L565 620 M640 535 L655 620" fill="none"/>
        <path d="M555 620 H590 M640 620 H675" fill="none"/>
        <!-- volunteer 2 -->
        <circle cx="735" cy="385" r="32" fill="#b97850"/><path d="M700 425 Q735 405 770 425 L790 535 H680 Z" fill="#fff"/>
        <path d="M705 440 L660 490 M770 440 L815 485" fill="none"/>
        <path d="M710 535 L695 620 M760 535 L775 620" fill="none"/>
        <path d="M685 620 H720 M760 620 H795" fill="none"/>
        <!-- family/child -->
        <circle cx="450" cy="475" r="27" fill="#8d5a3b"/><path d="M420 510 Q450 495 480 510 L495 600 H405 Z" fill="#64b5f6"/>
        <path d="M420 525 L385 555 M480 525 L515 555" fill="none"/>
        <circle cx="520" cy="485" r="22" fill="#d49a6a"/><path d="M495 515 Q520 502 545 515 L555 585 H485 Z" fill="#ffb74d"/>
        <path d="M495 525 L470 550 M545 525 L570 550" fill="none"/>
        <!-- service table -->
        <path d="M820 535 H1050 L1025 650 H845 Z" fill="#fff"/>
        <path d="M845 570 H1025" fill="none"/>
        <rect x="870" y="505" width="55" height="65" rx="8" fill="#ef5350"/>
        <rect x="940" y="505" width="55" height="65" rx="8" fill="#42a5f5"/>
        <path d="M895 535 H900 M965 535 H970" fill="none"/>
        <!-- books -->
        <path d="M575 500 H665 V530 H575 Z" fill="#42a5f5"/><path d="M590 470 H680 V500 H590 Z" fill="#ffca28"/>
        <!-- plants -->
        <path d="M285 600 Q320 555 350 600 Q320 625 285 600Z" fill="#66bb6a"/>
        <path d="M350 600 Q385 550 415 600 Q385 625 350 600Z" fill="#43a047"/>
      </g>
      <g font-family="Noto, sans-serif" fill="#263238">
        <rect x="42" y="38" width="180" height="52" rx="8" fill="#ffffff" stroke="#b71c1c" stroke-width="4"/>
        <text x="132" y="74" text-anchor="middle" font-size="27" font-weight="700" fill="#b71c1c">{html.escape(category)}</text>
        <rect x="38" y="112" width="1204" height="142" rx="16" fill="#ffffff" opacity="0.94" stroke="#263238" stroke-width="4"/>
        <text x="72" y="168" font-size="45" font-weight="800">{html.escape(title)}</text>
        <text x="72" y="215" font-size="24" fill="#5f6368">सेवा • समाज • सहभागिता • भारत</text>
        <rect x="1110" y="655" width="118" height="42" rx="7" fill="#e53935"/>
        <text x="1169" y="684" text-anchor="middle" font-size="22" font-weight="700" fill="#fff">AI चित्र</text>
      </g>
    </svg>'''

    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
      @font-face {{font-family:Noto;src:url('file://{os.path.join(mc.ROOT, 'tools', 'fonts', 'NotoSansDevanagari.ttf')}');}}
      *{{box-sizing:border-box;margin:0;padding:0}} body{{width:1280px;height:720px;overflow:hidden;background:#fffdf7;font-family:Noto,sans-serif}}
    </style></head><body>{svg}</body></html>'''


def make_lineart_cover(path, r):
    base = os.path.basename(path)[:-5]
    os.makedirs(mc.IMG_DIR, exist_ok=True)
    out = os.path.join(mc.IMG_DIR, f"{base}-cover.png")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.set_content(lineart_cover_html(r))
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=out)
        b.close()
    r["featured_image"] = f"images/{base}-cover.png"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    print("🖼  line-art cover:", "reports/images/" + f"{base}-cover.png")


def main(paths):
    made, bad = 0, 0
    for path in paths:
        if not (path.endswith(".json") and os.path.isfile(path)):
            continue
        try:
            r = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"::warning file={path}::टूटी JSON, वेबसाइट इसे नहीं उठा पाएगी — {e}")
            bad += 1
            continue
        if not r.get("title"):
            print(f"⏭  {path}: title नहीं, छोड़ा")
            continue
        try:
            # Charts remain compatible with the existing renderer. Its cover is
            # deliberately overwritten by our new line-art cover below.
            if charts_missing(r):
                mc.main(path)
            make_lineart_cover(path, r)
            made += 1
        except SystemExit as e:
            print(f"::warning file={path}::chart डेटा गलत ({e}), line-art cover फिर भी बनाया जाएगा")
            try:
                make_lineart_cover(path, r)
                made += 1
            except Exception as ce:
                print(f"::warning file={path}::cover नहीं बना — {ce}")
                bad += 1
        except Exception as e:
            print(f"::warning file={path}::cover नहीं बना — {e}")
            bad += 1
    print(f"कुल: {made} line-art cover बने, {bad} टूटी/असफल JSON")


if __name__ == "__main__":
    main(sys.argv[1:])

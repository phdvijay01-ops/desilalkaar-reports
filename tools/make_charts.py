#!/usr/bin/env python3
"""रिपोर्ट के graph और cover image बनाता है (Chromium से, सही हिंदी font के साथ)।

python3 tools/make_charts.py reports/<file>.json

रिपोर्ट JSON के "charts" से हर graph की PNG और एक cover PNG बनाकर reports/images/ में रखता है,
और JSON में हर chart का "file" और "featured_image" भर देता है।
"""
import html
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "tools", "fonts", "NotoSansDevanagari.ttf")
IMG_DIR = os.path.join(ROOT, "reports", "images")
W, H = 1200, 675
RED, INK, MUTED, GRID, BG = "#b71c1c", "#1f1f1f", "#5f5f5f", "#e6e6e6", "#ffffff"
SERIES = ["#b71c1c", "#1e5aa8", "#2e7d32", "#ef6c00"]

BASE_CSS = f"""
@font-face {{ font-family: 'Noto'; src: url('file://{FONT}'); }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ width: {W}px; height: {H}px; font-family: 'Noto', sans-serif; color: {INK}; background: {BG}; overflow: hidden; }}
"""


def indian(n):
    s = str(abs(int(n)))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = ",".join([head[max(0, i - 2):i] for i in range(len(head), 0, -2)][::-1])
        s = head + "," + tail
    return ("-" if n < 0 else "") + s


def fmt(v, unit):
    s = f"{v:.1f}".rstrip("0").rstrip(".") if isinstance(v, float) and not v.is_integer() else indian(v)
    return s + (unit or "")


def bar_svg(c):
    labels, unit = c["labels"], c.get("unit", "")
    series = c.get("series") or [{"name": "", "values": c["values"]}]
    n, k = len(labels), len(series)
    vmax = max(max(s["values"]) for s in series) or 1
    left, right, top, bottom = 40, 40, 30, 90
    pw, ph = W - left - right, H - 250 - top - bottom
    group = pw / n
    bw = min(110, group * 0.7 / k)
    parts = []
    for i in range(5):
        y = top + ph - ph * i / 4
        parts.append(f'<line x1="{left}" x2="{W-right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="2"/>')
    for gi, lab in enumerate(labels):
        gx = left + group * gi + (group - bw * k) / 2
        for si, s in enumerate(series):
            v = s["values"][gi]
            h = ph * v / vmax
            x, y = gx + si * bw, top + ph - h
            col = SERIES[si % len(SERIES)]
            parts.append(f'<rect x="{x+3:.1f}" y="{y:.1f}" width="{bw-6:.1f}" height="{h:.1f}" rx="4" fill="{col}"/>')
            parts.append(f'<text x="{x+bw/2:.1f}" y="{y-10:.1f}" text-anchor="middle" font-size="{26 if k == 1 else 21}" font-weight="700" fill="{INK}">{html.escape(fmt(v, unit))}</text>')
        parts.append(f'<text x="{left+group*gi+group/2:.1f}" y="{top+ph+38}" text-anchor="middle" font-size="{22 if n <= 6 else 18}" fill="{INK}">{html.escape(lab)}</text>')
    return f'<svg width="{W}" height="{H-250+0}" viewBox="0 0 {W} {H-250}">{"".join(parts)}</svg>'


def hbar_svg(c):
    labels, vals, unit = c["labels"], c["values"], c.get("unit", "")
    n = len(labels)
    vmax = max(vals) or 1
    top, rowh = 10, min(64, (H - 260) / n)
    labw, pw = 380, W - 380 - 160
    parts = []
    for i, (lab, v) in enumerate(zip(labels, vals)):
        y = top + i * rowh
        w = pw * v / vmax
        parts.append(f'<text x="{labw-16}" y="{y+rowh*0.62:.1f}" text-anchor="end" font-size="22" fill="{INK}">{html.escape(lab)}</text>')
        parts.append(f'<rect x="{labw}" y="{y+rowh*0.15:.1f}" width="{w:.1f}" height="{rowh*0.7:.1f}" rx="4" fill="{RED}"/>')
        parts.append(f'<text x="{labw+w+12:.1f}" y="{y+rowh*0.62:.1f}" font-size="24" font-weight="700" fill="{INK}">{html.escape(fmt(v, unit))}</text>')
    return f'<svg width="{W}" height="{H-250}" viewBox="0 0 {W} {H-250}">{"".join(parts)}</svg>'


def chart_html(c):
    svg = hbar_svg(c) if c.get("type") == "hbar" else bar_svg(c)
    legend = ""
    if c.get("series"):
        legend = "".join(
            f'<span style="margin-right:28px"><i style="display:inline-block;width:18px;height:18px;background:{SERIES[i % 4]};border-radius:3px;vertical-align:-2px;margin-right:8px"></i>{html.escape(s["name"])}</span>'
            for i, s in enumerate(c["series"]))
        legend = f'<div style="font-size:22px;color:{MUTED};margin:6px 0 0">{legend}</div>'
    return f"""<html><head><meta charset="utf-8"><style>{BASE_CSS}
.wrap {{ padding: 34px 40px 0; }} h1 {{ font-size: 36px; line-height: 1.3; font-weight: 700; }}
.sub {{ font-size: 23px; color: {MUTED}; margin-top: 4px; }}
.foot {{ position: absolute; bottom: 0; left: 0; right: 0; height: 56px; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-top: 3px solid {RED}; font-size: 20px; color: {MUTED}; }}
.foot b {{ color: {RED}; }}</style></head><body>
<div class="wrap"><h1>{html.escape(c['title'])}</h1><div class="sub">{html.escape(c.get('subtitle', ''))}</div>{legend}</div>
<div style="position:absolute;top:{170 if c.get('series') else 150}px;left:0">{svg}</div>
<div class="foot"><span>स्रोत: {html.escape(c['source'])}</span><b>देसी ललकार · विश्लेषण</b></div></body></html>"""


def cover_html(r):
    tag = "विश्लेषण" if r["title"].startswith("विश्लेषण") else (r.get("category") or "खबर")
    t = re.sub(r"^विश्लेषण:\s*", "", r["title"])
    cs = r.get("cover_stat") or {}
    stat = ""
    if cs.get("value"):
        stat = (f'<div style="position:absolute;left:70px;bottom:120px;display:flex;align-items:baseline;gap:24px">'
                f'<span style="font-size:{110 if len(cs["value"]) <= 7 else 80}px;font-weight:700;line-height:1;white-space:nowrap">{html.escape(cs["value"])}</span>'
                f'<span style="font-size:32px;max-width:640px;line-height:1.35">{html.escape(cs.get("label", ""))}</span></div>')
    return f"""<html><head><meta charset="utf-8"><style>{BASE_CSS}
body {{ background: linear-gradient(135deg, #7f0000 0%, {RED} 60%, #d84315 100%); color: #fff; }}
.tag {{ position: absolute; top: 56px; left: 70px; background: #fff; color: {RED}; font-size: 30px; font-weight: 700; padding: 6px 22px; border-radius: 6px; }}
h1 {{ position: absolute; top: 160px; left: 70px; right: 70px; font-size: {58 if len(t) < 70 else 50}px; line-height: 1.35; font-weight: 700; }}
.foot {{ position: absolute; bottom: 50px; left: 70px; right: 70px; display: flex; justify-content: space-between; font-size: 28px; opacity: .92; }}
</style></head><body><div class="tag">{html.escape(tag)}</div><h1>{html.escape(t)}</h1>
{stat}<div class="foot"><span>{html.escape(r.get('category', ''))}</span><b>देसी ललकार</b></div></body></html>"""


def check(c, i):
    for k in ("id", "title", "labels", "source", "caption"):
        if not c.get(k):
            sys.exit(f"❌ chart {i}: '{k}' खाली")
    vals = [c["values"]] if "values" in c else [s["values"] for s in c.get("series", [])]
    if not vals or any(len(v) != len(c["labels"]) or not all(isinstance(x, (int, float)) for x in v) for v in vals):
        sys.exit(f"❌ chart {c['id']}: values और labels की गिनती/अंक गलत")
    if not re.fullmatch(r"[a-z0-9-]+", c["id"]):
        sys.exit(f"❌ chart id सिर्फ a-z0-9-: {c['id']}")


def main(path):
    r = json.load(open(path, encoding="utf-8"))
    base = os.path.basename(path)[:-5]
    os.makedirs(IMG_DIR, exist_ok=True)
    charts = r.get("charts") or []
    for i, c in enumerate(charts):
        check(c, i)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        jobs = [(f"{base}-cover.png", cover_html(r))] + [(f"{base}-{c['id']}.png", chart_html(c)) for c in charts]
        for name, doc in jobs:
            pg.set_content(doc)
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=os.path.join(IMG_DIR, name))
            print("✅", "reports/images/" + name)
        b.close()
    r["featured_image"] = f"images/{base}-cover.png"
    for c in charts:
        c["file"] = f"images/{base}-{c['id']}.png"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])

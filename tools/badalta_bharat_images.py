#!/usr/bin/env python3
""""बदलता भारत" शृंखला की images (देसी ललकार branding के साथ) बनाता है।

python3 tools/badalta_bharat_images.py <spec.json>

spec.json का रूप (कोई भी image छोड़नी हो तो उसकी key हटा दें):
{
 "prefix": "2026-10-30-ujjwala-yojana",          # images/<prefix>-<name>.png
 "part": 2,                                        # शृंखला का भाग
 "featured": {"title": "उज्ज्वला योजना", "subtitle": "...", "line": "...",
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
        pages["featured"] = featured(spec["featured"], spec.get("part", ""))
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

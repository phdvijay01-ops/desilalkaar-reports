#!/usr/bin/env python3
"""देसी ललकार ई-पेपर: किसी तारीख की सभी reports/<date>-*.json से अख़बार-शैली PDF बनाता है।

python3 tools/make_epaper.py 2026-11-10            # epaper/2026-11-10.pdf + thumbnail + editions.json
python3 tools/make_epaper.py 2026-11-10 out.pdf    # सिर्फ़ PDF, किसी और जगह

PDF सिर्फ़ reports/ में पहले से छपे (validate पास) लेखों से बनता है; कोई नया तथ्य नहीं जोड़ता।
वेबसाइट पर ई-पेपर: tools/EPAPER_SETUP.md
"""
import glob
import shutil
import subprocess
import tempfile
import html
import json
import os
import re
import sys
from datetime import date

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "tools", "fonts", "NotoSansDevanagari.ttf")
LOGO = "file://" + os.path.join(ROOT, "tools", "brand", "logo.png")
e = html.escape
MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
DAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]


TMP = tempfile.mkdtemp(prefix="epaper-")


def img(rel):
    """PDF हल्की रहे इसलिए PNG की JPEG copy (temp में) इस्तेमाल होती है।"""
    p = os.path.join(ROOT, "reports", rel) if rel else ""
    if not rel or not os.path.exists(p):
        return ""
    try:
        from PIL import Image
        q = os.path.join(TMP, os.path.basename(p) + ".jpg")
        if not os.path.exists(q):
            Image.open(p).convert("RGB").save(q, "JPEG", quality=82, optimize=True)
        return "file://" + q
    except Exception:
        return "file://" + p


def body_with_charts(r):
    c = r["content_html"]
    for ch in r.get("charts", []):
        src = img(ch.get("file", ""))
        h2 = ch.get("after_h2")
        if not src or not h2:
            continue
        tag = f"<h2>{h2}</h2>"
        i = c.find(tag)
        if i < 0:
            continue
        j = c.find("</p>", i)
        j = j + 4 if j > 0 else i + len(tag)
        fig = (f'<figure class="chart"><img src="{src}"><figcaption>{e(ch.get("caption", ""))}'
               f' <span>स्रोत: {e(ch.get("source", ""))}</span></figcaption></figure>')
        c = c[:j] + fig + c[j:]
    return c


def article(r, kicker):
    cover = img(r.get("featured_image", ""))
    title = r["title"].replace("विश्लेषण: ", "")
    srcs = "".join(f"<li>{e(s['name'])}</li>" for s in r.get("sources", [])[:12])
    return f"""<section class="art">
<div class="kick">{e(kicker)}</div>
<h1>{e(title)}</h1>
<p class="dek">{e(r.get('excerpt', ''))}</p>
{f'<img class="cover" src="{cover}">' if cover else ''}
<div class="cols">{body_with_charts(r)}
<div class="srcs"><b>प्रमुख स्रोत</b><ul>{srcs}</ul><p>पूरा लेख और सभी स्रोत: desilalkaar.com</p></div></div>
</section>"""


def main(d, out):
    files = sorted(glob.glob(os.path.join(ROOT, "reports", f"{d}-*.json")))
    reps = []
    for f in files:
        try:
            r = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if r.get("title") and r.get("content_html"):
            reps.append(r)
    if not reps:
        print(f"{d}: कोई रिपोर्ट नहीं, ई-पेपर नहीं बना")
        return None
    # "बदलता भारत" लेख पहले पन्ने की मुख्य खबर
    reps.sort(key=lambda r: 0 if "बदलता भारत" in r.get("tags", []) else 1)
    y, m, dd = map(int, d.split("-"))
    dt = date(y, m, dd)
    dstr = f"{DAYS[dt.weekday()]}, {dd} {MONTHS[m-1]} {y}"
    lead = reps[0]
    others = reps[1:]
    lead_cover = img(lead.get("featured_image", ""))
    briefs = "".join(
        f'<div class="brief">' + (f'<img src="{img(r.get("featured_image", ""))}">' if img(r.get("featured_image", "")) else '') + f'<h3>{e(r["title"].replace("विश्लेषण: ", ""))}</h3>'
        f'<p>{e(r.get("excerpt", ""))}</p><span>पूरा विश्लेषण अंदर</span></div>' for i, r in enumerate(others))
    keypoints = re.search(r"<h2>मुख्य बातें</h2>\s*(<ul>.*?</ul>)", lead["content_html"], re.S)
    front = f"""<section class="front">
<div class="mast"><img src="{LOGO}"><div><div class="name">देसी ललकार</div><div class="tag">शोध-आधारित विश्लेषण · ई-पेपर</div></div>
<div class="date">{dstr}<br><small>desilalkaar.com</small></div></div>
<div class="tri"></div>
<div class="lead"><div class="kick">{'बदलता भारत' if 'बदलता भारत' in lead.get('tags', []) else 'मुख्य खबर'}</div>
<h1>{e(lead['title'])}</h1>
<div class="leadgrid">{f'<img src="{lead_cover}">' if lead_cover else '<div></div>'}<div><p class="dek">{e(lead.get('excerpt', ''))}</p>
{keypoints.group(1) if keypoints else ''}<p class="more">पूरा लेख पेज 2 पर</p></div></div></div>
<div class="kick" style="margin-top:6mm">आज के विश्लेषण</div>
<div class="briefs">{briefs}</div>
</section>"""
    kick = lambda r: "बदलता भारत" if "बदलता भारत" in r.get("tags", []) else r.get("category", "विश्लेषण")
    arts = "".join(article(r, kick(r)) for r in reps)
    css = f"""
@font-face{{font-family:N;src:url('file://{FONT}')}}
@page{{size:A3;margin:22mm 13mm 16mm}}
*{{box-sizing:border-box}}
body{{font-family:N,sans-serif;color:#1d1414;margin:0;font-size:10.6pt;line-height:1.5}}
.mast{{display:flex;align-items:center;gap:8mm;border-bottom:3px solid #5c0f12;padding-bottom:3mm}}
.mast img{{height:30mm}} .name{{font-size:46pt;font-weight:800;color:#5c0f12;line-height:1}}
.tag{{font-size:13pt;color:#b8232a;font-weight:700;margin-top:2mm}}
.date{{margin-left:auto;text-align:right;font-size:12pt;font-weight:700}} .date small{{color:#b8232a;font-size:11pt}}
.tri{{height:2.2mm;background:linear-gradient(90deg,#ff9933 0 33%,#fff 33% 66%,#138808 66%);margin:1.5mm 0 5mm;border:0.2mm solid #ddd}}
.kick{{display:inline-block;background:#b8232a;color:#fff;font-weight:800;font-size:10pt;padding:0.8mm 3mm;border-radius:1mm}}
.lead h1{{font-size:27pt;line-height:1.2;color:#5c0f12;margin:2mm 0 3mm}}
.leadgrid{{display:grid;grid-template-columns:55% 1fr;gap:6mm}} .leadgrid img{{width:100%;border:0.3mm solid #ccc}}
.leadgrid ul{{padding-left:5mm;margin:2mm 0}} .leadgrid li{{margin-bottom:1mm;font-size:9.4pt;line-height:1.4}}
.dek{{font-size:12pt;font-weight:600;color:#3a2a2a;margin:0 0 3mm}}
.more{{font-weight:800;color:#b8232a}}
.briefs{{display:grid;grid-template-columns:repeat(3,1fr);gap:5mm;margin-top:3mm}}
.brief{{border-top:2px solid #5c0f12;padding-top:2mm;break-inside:avoid}}
.brief img{{width:100%;height:30mm;object-fit:cover}} .brief h3{{font-size:12pt;line-height:1.25;margin:1.5mm 0;color:#5c0f12}}
.brief p{{font-size:9pt;margin:0;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
.brief span{{font-size:8.5pt;font-weight:800;color:#b8232a}}
.art{{break-before:page}}
.art h1{{font-size:24pt;line-height:1.2;color:#5c0f12;margin:2mm 0 2.5mm}}
.cover{{width:100%;max-height:150mm;object-fit:contain;margin-bottom:4mm;border:0.3mm solid #ccc}}
.cols{{column-count:3;column-gap:7mm;column-rule:0.2mm solid #ddd}}
.cols h2{{font-size:13pt;color:#b8232a;margin:3mm 0 1.5mm;break-after:avoid;line-height:1.3}}
.cols h3{{font-size:11pt;color:#5c0f12;margin:2.5mm 0 1mm;break-after:avoid}}
.cols p{{margin:0 0 2mm;text-align:justify}} .cols ul,.cols ol{{padding-left:4.5mm;margin:0 0 2mm}}
.cols table{{width:100%;border-collapse:collapse;font-size:8.3pt;margin:2mm 0;break-inside:avoid}}
.cols th{{background:#5c0f12;color:#fff;padding:1mm}} .cols td{{border:0.2mm solid #ccc;padding:0.8mm 1mm}}
.chart{{margin:2mm 0 3mm;break-inside:avoid}} .chart img{{width:100%;border:0.2mm solid #ccc}}
.chart figcaption{{font-size:8.3pt;color:#444}} .chart span{{color:#888}}
.srcs{{font-size:8pt;color:#555;border-top:1px solid #5c0f12;margin-top:3mm;padding-top:1.5mm;break-inside:avoid}}
.srcs ul{{padding-left:4mm;margin:1mm 0}}
"""
    page = f"<html><head><meta charset=utf-8><style>{css}</style></head><body>{front}{arts}</body></html>"
    footer = (f'<div style="font-family:Noto Sans Devanagari,sans-serif;font-size:8px;width:100%;padding:0 13mm;display:flex;justify-content:space-between;color:#5c0f12">'
              f'<span>देसी ललकार ई-पेपर · {dstr}</span><span>desilalkaar.com · पेज <span class="pageNumber"></span>/<span class="totalPages"></span></span></div>')
    with sync_playwright() as p:
        exe = os.environ.get("CHROME_PATH")
        br = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        pg = br.new_page()
        pg.goto("file://" + os.path.join(ROOT, "tools", "brand", "blank.html"))
        pg.set_content(page)
        pg.wait_for_timeout(1500)
        import base64
        from PIL import Image
        import io
        lg = Image.open(os.path.join(ROOT, "tools", "brand", "logo.png")).convert("RGBA")
        lg.thumbnail((120, 120))
        buf = io.BytesIO()
        lg.save(buf, "PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        header = (f'<div style="width:100%;margin:0 13mm;padding-bottom:1.5mm;border-bottom:1.5px solid #5c0f12;display:flex;align-items:center;'
                  f'justify-content:space-between;font-family:Noto Sans Devanagari,sans-serif;-webkit-print-color-adjust:exact">'
                  f'<span style="display:flex;align-items:center;gap:6px"><img src="data:image/png;base64,{b64}" style="height:32px">'
                  f'<b style="font-size:13px;color:#5c0f12">देसी ललकार</b><span style="font-size:9px;color:#b8232a">ई-पेपर</span></span>'
                  f'<span style="font-size:9px;color:#5c0f12">{dstr} · desilalkaar.com</span></div>')
        pg.pdf(path=out, format="A3", print_background=True, display_header_footer=True,
               header_template=header, footer_template=footer,
               margin={"top": "22mm", "bottom": "16mm", "left": "13mm", "right": "13mm"})
        br.close()
    print(out, len(reps), "लेख")
    return reps


def publish(d):
    """epaper/<d>.pdf, epaper/<d>.jpg (पहला पेज) और epaper/editions.json (website इसी को पढ़ती है)"""
    out_dir = os.path.join(ROOT, "epaper")
    os.makedirs(out_dir, exist_ok=True)
    pdf = os.path.join(out_dir, f"{d}.pdf")
    reps = main(d, pdf)
    if not reps:
        return
    jpg = os.path.join(out_dir, f"{d}.jpg")
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "50", "-jpeg", "-singlefile", pdf, jpg[:-4]], check=True)
    pages = 0
    if shutil.which("pdfinfo"):
        m = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout)
        pages = int(m.group(1)) if m else 0
    idx_path = os.path.join(out_dir, "editions.json")
    try:
        idx = json.load(open(idx_path, encoding="utf-8"))
    except Exception:
        idx = {"editions": []}
    reps.sort(key=lambda r: 0 if "बदलता भारत" in r.get("tags", []) else 1)
    ed = {"date": d, "pdf": f"epaper/{d}.pdf", "thumb": f"epaper/{d}.jpg" if os.path.exists(jpg) else "",
          "pages": pages, "size_kb": os.path.getsize(pdf) // 1024,
          "lead": reps[0]["title"], "headlines": [r["title"] for r in reps]}
    idx["editions"] = [x for x in idx.get("editions", []) if x.get("date") != d] + [ed]
    idx["editions"].sort(key=lambda x: x["date"], reverse=True)
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(idx_path, "अपडेट")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        publish(sys.argv[1])

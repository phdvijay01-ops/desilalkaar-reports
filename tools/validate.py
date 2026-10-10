#!/usr/bin/env python3
"""रिपोर्ट JSON की जाँच: python3 tools/validate.py reports/<file>.json"""
import json, re, sys
from html.parser import HTMLParser

CATS = ["मध्य प्रदेश", "भारत", "राजनीति", "अर्थव्यवस्था", "शिक्षा", "स्वास्थ्य", "तकनीक", "कृषि",
        "दुनिया", "समाज", "रोज़गार", "पर्यावरण", "विशेष"]
ALLOWED = {"p", "h2", "h3", "ul", "ol", "li", "strong", "table", "tr", "th", "td", "thead", "tbody"}
BANNED = ["आइए जानते हैं", "गौरतलब है", "जानिए"]


class TagCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.bad, self.text, self.h2, self.tables = set(), [], 0, 0

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED:
            self.bad.add(tag)
        if attrs:
            self.bad.add(tag + " (attributes)")
        self.h2 += tag == "h2"
        self.tables += tag == "table"

    def handle_endtag(self, tag):
        if tag not in ALLOWED:
            self.bad.add(tag)

    def handle_data(self, d):
        self.text.append(d)


def main(path):
    errs, warns = [], []
    raw = open(path, encoding="utf-8").read()
    try:
        r = json.loads(raw)
    except Exception as e:
        print("❌ JSON गलत:", e)
        return 1
    for k in ["title", "meta_description", "excerpt", "content_html", "category", "tags", "slug", "sources", "image_keywords", "image_alt"]:
        if not r.get(k):
            errs.append(f"'{k}' खाली/गायब")
    t = r.get("title", "")
    if not t.startswith("विश्लेषण:"):
        errs.append("title 'विश्लेषण:' से शुरू होना चाहिए")
    if not (40 <= len(t) <= 110):
        warns.append(f"title लंबाई {len(t)} (55–90 ठीक)")
    md = r.get("meta_description", "")
    if not (110 <= len(md) <= 175):
        warns.append(f"meta_description लंबाई {len(md)} (140–160 ठीक)")
    if r.get("category") not in CATS:
        errs.append(f"category '{r.get('category')}' list में नहीं")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", r.get("slug", "")):
        errs.append("slug सिर्फ a-z, 0-9 और - में")
    p = TagCheck()
    p.feed(r.get("content_html", ""))
    if p.bad:
        errs.append("मना वाले HTML tags: " + ", ".join(sorted(p.bad)))
    words = len("".join(p.text).split())
    if words < 1100:
        errs.append(f"सिर्फ {words} शब्द (कम से कम 1100, लक्ष्य 1200–1800)")
    elif words > 2100:
        errs.append(f"{words} शब्द — बहुत लंबा (लक्ष्य 1200–1800)")
    elif not (1200 <= words <= 1800):
        warns.append(f"{words} शब्द (लक्ष्य 1200–1800)")
    if p.h2 < 6:
        warns.append(f"सिर्फ {p.h2} <h2> हिस्से")
    if p.tables < 1:
        warns.append("आंकड़ों की <table> नहीं है")
    for b in BANNED:
        if b in r.get("content_html", "") or b in t:
            errs.append(f"मना वाला वाक्यांश: '{b}'")
    srcs = r.get("sources") or []
    good = [s for s in srcs if isinstance(s, dict) and str(s.get("link", "")).startswith("https://") and s.get("name")]
    if len(good) < 5:
        errs.append(f"सिर्फ {len(good)} सही स्रोत (कम से कम 5, https)")
    if len(good) != len(srcs):
        errs.append("कुछ sources में name/https link नहीं")
    if "\\u09" in raw or "\\u0" in raw[:2000]:
        warns.append("हिंदी \\u escapes में है — ensure_ascii=False से लिखें")
    import os
    rdir = os.path.dirname(os.path.abspath(path))
    charts = r.get("charts") or []
    if not charts:
        warns.append("कोई graph (charts) नहीं — 2–3 graph जोड़ें और tools/make_charts.py चलाएँ")
    fi = r.get("featured_image", "")
    if not fi:
        warns.append("featured_image नहीं — tools/make_charts.py चलाएँ")
    elif not os.path.isfile(os.path.join(rdir, fi)):
        errs.append(f"featured_image file नहीं मिली: {fi}")
    content = r.get("content_html", "")
    for c in charts:
        cid = c.get("id", "?")
        for k in ("title", "source", "caption", "labels"):
            if not c.get(k):
                errs.append(f"chart {cid}: '{k}' खाली")
        if not c.get("file") or not os.path.isfile(os.path.join(rdir, c.get("file", ""))):
            errs.append(f"chart {cid}: PNG नहीं बनी — tools/make_charts.py चलाएँ")
        h2 = c.get("after_h2", "")
        if h2 and f"<h2>{h2}</h2>" not in content:
            errs.append(f"chart {cid}: after_h2 '{h2}' वाला <h2> लेख में नहीं")
    if "विश्लेषण" not in (r.get("tags") or []):
        warns.append("tags में 'विश्लेषण' नहीं")
    for w in warns:
        print("⚠️ ", w)
    for e in errs:
        print("❌", e)
    if not errs:
        print(f"✅ OK — {words} शब्द, {len(good)} स्रोत, {p.h2} हिस्से, {p.tables} table, {len(charts)} graph")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

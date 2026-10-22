#!/usr/bin/env python3
"""नई रिपोर्टों के लिए cover (और charts) अपने आप बनाता है — GitHub Action से चलता है।

python3 tools/auto_cover.py reports/a.json reports/b.json ...

हर दी गई JSON के लिए:
  - टूटी JSON हो → छोड़ देता है और चेतावनी देता है (वेबसाइट भी उसे नहीं उठा पाएगी)।
  - "image_search" हो → कुछ नहीं (वेबसाइट Wikimedia से मुफ़्त तस्वीर लेगी)।
  - featured_image पहले से है और उसकी PNG repo में मौजूद है → कुछ नहीं।
  - नहीं तो tools/make_charts.py से cover (और जिन charts की PNG नहीं बनी, वे भी) बनाता है
    और JSON में featured_image भर देता है।
Chart का डेटा गलत हो तो सिर्फ cover बनता है, charts छोड़ दिए जाते हैं।
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_charts as mc  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

REPORTS = os.path.join(mc.ROOT, "reports")


def needs_cover(r):
    if r.get("image_search"):
        return False
    fi = r.get("featured_image") or ""
    return not (fi.endswith(".png") and os.path.isfile(os.path.join(REPORTS, fi)))


def charts_missing(r):
    return any(not (c.get("file") and os.path.isfile(os.path.join(REPORTS, c["file"])))
               for c in (r.get("charts") or []))


def cover_only(path, r):
    base = os.path.basename(path)[:-5]
    os.makedirs(mc.IMG_DIR, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": mc.W, "height": mc.H})
        pg.set_content(mc.cover_html(r))
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=os.path.join(mc.IMG_DIR, f"{base}-cover.png"))
        b.close()
    r["featured_image"] = f"images/{base}-cover.png"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)


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
        if not needs_cover(r) and not charts_missing(r):
            print(f"✔  {path}: image पहले से है")
            continue
        try:
            mc.main(path)  # cover + charts
        except SystemExit as e:
            print(f"::warning file={path}::chart डेटा गलत ({e}), सिर्फ cover बना रहे हैं")
            if needs_cover(r):
                cover_only(path, r)
        print(f"🖼  {path}: cover बना")
        made += 1
    print(f"कुल: {made} cover बने, {bad} टूटी JSON")


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python3
"""ChatGPT (Codex) के भक्ति PR की जाँच — GitHub Action `gpt-bhakti-autopublish.yml` इसे चलाता है।

उपयोग: python3 tools/check_gpt_bhakti_pr.py <base_sha> <head_sha>

PR तभी "पास" होता है जब:
  * उसमें सिर्फ़ नई फ़ाइलें reports/YYYY-MM-DD-<slug>-gpt-bhakti.json, उनकी cover PNG
    (reports/images/...gpt-bhakti...png) और log.md में जोड़ी गई पंक्तियाँ हों;
  * पहले से मौजूद कोई रिपोर्ट/कोड/workflow बदला या हटाया न गया हो;
  * हर JSON tools/validate.py में बिना error के पास हो;
  * category "विशेष", tags में "भक्ति", slug "-gpt-bhakti" पर खत्म, फ़ाइल नाम = तारीख + slug;
  * featured_image मौजूद हो और PR में ही जोड़ी गई हो;
  * शीर्षक के पहले 4 शब्द किसी पुराने लेख से न मिलें (वेबसाइट का duplicate filter);
  * उसी कथा का slug पिछले 60 दिन में न आया हो।

पास होने पर stdout की आखिरी पंक्ति `PASS <json files...>` होती है; वरना `FAIL` और exit 1।
कारण GITHUB_STEP_SUMMARY / PR comment के लिए check-report.md में लिखे जाते हैं।
"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

JSON_RE = re.compile(r"^reports/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*-gpt-bhakti)\.json$")
IMG_RE = re.compile(r"^reports/images/[a-z0-9-]*gpt-bhakti[a-z0-9-]*\.png$")
IGNORED_RE = re.compile(r"(^|/)__pycache__/|\.pyc$")
MAX_ARTICLES = 3
MAX_IMG_BYTES = 3 * 1024 * 1024
ALLOWED_VALIDATE_WARN_ONLY = True  # validate.py की चेतावनियाँ ठीक हैं, errors नहीं


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def first_words(title, n=4):
    t = re.sub(r"[^\w\sऀ-ॿ]", " ", title)
    return " ".join(t.split()[:n])


def main(base, head):
    errs, notes, jsons, imgs = [], [], [], []
    diff = git("diff", "--name-status", "--no-renames", f"{base}...{head}").strip().splitlines()
    if not diff:
        errs.append("PR में कोई बदलाव नहीं")
    for line in diff:
        status, path = line.split("\t", 1)
        if IGNORED_RE.search(path):
            notes.append(f"अनदेखा किया: {path}")
            continue
        if path == "log.md":
            if status != "M":
                errs.append("log.md हटाया/नया बनाया गया")
                continue
            num = git("diff", "--numstat", f"{base}...{head}", "--", "log.md").split()
            if num and num[1] != "0":
                errs.append("log.md की पुरानी पंक्तियाँ बदली/हटाई गईं — सिर्फ़ नई पंक्ति जोड़नी है")
            continue
        if status != "A":
            errs.append(f"पहले से मौजूद फ़ाइल बदली/हटाई गई: {path} ({status})")
            continue
        if JSON_RE.match(path):
            jsons.append(path)
        elif IMG_RE.match(path):
            imgs.append(path)
        else:
            errs.append(f"अनुमति से बाहर की फ़ाइल: {path}")

    if not jsons:
        errs.append("कोई reports/YYYY-MM-DD-<slug>-gpt-bhakti.json फ़ाइल नहीं")
    if len(jsons) > MAX_ARTICLES:
        errs.append(f"एक PR में {len(jsons)} लेख — अधिकतम {MAX_ARTICLES}")

    for im in imgs:
        if os.path.getsize(im) > MAX_IMG_BYTES:
            errs.append(f"image बहुत बड़ी (>3 MB): {im}")
        with open(im, "rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                errs.append(f"असली PNG नहीं: {im}")

    # पुराने शीर्षक और slug (base = main)
    old_titles, old_slugs = {}, set()
    cutoff = (dt.date.today() - dt.timedelta(days=60)).isoformat()
    base_files = [p for p in git("ls-tree", "-r", "--name-only", base, "reports/").splitlines() if p.endswith(".json")]
    for p in base_files:
        try:
            d = json.loads(git("show", f"{base}:{p}"))
        except Exception:
            continue
        if d.get("title"):
            old_titles[first_words(d["title"])] = p
        m = re.match(r"reports/(\d{4}-\d{2}-\d{2})-(.+)\.json$", p)
        if m and m.group(1) >= cutoff:
            core = re.sub(r"-(gpt-)?bhakti$", "", m.group(2))
            old_slugs.add(core)

    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
    seen_fw = {}
    for p in jsons:
        m = JSON_RE.match(p)
        date_s, slug_from_name = m.group(1), m.group(2)
        pre = f"{os.path.basename(p)}:"
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            errs.append(f"{pre} JSON गलत — {e}")
            continue
        try:
            fdate = dt.date.fromisoformat(date_s)
            if abs((fdate - today).days) > 2:
                errs.append(f"{pre} तारीख {date_s} आज ({today}) से मेल नहीं खाती")
        except ValueError:
            errs.append(f"{pre} तारीख गलत")
        if d.get("slug") != slug_from_name:
            errs.append(f"{pre} slug '{d.get('slug')}' फ़ाइल नाम से मेल नहीं खाता ('{slug_from_name}')")
        if d.get("category") != "विशेष":
            errs.append(f"{pre} category 'विशेष' होनी चाहिए")
        tags = d.get("tags") or []
        if "भक्ति" not in tags:
            errs.append(f"{pre} tags में 'भक्ति' नहीं")
        title = d.get("title", "")
        if title.startswith(("विश्लेषण", "भक्ति", "कथा")):
            errs.append(f"{pre} शीर्षक कथा के अपने विषय से शुरू हो, '{title.split()[0]}' से नहीं")
        if re.search(r"भगवद्\s*गीता|श्रीमद्भगवद्गीता", title):
            errs.append(f"{pre} गीता के श्लोकों पर लेख अलग गीता शृंखला में आते हैं")
        fw = first_words(title)
        if fw in old_titles:
            errs.append(f"{pre} शीर्षक के पहले शब्द '{fw}' पुराने लेख {old_titles[fw]} से मिलते हैं")
        if fw in seen_fw:
            errs.append(f"{pre} शीर्षक इसी PR के {seen_fw[fw]} से मिलता है")
        seen_fw[fw] = os.path.basename(p)
        core = re.sub(r"-gpt-bhakti$", "", slug_from_name)
        if core in old_slugs:
            errs.append(f"{pre} यही कथा (slug '{core}') पिछले 60 दिन में आ चुकी है")
        fi = d.get("featured_image", "")
        if not fi:
            errs.append(f"{pre} featured_image नहीं")
        elif f"reports/{fi}" not in imgs:
            errs.append(f"{pre} featured_image '{fi}' इस PR में जोड़ी नहीं गई")
        if d.get("image_search"):
            errs.append(f"{pre} image_search न रखें — line-art cover ही चाहिए")
        out = subprocess.run([sys.executable, "tools/validate.py", p], capture_output=True, text=True)
        for ln in out.stdout.splitlines():
            if ln.startswith("❌"):
                errs.append(f"{pre} validate: {ln[1:].strip()}")
            elif ln.startswith("✅"):
                notes.append(f"{pre} {ln[1:].strip()}")
        nc = d.get("needs_check") or []
        if nc:
            notes.append(f"{pre} needs_check में {len(nc)} बातें — publish के बाद एक नज़र देख लें")

    with open("check-report.md", "w", encoding="utf-8") as f:
        if errs:
            f.write("### ❌ भक्ति PR अपने-आप publish नहीं हुआ\n\nये कमियाँ ठीक करके PR में नया commit करें (जाँच फिर से चलेगी):\n\n")
            f.writelines(f"- {e}\n" for e in errs)
        else:
            f.write("### ✅ भक्ति PR की जाँच पास\n\n")
        if notes:
            f.write("\n**नोट:**\n\n")
            f.writelines(f"- {n}\n" for n in notes)
    print(open("check-report.md", encoding="utf-8").read())
    if errs:
        print("FAIL")
        return 1
    print("PASS " + " ".join(jsons + imgs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

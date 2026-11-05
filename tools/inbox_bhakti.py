#!/usr/bin/env python3
"""inbox/ में डाले गए ChatGPT के भक्ति लेख जाँचकर reports/ में publish के लिए रखना।

GitHub Action `gpt-bhakti-inbox.yml` इसे चलाता है (inbox/ में कुछ भी push होते ही)।
User को बस GitHub पर inbox/ में एक नई फ़ाइल बनाकर ChatGPT का JSON paste करना है
(चाहे ```json वाले निशान समेत)। साथ में उसी नाम की image (.png/.jpg/.webp) भी डाली जा
सकती है; न हो तो auto-cover workflow 10 मिनट में cover बना देता है।

अपने-आप ठीक होने वाली बातें: फ़ाइल नाम और तारीख, slug का "-gpt-bhakti", category "विशेष",
tags में "भक्ति"/"कथा", image_search हटाना, image को 1200×675 cover में बदलना।
सख़्त जाँच (फ़ेल होने पर publish नहीं): validate.py के errors, 5+ https स्रोत, शब्द-सीमा,
शीर्षक के पहले 4 शब्द किसी पुराने लेख से न मिलें, 60 दिन में कथा का दोहराव नहीं, गीता-श्लोक लेख नहीं।

फ़ेल होने पर inbox/<नाम>.errors.md में कारण लिखे जाते हैं और JSON inbox में ही रहता है;
उसे GitHub पर edit करके commit करें, जाँच फिर चलेगी।
"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")


def first_words(title, n=4):
    t = re.sub(r"[^\w\sऀ-ॿ]", " ", title)
    return " ".join(t.split()[:n])


def parse_loose(text):
    text = text.strip().lstrip("﻿")
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("फ़ाइल में JSON ({ … }) नहीं मिला")
    return json.loads(text[a:b + 1])


def make_cover(src, dst):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    W, H = 1200, 675
    canvas = Image.new("RGB", (W, H), (251, 243, 226))  # #fbf3e2 क्रीम
    im.thumbnail((W, H))
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    canvas.save(dst, "PNG", optimize=True)


def word_count(html):
    return len(re.sub(r"<[^>]+>", " ", html).split())


def main():
    today = dt.datetime.now(IST).date().isoformat()
    cutoff = (dt.datetime.now(IST).date() - dt.timedelta(days=60)).isoformat()
    old_titles, old_slugs = {}, set()
    for p in glob.glob("reports/*.json"):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if d.get("title"):
            old_titles[first_words(d["title"])] = p
        m = re.match(r"reports/(\d{4}-\d{2}-\d{2})-(.+)\.json$", p)
        if m and m.group(1) >= cutoff:
            old_slugs.add(re.sub(r"-(gpt-)?bhakti$", "", m.group(2)))

    inbox = sorted(f for f in glob.glob("inbox/*.json"))
    published, failed, log_lines = [], [], []
    for src in inbox:
        stem = os.path.splitext(os.path.basename(src))[0]
        errfile = f"inbox/{stem}.errors.md"
        errs = []
        try:
            d = parse_loose(open(src, encoding="utf-8").read())
        except Exception as e:
            d, errs = None, [f"JSON पढ़ा नहीं जा सका: {e}. ChatGPT से पूरा JSON दोबारा copy करके paste करें।"]

        if d is not None:
            raw_slug = str(d.get("slug") or stem).lower()
            raw_slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", raw_slug)
            core = re.sub(r"[^a-z0-9]+", "-", raw_slug).strip("-")
            core = re.sub(r"-(gpt-)?bhakti$", "", core)
            if len(core) < 6:
                errs.append("slug (English नाम) बहुत छोटा/गायब — जैसे \"kevat-ram-ganga-ayodhya-kanda\"")
            slug = f"{core}-gpt-bhakti"
            final = f"reports/{today}-{slug}.json"
            d["slug"] = slug
            d["category"] = "विशेष"
            tags = [t for t in (d.get("tags") or []) if isinstance(t, str)]
            for t in ("कथा", "भक्ति"):
                if t not in tags:
                    tags.insert(0, t)
            d["tags"] = tags
            d.pop("image_search", None)
            d.setdefault("needs_check", [])
            d.pop("featured_image", None)

            title = d.get("title", "")
            if os.path.exists(final):
                errs.append(f"{final} पहले से मौजूद है — slug बदलें")
            if title.startswith(("विश्लेषण", "भक्ति", "कथा")):
                errs.append("शीर्षक कथा के अपने विषय से शुरू हो (\"भक्ति\", \"कथा\", \"विश्लेषण\" से नहीं)")
            if re.search(r"भगवद्\s*गीता|श्रीमद्भगवद्गीता", title):
                errs.append("गीता के श्लोकों पर लेख अलग गीता शृंखला में आते हैं")
            fw = first_words(title)
            if fw and fw in old_titles:
                errs.append(f"शीर्षक के पहले शब्द \"{fw}\" पुराने लेख {old_titles[fw]} से मिलते हैं — वेबसाइट इसे रोक देगी")
            if core in old_slugs:
                errs.append(f"यही कथा (\"{core}\") पिछले 60 दिन में आ चुकी है — दूसरी कथा लें")

            img = next((f"inbox/{stem}{e}" for e in IMG_EXT if os.path.exists(f"inbox/{stem}{e}")), None)
            cover = f"reports/images/{today}-{slug}-cover.png"
            if not errs:
                json.dump(d, open(final, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                if img:
                    try:
                        make_cover(img, cover)
                        d["featured_image"] = os.path.relpath(cover, "reports")
                        json.dump(d, open(final, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                    except Exception as e:
                        errs.append(f"image नहीं खुली ({e}) — PNG/JPG दोबारा डालें या image हटा दें")
                out = subprocess.run([sys.executable, "tools/validate.py", final], capture_output=True, text=True)
                errs += [ln[1:].strip() for ln in out.stdout.splitlines() if ln.startswith("❌")]
                if errs:
                    os.remove(final)
                    if os.path.exists(cover):
                        os.remove(cover)

        if errs:
            with open(errfile, "w", encoding="utf-8") as f:
                f.write(f"# ❌ {stem}.json publish नहीं हुआ\n\nये कमियाँ ChatGPT से ठीक करवाकर `{src}` को edit करें और commit करें — जाँच फिर चलेगी:\n\n")
                f.writelines(f"- {e}\n" for e in errs)
            failed.append((src, errs))
            continue

        for f in [src, errfile] + ([img] if img else []):
            if f and os.path.exists(f):
                os.remove(f)
        old_titles[fw] = final
        old_slugs.add(core)
        log_lines.append(f"- {today} | भक्ति (ChatGPT): {d['title']} | {final} | {word_count(d['content_html'])}")
        published.append(final)

    if log_lines:
        log = open("log.md", encoding="utf-8").read()
        log += ("" if log.endswith("\n") else "\n") + "\n".join(log_lines) + "\n"
        open("log.md", "w", encoding="utf-8").write(log)

    summary = []
    for p in published:
        summary.append(f"✅ publish के लिए भेजा: {p}")
    for src, errs in failed:
        summary.append(f"❌ {src}:")
        summary += [f"   - {e}" for e in errs]
    print("\n".join(summary) or "inbox में कोई JSON नहीं")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n\n".join(summary) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

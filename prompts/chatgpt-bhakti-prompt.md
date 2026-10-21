# ChatGPT (Codex / Agent) के लिए भक्ति-कथा prompt

यह prompt ChatGPT **Codex** (GitHub repo `phdvijay01-ops/desilalkaar-reports` से जुड़ा) में या ChatGPT **Agent mode** में चलाने के लिए है।
Codex आमतौर पर branch बनाकर Pull Request खोलता है — वेबसाइट केवल `main` branch की `reports/` फ़ाइलें उठाती है, इसलिए PR को review करके **merge** करना ही "publish" है।
Claude वाली routine के साथ चलाएँ तो दोनों का दोहराव रोकने के लिए ChatGPT की फ़ाइलों के slug में `-gpt-bhakti` रखा गया है और हर run से पहले `git pull` + log जाँच ज़रूरी है।

---

## Prompt (नीचे का पूरा हिस्सा copy करें)

You write ONE Hindi devotional article (भक्ति — कथा और प्रसंग) per run for the Hindi news website देसी ललकार (desilalkaar.com). The website picks up new JSON files (and images) from the GitHub repo phdvijay01-ops/desilalkaar-reports, folder reports/, on the main branch and publishes them automatically, so accuracy and respect matter most.

Do NOT write about Bhagavad Gita verses (a separate गीता शृंखला covers them); other Mahabharata episodes are fine.

**Step 1 — repo.** Work in the repo phdvijay01-ops/desilalkaar-reports on the latest main. Read CLAUDE.md (JSON schema, allowed HTML tags, fairness and safety rules — they apply to you too), log.md, and the titles of all reports/*-bhakti.json files. For this task these rules override CLAUDE.md's analysis-specific rules: one article per run; title does NOT start with "विश्लेषण:"; no charts; structure as below; category "विशेष".

**Step 2 — topic.** One कथा or प्रसंग from Indian religious tradition — रामायण, महाभारत, पुराण (भागवत, शिव, विष्णु, स्कंद, देवी भागवत आदि), संतों/भक्तों के जीवन-प्रसंग (मीरा, कबीर, तुलसीदास, सूरदास, नरसी मेहता, रैदास, नामदेव आदि), ज्योतिर्लिंग/शक्तिपीठ कथाएँ, especially those connected to Madhya Pradesh (महाकाल-उज्जैन, ओंकारेश्वर, चित्रकूट, ओरछा, अमरकंटक, मैहर). It must NOT repeat any कथा/प्रसंग already in log.md or reports/*-bhakti.json in the last 60 days. If a major Hindu festival falls within the next 7 days, prefer a कथा linked to it — but verify the festival date from at least two reliable panchang/news sources in this session.

**Step 3 — research.** Browse the web (at least 6–8 searches, Hindi and English). Prefer: shlokam.org, valmikiramayan.net, gitasupersite.iitk.ac.in, wisdomlib.org, sacred-texts.com, vedabase.io, temple trust / MP Tourism sites, Britannica, museum and university pages. Every factual claim (text name, स्कंध/कांड/अध्याय, verse number, names, places) must come from a page you actually opened in this run. Where versions differ between texts or regions, say so plainly. Never invent shlokas, verse numbers, quotes, events or sources. If you cannot find at least 5 reliable https sources, choose another कथा.

**Step 4 — writing.** Simple, warm, respectful Hindi, 1150–1600 words, in your own words (no copying or literal translation; no modern copyrighted bhajans, aartis, songs or translations such as Gita Press — paraphrase only). You may quote at most 2 short ancient Sanskrit shlokas in verified Devanagari, each followed by "— <ग्रंथ> X.Y.Z", each half-line in its own `<p><strong>…</strong></p>` (no `<br>`). No superstition claims, miracle cures, fear-mongering, astrology predictions or promised benefits. Do not disparage any religion, sect or community; stay politically neutral.
Structure with `<h2>` headings and short paragraphs: opening paragraph(s); कथा का स्रोत; कथा in 2–4 `<h2>` sections; प्रमुख पात्र (optional `<table>` with पात्र / भूमिका); कथा का संदेश (`<ul>`); आज के जीवन में अर्थ; मध्य प्रदेश से जुड़ाव (only if real and sourced); निष्कर्ष.
Allowed tags ONLY: p h2 h3 ul ol li strong table tr th td thead tbody. No img, a, br, em, div.

**Step 5 — JSON file.** Path: `reports/YYYY-MM-DD-<english-slug>-gpt-bhakti.json` (today's IST date; make sure the name is unique in reports/). Write it with Python `json.dump(data, f, ensure_ascii=False, indent=2)` — real Hindi characters, no \u escapes. Keys:
- `title` (55–90 chars), starting with this कथा's own subject, e.g. "भक्त प्रह्लाद की कथा: अटूट विश्वास का संदेश". Its first 4–5 words must not match any earlier title (the website's duplicate filter blocks look-alike titles).
- `meta_description` (140–160 chars, starts with the same subject) — this is the "देसी ललकार विवरण"; keep the key name `meta_description`.
- `excerpt`, `content_html`, `category`: "विशेष"
- `tags`: include "भक्ति", "कथा" and 2–4 more
- `slug`: a-z0-9- only = the file name without the date and `.json`, e.g. `prahlad-narasimha-bhagavata-gpt-bhakti` (ends in `-bhakti`)
- `sources`: list of {"name","link"}, at least 5 verified https links you opened
- `image_keywords` (English), `image_alt` (Hindi: describe a cream-coloured line-art cover with the कथा title)
- `needs_check`: list every version difference or anything not fully verified
- `cover_stat`: {"value": short word ≤7 letters like "कथा" or the scripture name, "label": e.g. "श्रीमद्भागवत, दशम स्कंध से"}
- Do NOT add `image_search` — the line-art cover from step 6 must be used.

**Step 6 — line-art cover (same style as Claude's गीता शृंखला covers).** From the repo root (needs Python + Playwright Chromium; if missing: `pip install playwright && python -m playwright install chromium`):
```
python3 tools/bhakti_lineart_cover.py reports/<file>.json "<ग्रंथ/परंपरा, e.g. श्रीमद्भागवत>" "<छोटा हिंदी शीर्षक, max ~28 chars>" "<उप-पंक्ति, e.g. दशम स्कंध · अध्याय 29–33>" <motif>
```
motif = `moon` (चाँदनी/वृंदावन/कृष्ण कथाएँ), `temple` (ज्योतिर्लिंग/मंदिर/शक्तिपीठ), `diya` (संत, व्रत, दीपावली), `river` (नर्मदा, गंगा, घाट, तीर्थ).
This writes `reports/images/<file>-cover.png` (1200×675, cream background #fbf3e2, maroon ink #5b1d0f line art, double border with lotus, text on the right) and sets `featured_image`. Open the PNG and confirm the Hindi renders correctly (no broken matras or boxes).
If you cannot run Python/Playwright (plain ChatGPT chat): generate a 1200×675 image yourself in exactly this style — flat cream background (#fbf3e2), thin maroon (#5b1d0f) single-weight line drawing on the left half (moon/kadamba/flute, temple shikhara, diya or river ghat), double rectangular border with a small lotus at top and bottom centre, the right half left EMPTY (no text at all — image models break Hindi letters), no faces of deities, no colour fills. Save it as `reports/images/<file>-cover.png` and set `"featured_image": "images/<file>-cover.png"` in the JSON.

**Step 7 — validate.** Run `python3 tools/validate.py reports/<file>.json`. The ONLY acceptable error is "title 'विश्लेषण:' से शुरू होना चाहिए" (plus warnings about charts/table/विश्लेषण tag); fix every other error. Word count must be 1100–2100 (website rejects under 1000 words or under 5 https sources).

**Step 8 — log and publish.** Discard changes to tools/__pycache__ if any. Append one line to log.md:
`- YYYY-MM-DD | भक्ति: <कथा का नाम> | reports/<file>.json | <शब्द>`
Commit ONLY the JSON, its cover PNG and log.md with message `भक्ति: <कथा>` and push to main (or, in Codex, open a PR to main titled the same — it is published when merged). Never edit or delete previously pushed files in reports/. Never push a guessed or incomplete article; never put API keys or credentials in the repo.

Finish with a 2-line Hindi summary: कथा, शब्द, स्रोत, file name.

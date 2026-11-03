# ChatGPT से 10 लेख + line-art image — Claude को सौंपने का तरीका

इस तरीके में ChatGPT लेख और image बनाता है, लेकिन GitHub पर push नहीं करता। आप ChatGPT से मिली फ़ाइलें Claude को देते हैं। Claude उन्हें जाँचता है (schema, शब्द, स्रोत खोलकर तथ्य, duplicate शीर्षक, image) और ठीक होने पर `reports/` में push करता है। Push के बाद वेबसाइट का cron उन्हें publish कर देता है।

ChatGPT को एक बार में 10 के बजाय **2–3 लेख प्रति chat** देने को कहें, वरना लंबे लेख अधूरे या कमज़ोर बनते हैं।

---

## Prompt (नीचे का पूरा हिस्सा ChatGPT में copy करें)

You will write Hindi devotional articles (भक्ति — कथा और प्रसंग) for the Hindi news website देसी ललकार (desilalkaar.com), plus one line-art cover image for each. I will hand your files to an editor who checks every source before publishing, so accuracy matters more than speed. Write 2 articles in this chat, one at a time; after each article give me its two files, then continue.

**Topics.** Choose कथाएँ/प्रसंग from रामायण, महाभारत (NOT Bhagavad Gita verses), पुराण (भागवत, शिव, विष्णु, स्कंद, देवी भागवत), संतों/भक्तों के जीवन-प्रसंग (मीरा, कबीर, तुलसीदास, सूरदास, नरसी मेहता, रैदास, नामदेव), ज्योतिर्लिंग/शक्तिपीठ कथाएँ — preferably connected to Madhya Pradesh (महाकाल-उज्जैन, ओंकारेश्वर, चित्रकूट, ओरछा, अमरकंटक, मैहर). Do not repeat these already-used topics: <यहाँ पहले के लेखों के शीर्षक paste करें, या "कोई नहीं">.

**Research.** Browse the web (at least 6 searches per article, Hindi and English). Prefer shlokam.org, valmikiramayan.net, gitasupersite.iitk.ac.in, wisdomlib.org, sacred-texts.com, vedabase.io, temple trust / MP Tourism / government sites, Britannica, university or museum pages. Every name, text, स्कंध/कांड/अध्याय, verse number and place must come from a page you actually opened. Where versions differ, say so. Never invent shlokas, verse numbers, quotes, events or sources. If you cannot find 5 reliable https sources, pick another कथा.

**Writing.** Simple, warm, respectful Hindi, 1,200–1,600 words, in your own words (no copying, no literal translation, no modern copyrighted bhajans/aartis/Gita Press translations). At most 2 short Sanskrit shlokas in verified Devanagari, each followed by "— <ग्रंथ> X.Y.Z". No superstition, miracle-cure claims, astrology predictions, fear or promised benefits. Do not disparage any religion or community; stay politically neutral. Use `<h2>` sections: शुरुआत; कथा का स्रोत; कथा (2–4 sections); प्रमुख पात्र (optional table); कथा का संदेश (`<ul>`); आज के जीवन में अर्थ; मध्य प्रदेश से जुड़ाव (only if real and sourced); निष्कर्ष. Allowed HTML tags ONLY: p h2 h3 ul ol li strong table tr th td thead tbody (no img, a, br, em, div).

**File 1 — JSON** named `<english-slug>-gpt-bhakti.json` (slug: lowercase a-z, 0-9 and hyphens only). Give it as a downloadable .json file (UTF-8, real Hindi letters, no \u escapes). Keys:
- `title` (55–90 characters), starting with this कथा's own subject, e.g. "भक्त प्रह्लाद की कथा: अटूट विश्वास का संदेश". Do NOT start with "भक्ति", "कथा", "विश्लेषण:" or a series name.
- `meta_description` (140–160 characters, starts with the same subject)
- `excerpt` (2 sentences), `content_html`, `category`: "विशेष"
- `tags`: "भक्ति", "कथा" + 2–4 more
- `slug`: same as the file name without `.json`
- `sources`: list of {"name": "...", "link": "https://..."} — at least 5 pages you opened
- `image_keywords` (English list), `image_alt` (Hindi sentence describing the cover)
- `needs_check`: list every version difference or anything you could not fully verify (empty list if none)
- `cover_stat`: {"value": a short word like "कथा" or the scripture name, "label": e.g. "श्रीमद्भागवत, दशम स्कंध से"}
- `featured_image`: "images/<slug>-cover.png"

**File 2 — cover image.** Do NOT make the image in this same message. After the JSON file, write one short line starting with `IMAGE PROMPT:` describing the main scene of this कथा in a few words (main character or deity + place), e.g. "IMAGE PROMPT: भगवान राम और केवट, गंगा तट पर नाव". I will ask for the image separately.

At the end, list the JSON file and the IMAGE PROMPT line of each article and a 1-line summary (कथा, शब्द संख्या, स्रोतों की संख्या).

---

## Image अलग से बनवाएँ (नया message, छोटा prompt)

लेख पूरा होने के बाद उसी chat में छोटा message भेजें। लंबे prompt पर ChatGPT कई बार "content policy" वाला संदेश दे देता है, जबकि छोटा prompt आराम से चलता है। उदाहरण:

```
<IMAGE PROMPT वाली पंक्ति> का रंगीन line art बनाओ, 16:9 landscape (चौड़ी), हल्की क्रीम पृष्ठभूमि, image में कोई अक्षर या text नहीं
```

- Image **चौड़ी (16:9)** हो, चौकोर नहीं। चौकोर बने तो "इसे 16:9 चौड़ा बनाओ" कहकर दोबारा बनवाएँ। फिर भी चौकोर रहे तो वैसे ही दे दें, Claude उसे क्रीम पृष्ठभूमि वाले 1200×675 फ्रेम में बिठा देगा।
- Image में अक्षर न हों, क्योंकि ChatGPT की image में हिंदी अक्षर टूट जाते हैं।
- फिर भी रोक लगे तो सिर्फ़ जगह और वस्तुएँ लिखें, जैसे "गंगा घाट, नाव, दीपक और कमल का रंगीन line art"।
- Image को `<slug>-cover.png` नाम से save करें।

## Claude को कैसे दें

1. हर लेख की `.json` और `-cover.png` ChatGPT से download करें।
2. सारी फ़ाइलें (या उनका एक zip) Claude के chat में attach करें और लिखें: "ये लेख जाँचकर push कर दो"।
3. Claude हर लेख पर यह करेगा:
   - file name में तारीख जोड़ना: `reports/YYYY-MM-DD-<slug>.json`
   - image को 1200×675 में बदलकर `reports/images/` में रखना
   - `tools/validate.py` चलाना
   - स्रोत खोलकर तथ्य जाँचना और पुराने शीर्षकों से टकराव देखना
   - `log.md` में पंक्ति जोड़ना और push करना
4. जो लेख जाँच में कमज़ोर निकले (स्रोत न खुलें, तथ्य न मिलें, शीर्षक टकराए), उसे Claude push नहीं करेगा और कारण बताएगा।

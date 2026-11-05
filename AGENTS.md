# Codex / ChatGPT के लिए निर्देश

यह repo "देसी ललकार" (desilalkaar.com) का है। `reports/` में आई नई JSON फ़ाइलें वेबसाइट अपने-आप publish करती है।

## भक्ति लेख

जब user कहे "आज का भक्ति लेख बनाओ" (या "भक्ति लेख", "भक्ति कथा", "N भक्ति लेख बनाओ"), तो:

1. `prompts/chatgpt-bhakti-prompt.md` पूरा पढ़ो और उसके "Prompt" हिस्से के Step 1–8 हूबहू मानो। CLAUDE.md के तथ्य-जाँच, निष्पक्षता, JSON schema और HTML tags वाले नियम भी तुम पर लागू हैं।
2. फ़ाइल नाम `reports/YYYY-MM-DD-<english-slug>-gpt-bhakti.json` (आज की IST तारीख), cover `reports/images/YYYY-MM-DD-<english-slug>-gpt-bhakti-cover.png`।
3. PR खोलने से पहले चलाओ और हर ❌ ठीक करो:
   - `python3 tools/validate.py reports/<file>.json`
   - `git fetch origin main && python3 tools/check_gpt_bhakti_pr.py origin/main HEAD`
4. एक PR में अधिकतम 3 लेख। PR में सिर्फ़ नई JSON, उनकी cover PNG और log.md हों — tools/, .github/, prompts/ या पुरानी reports कभी न बदलो।
5. PR खुलते ही GitHub Action `gpt-bhakti-autopublish.yml` जाँच करता है और पास होने पर लेख खुद publish कर देता है। फ़ेल होने पर PR पर कारण लिखे जाते हैं — उन्हें उसी branch पर नए commit से ठीक करो।

सबसे ज़रूरी: कोई श्लोक, श्लोक-क्रमांक, कथा-घटना, तारीख या स्रोत गढ़ो मत। जो इस run में खोले गए पेज से सत्यापित न हो, उसे छोड़ दो या `needs_check` में लिखो।

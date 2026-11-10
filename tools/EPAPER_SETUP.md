# ई-पेपर: वेबसाइट पर कैसे दिखेगा

पता: **https://www.desilalkaar.com/epaper/**

## पूरा रास्ता

1. **PDF बनना (अपने-आप, GitHub पर):** `.github/workflows/epaper.yml` रोज़ रात 11:15 बजे (IST) उस दिन की
   `reports/YYYY-MM-DD-*.json` से `tools/make_epaper.py` चलाता है और ये files `epaper/` में push करता है:
   - `epaper/YYYY-MM-DD.pdf` — A3 ई-पेपर (पहला पेज: masthead, मुख्य खबर, बाकी खबरों की झलक; अंदर हर लेख charts के साथ; हर पेज पर logo)
   - `epaper/YYYY-MM-DD.jpg` — पहले पेज की छोटी तस्वीर
   - `epaper/editions.json` — सभी संस्करणों की सूची
2. **वेबसाइट पर आना (cron):** `public_html/autonews/github_epaper.php` हर 30 मिनट `epaper/editions.json` पढ़कर नई PDF/तस्वीर
   `public_html/epaper/files/` में उतारता है।
3. **पाठक का पेज:** `public_html/epaper/index.php` — आज का ई-पेपर, पढ़ें/डाउनलोड बटन और पिछले अंकों की सूची।
   `/epaper/?d=2026-11-10` से किसी दिन का अंक खुलता है। मोबाइल पर पहला पेज दिखता है और बटन से पूरी PDF खुलती है।

`reports/` वाला लेख-import (`github_reports.php`) इससे अलग है और इससे नहीं बदलता।

## एक बार का setup (cPanel)

1. **File Manager** में:
   - इस repo की `tools/github_epaper.php` → `public_html/autonews/github_epaper.php`
   - इस repo की `tools/epaper_index.php` → `public_html/epaper/index.php` (`epaper` folder बनाएँ)
2. **Cron Jobs** में नई line (path वही जो `github_reports.php` के cron में है):
   ```
   15,45 * * * * /usr/local/bin/php /home2/desil840/public_html/autonews/github_epaper.php >/dev/null 2>&1
   ```
3. पहली बार तुरंत चलाने के लिए cPanel **Terminal** में:
   ```
   /usr/local/bin/php /home2/desil840/public_html/autonews/github_epaper.php
   ```
   फिर https://www.desilalkaar.com/epaper/ खोलें। `public_html/epaper/files/` में PDF, jpg, `logo.png` और `editions.json` दिखने चाहिए;
   दिक्कत हो तो `public_html/epaper/files/import.log` देखें।
4. वेबसाइट के menu/header में **"ई-पेपर"** नाम का link जोड़ें: `/epaper/`

## रोज़ का काम

कुछ नहीं। रात 11:15 बजे PDF बनती है, अगले 30 मिनट में वेबसाइट पर आ जाती है।

- किसी दिन का ई-पेपर पहले या दोबारा बनाना हो (जैसे देर से आई रिपोर्ट के बाद): GitHub → **Actions → ई-पेपर → Run workflow** →
  तारीख डालें। उसी दिन की PDF बदल जाती है और cron नया आकार देखकर वेबसाइट पर भी बदल देता है।
- Local: `python3 tools/make_epaper.py 2026-11-10` (Playwright, Pillow और `pdftoppm` चाहिए)।
- वेबसाइट पर पिछले 90 दिन के अंक रहते हैं (`EP_KEEP`); GitHub में सब रहते हैं।

## ध्यान रखें

- ई-पेपर में वही लेख जाते हैं जो `reports/` में पहले से छपे हैं; कोई नया तथ्य नहीं जुड़ता। इसलिए लेखों की तथ्य-जाँच ही ई-पेपर की तथ्य-जाँच है।
- एक PDF लगभग 3–4 MB की होती है।

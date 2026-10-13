# नए लेख Facebook और X पर अपने-आप — setup

Website के header/footer में Facebook, X, YouTube, Instagram के follow links पहले से हैं।
यह setup हर नया छपा लेख (शीर्षक + लिंक) Facebook Page और X पर post करता है।

## 1. Server पर files रखें (public_html/autonews/)
- `tools/social_post.php` → `public_html/autonews/social_post.php`
- `tools/github_reports.php` (नया version) → `public_html/autonews/github_reports.php`
- `tools/social_config.example.php` → copy करके `public_html/autonews/data/social_config.php`

## 2. Facebook keys
1. developers.facebook.com → My Apps → Create App (Business type)। App में "Facebook Login for Business"/Pages use case जोड़ें।
2. Graph API Explorer में अपना App चुनें, permissions `pages_show_list`, `pages_manage_posts`, `pages_read_engagement` दें, User Token बनाएँ।
3. Access Token Debugger में "Extend Access Token" से long-lived token लें, फिर Explorer में `me/accounts` चलाएँ।
   वहाँ "देसी ललकार" Page की `id` और `access_token` मिलेगा (यह Page token expire नहीं होता)।
4. इन्हें `social_config.php` में `facebook_page_id` और `facebook_page_token` में डालें।
   आप App के admin हैं, इसलिए अपने Page पर post के लिए App Review की ज़रूरत आम तौर पर नहीं होती।

## 3. X keys
1. console.x.com में App बनाएँ। User authentication settings में permission **Read and write** करें।
2. "Keys and tokens" से API Key, API Secret, Access Token, Access Token Secret लें
   (permission बदलने के बाद Access Token दोबारा बनाएँ)।
3. Credits खरीदें। link वाली हर post ≈ $0.20 (अक्टूबर 2026 की दर)। card जोड़ने पर $20 free credit मिलता है।

## 4. पहले dry run
`social_config.php` में `dry_run => true` और `facebook_enabled`/`x_enabled` => true रखें। फिर:

    php /home2/desil840/public_html/autonews/social_post.php --queue=795 "परीक्षण"

Auto News log में "Social (dry run): ..." दिखे तो सब ठीक। फिर `dry_run => false` करें
(dry run वाले लेख दोबारा post नहीं होंगे)।

## 5. Cron (बचे/fail हुए post दोबारा, हर 15 मिनट)

    5,20,35,50 * * * * /usr/local/bin/php /home2/desil840/public_html/autonews/social_post.php >/dev/null 2>&1

## बाकी Auto News खबरें भी post करनी हों
अभी GitHub रिपोर्टें अपने-आप कतार में जाती हैं। बाकी खबरों के लिए `lib/` में जहाँ `an_publish_draft()`
लेख छापता है, वहाँ (article id और title मिलने के बाद) ये दो lines जोड़ें:

    require_once dirname(__DIR__) . '/social_post.php';
    sp_queue_article($articleId, $title);

- Log: Auto News log में "Social:" वाली lines। State: `data/social_state.json`।
- हर लेख हर platform पर एक बार; fail हो तो 3 बार तक कोशिश।

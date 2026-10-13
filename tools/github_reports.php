<?php
/**
 * देसी ललकार — GitHub विश्लेषण रिपोर्ट import
 *
 * GitHub repo (phdvijay01-ops/desilalkaar-reports) के reports/ folder से नई .json रिपोर्ट
 * उठाकर Auto News के draft (an_drafts) में डालता है और (AUTO_PUBLISH = true हो तो)
 * उसी an_publish_draft() से articles.json में publish करता है जिससे बाकी खबरें छपती हैं।
 *
 * जगह:  public_html/autonews/github_reports.php
 * Cron: 30 * * * * /usr/local/bin/php /home2/desil840/public_html/autonews/github_reports.php >/dev/null 2>&1
 *
 * - हर file सिर्फ एक बार import होती है (याद: autonews/data/github_reports_state.json)
 * - Log: बाकी Auto News log में ही ("GitHub रिपोर्ट: ..." से शुरू होने वाली lines)
 * - रिपोर्ट के graph (charts) और cover image GitHub से उठाकर public_html/images/auto/YYYY/MM/ में रखता है;
 *   cover = featured image, graph = लेख के अंदर सही हिस्से में।
 */
declare(strict_types=1);

const GH_REPO = 'phdvijay01-ops/desilalkaar-reports';
const GH_BRANCH = 'main';
const GH_DIR = 'reports';
const AUTO_PUBLISH = true;   // false करें तो रिपोर्ट सिर्फ draft बनेगी, admin से publish करनी होगी
const MAX_PER_RUN = 3;       // एक run में ज़्यादा से ज़्यादा इतनी नई रिपोर्ट

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit('forbidden');
}
@set_time_limit(300);

require __DIR__ . '/lib/bootstrap.php';
if (is_file(__DIR__ . '/social_post.php')) {
    require_once __DIR__ . '/social_post.php'; // नए लेख Facebook/X पर
}

if (!an_is_configured()) {
    an_log('GitHub रिपोर्ट: setup पूरा नहीं है, कुछ नहीं किया।');
    exit(1);
}

function ghr_http_get(string $url): string
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_CONNECTTIMEOUT => 15,
        CURLOPT_TIMEOUT => 60,
        CURLOPT_USERAGENT => 'desilalkaar-autonews',
        CURLOPT_HTTPHEADER => ['Accept: application/vnd.github+json'],
    ]);
    $body = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    if ($body === false || $code !== 200) {
        throw new RuntimeException("HTTP $code $err — $url");
    }
    return (string)$body;
}

/** GitHub से एक PNG उठाकर images/auto/YYYY/MM/ में रखता है। Return: site-relative path */
function ghr_fetch_image(string $rel): string
{
    if (!preg_match('~^images/[a-z0-9-]+\.png$~', $rel)) {
        throw new RuntimeException('image path गलत: ' . $rel);
    }
    $sub = 'images/auto/' . date('Y/m');
    $dir = an_site_root() . '/' . $sub;
    if (!is_dir($dir) && !@mkdir($dir, 0755, true)) {
        throw new RuntimeException('image folder नहीं बना: ' . $dir);
    }
    $dest = $dir . '/' . basename($rel);
    if (!is_file($dest)) {
        $bin = ghr_http_get('https://raw.githubusercontent.com/' . GH_REPO . '/' . GH_BRANCH . '/' . GH_DIR . '/' . $rel);
        if (strlen($bin) > 3000000 || substr($bin, 0, 8) !== "\x89PNG\r\n\x1a\n") {
            throw new RuntimeException('image सही PNG नहीं: ' . $rel);
        }
        if (file_put_contents($dest, $bin, LOCK_EX) === false) {
            throw new RuntimeException('image save नहीं हुई: ' . $dest);
        }
    }
    return $sub . '/' . basename($rel);
}

/** graph को लेख में उसके <h2> वाले हिस्से के पहले पैराग्राफ के बाद जोड़ता है */
function ghr_add_charts(string $content, array $charts): string
{
    $groups = [];
    foreach ($charts as $c) {
        $src = an_h('/' . $c['path']);
        $alt = an_h(trim(strip_tags((string)($c['title'] ?? ''))));
        $cap = an_h(trim(strip_tags((string)($c['caption'] ?? ''))) . ' (स्रोत: ' . trim(strip_tags((string)($c['source'] ?? ''))) . ')');
        $fig = '<figure class="an-chart" style="margin:1.2em 0"><img src="' . $src . '" alt="' . $alt . '" width="1200" height="675" loading="lazy" style="width:100%;height:auto;border:1px solid #eee;border-radius:6px"><figcaption style="font-size:.9em;color:#555;margin-top:.4em">' . $cap . '</figcaption></figure>';
        $groups[trim((string)($c['after_h2'] ?? ''))][] = $fig;
    }
    foreach ($groups as $h2 => $figs) {
        $html = "\n" . implode("\n", $figs) . "\n";
        $pos = false;
        if ($h2 !== '') {
            $hp = mb_strpos($content, '<h2>' . $h2 . '</h2>');
            if ($hp !== false) {
                $pp = mb_strpos($content, '</p>', $hp);
                $pos = $pp !== false ? $pp + 4 : $hp + mb_strlen('<h2>' . $h2 . '</h2>');
            }
        }
        if ($pos === false) {
            $np = mb_strpos($content, '<h2>निष्कर्ष</h2>');
            $pos = $np !== false ? $np : mb_strlen($content);
        }
        $content = mb_substr($content, 0, $pos) . $html . mb_substr($content, $pos);
    }
    return $content;
}

function ghr_state_path(): string
{
    return AN_ROOT . '/data/github_reports_state.json';
}

function ghr_load_state(): array
{
    $raw = @file_get_contents(ghr_state_path());
    $d = $raw !== false ? json_decode($raw, true) : null;
    return is_array($d) ? $d : ['imported' => []];
}

function ghr_save_state(array $s): void
{
    $p = ghr_state_path();
    $tmp = $p . '.tmp';
    if (file_put_contents($tmp, json_encode($s, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX) === false || !@rename($tmp, $p)) {
        throw new RuntimeException('state file नहीं लिखी जा सकी: ' . $p);
    }
}

/** रिपोर्ट JSON की बुनियादी जाँच। गलती हो तो कारण लौटाता है, ठीक हो तो '' */
function ghr_check(array $r): string
{
    foreach (['title', 'content_html', 'category', 'excerpt'] as $k) {
        if (trim((string)($r[$k] ?? '')) === '') {
            return "'$k' खाली है";
        }
    }
    if (an_word_count((string)$r['content_html']) < 1000) {
        return 'लेख बहुत छोटा है';
    }
    $src = array_filter((array)($r['sources'] ?? []), fn($s) => is_array($s) && str_starts_with((string)($s['link'] ?? ''), 'https://'));
    if (count($src) < 5) {
        return '5 से कम स्रोत';
    }
    return '';
}

function ghr_insert_draft(array $r, string $file): int
{
    // पहले सारी images उठाएँ — कोई fail हो तो पूरी रिपोर्ट अगले run में दोबारा
    $cover = '';
    if (!empty($r['featured_image'])) {
        $cover = ghr_fetch_image((string)$r['featured_image']);
    }
    $charts = [];
    foreach ((array)($r['charts'] ?? []) as $c) {
        if (is_array($c) && !empty($c['file'])) {
            $c['path'] = ghr_fetch_image((string)$c['file']);
            $charts[] = $c;
        }
    }
    $content = an_sanitize_html((string)$r['content_html']);
    $content = ghr_add_charts($content, $charts); // sanitize के बाद, ताकि img न हटे
    $tags = array_slice(array_values(array_filter(array_map(fn($t) => trim(strip_tags((string)$t)), (array)($r['tags'] ?? [])))), 0, 6);
    $sources = array_values(array_map(
        fn($s) => ['name' => trim(strip_tags((string)($s['name'] ?? ''))), 'link' => (string)($s['link'] ?? '')],
        array_filter((array)($r['sources'] ?? []), 'is_array')
    ));
    $urls = array_values(array_unique(array_filter(array_map(fn($s) => $s['link'], $sources))));
    $needs = array_values(array_filter(array_map(fn($t) => trim(strip_tags((string)$t)), (array)($r['needs_check'] ?? []))));
    $needs[] = 'GitHub रिपोर्ट: ' . GH_DIR . '/' . $file;

    an_db()->prepare(
        'INSERT INTO an_drafts (category, district, title, slug, meta_description, excerpt, content, tags, image, image_alt, image_credit, sources, source_text, source_title, source_urls, needs_check, word_count, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())'
    )->execute([
        an_canonical_category((string)$r['category']),
        null,
        mb_substr(trim(strip_tags((string)$r['title'])), 0, 300),
        an_slugify((string)($r['slug'] ?? '')),
        mb_substr(trim(strip_tags((string)($r['meta_description'] ?? ''))), 0, 400),
        trim(strip_tags((string)$r['excerpt'])),
        $content,
        mb_substr(implode(', ', $tags), 0, 500),
        $cover,
        mb_substr(trim(strip_tags((string)($r['image_alt'] ?? ''))), 0, 300),
        $cover !== '' ? 'देसी ललकार ग्राफ़िक' : '',
        json_encode($sources, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        '',
        mb_substr('GitHub: ' . $file, 0, 500),
        json_encode($urls, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        json_encode(array_values(array_unique($needs)), JSON_UNESCAPED_UNICODE),
        an_word_count($content),
    ]);
    return (int)an_db()->lastInsertId();
}

// ---- एक साथ दो run न चलें ----
$lock = fopen(AN_ROOT . '/data/github_reports.lock', 'c');
if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) {
    exit(0);
}

try {
    an_ensure_schema();
    $state = ghr_load_state();
    $list = json_decode(ghr_http_get('https://api.github.com/repos/' . GH_REPO . '/contents/' . GH_DIR . '?ref=' . GH_BRANCH), true);
    if (!is_array($list)) {
        throw new RuntimeException('GitHub file list समझ नहीं आई');
    }
    $files = [];
    foreach ($list as $f) {
        $name = (string)($f['name'] ?? '');
        if (($f['type'] ?? '') === 'file' && preg_match('/^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.json$/', $name) && !isset($state['imported'][$name])) {
            $files[$name] = (string)($f['download_url'] ?? '');
        }
    }
    ksort($files); // पुरानी तारीख पहले
    $done = 0;
    foreach ($files as $name => $url) {
        if ($done >= MAX_PER_RUN) {
            break;
        }
        $done++;
        $articleId = 0;
        try {
            if (!str_starts_with($url, 'https://raw.githubusercontent.com/')) {
                throw new RuntimeException('download link अजीब है');
            }
            $raw = ghr_http_get($url);
            if (strlen($raw) > 2000000) {
                throw new RuntimeException('file बहुत बड़ी है');
            }
            $r = json_decode($raw, true);
            if (!is_array($r)) {
                throw new RuntimeException('JSON गलत है');
            }
            $why = ghr_check($r);
            if ($why !== '') {
                $state['imported'][$name] = ['status' => 'skipped', 'reason' => $why, 'at' => date('c')];
                ghr_save_state($state);
                an_log("GitHub रिपोर्ट: $name छोड़ी — $why");
                continue;
            }
            $draftId = ghr_insert_draft($r, $name);
            $state['imported'][$name] = ['status' => 'draft', 'draft_id' => $draftId, 'at' => date('c')];
            ghr_save_state($state); // draft बनते ही याद रखें, ताकि दोबारा न बने
            an_log("GitHub रिपोर्ट: $name → draft #$draftId");
            if (AUTO_PUBLISH) {
                try {
                    $articleId = an_publish_draft($draftId);
                    $state['imported'][$name]['status'] = 'published';
                    $state['imported'][$name]['article_id'] = $articleId;
                    ghr_save_state($state);
                } catch (Throwable $e) {
                    an_log("GitHub रिपोर्ट: draft #$draftId publish नहीं हुआ (admin से देखें) — " . $e->getMessage());
                }
                if (!empty($articleId) && function_exists('sp_queue_article')) {
                    try {
                        sp_queue_article((int)$articleId, (string)$r['title']);
                    } catch (Throwable $e) {
                        an_log("Social: लेख #$articleId कतार में नहीं गया — " . $e->getMessage());
                    }
                }
            }
        } catch (Throwable $e) {
            // इस file को state में नहीं डाला — अगले run में फिर कोशिश होगी
            an_log("GitHub रिपोर्ट: $name में दिक्कत — " . $e->getMessage());
        }
    }
    if ($done === 0) {
        an_log('GitHub रिपोर्ट: कोई नई रिपोर्ट नहीं।');
    }
    if (function_exists('sp_process_queue')) {
        try {
            sp_process_queue();
        } catch (Throwable $e) {
            an_log('Social error: ' . $e->getMessage());
        }
    }
} catch (Throwable $e) {
    an_log('GitHub रिपोर्ट error: ' . $e->getMessage());
    exit(1);
} finally {
    flock($lock, LOCK_UN);
    fclose($lock);
}

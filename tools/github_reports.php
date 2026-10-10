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
    $content = an_sanitize_html((string)$r['content_html']);
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
        '',
        mb_substr(trim(strip_tags((string)($r['image_alt'] ?? ''))), 0, 300),
        '',
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
            }
        } catch (Throwable $e) {
            // इस file को state में नहीं डाला — अगले run में फिर कोशिश होगी
            an_log("GitHub रिपोर्ट: $name में दिक्कत — " . $e->getMessage());
        }
    }
    if ($done === 0) {
        an_log('GitHub रिपोर्ट: कोई नई रिपोर्ट नहीं।');
    }
} catch (Throwable $e) {
    an_log('GitHub रिपोर्ट error: ' . $e->getMessage());
    exit(1);
} finally {
    flock($lock, LOCK_UN);
    fclose($lock);
}

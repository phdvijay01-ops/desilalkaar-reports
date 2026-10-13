<?php
/**
 * देसी ललकार — नए लेख Facebook Page और X (Twitter) पर अपने-आप post करना
 *
 * जगह:  public_html/autonews/social_post.php   (github_reports.php के साथ)
 * Config: public_html/autonews/data/social_config.php  (keys यहाँ, GitHub में कभी नहीं)
 *         नमूना: social_config.example.php
 * Cron (हर 15 मिनट, बचे/fail हुए post दोबारा):
 *   5,20,35,50 * * * * /usr/local/bin/php /home2/desil840/public_html/autonews/social_post.php >/dev/null 2>&1
 *
 * इस्तेमाल (किसी भी publish code से, लेख छपने के बाद एक line):
 *   require_once __DIR__ . '/social_post.php';
 *   sp_queue_article($articleId, $title);
 *
 * - हर लेख हर platform पर सिर्फ एक बार जाता है (याद: data/social_state.json)
 * - fail हो तो अगले run में दोबारा, ज़्यादा से ज़्यादा 3 बार
 * - Log: Auto News log में ("Social: ..." से शुरू होने वाली lines)
 */
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit('forbidden');
}

if (!defined('AN_ROOT')) {
    require __DIR__ . '/lib/bootstrap.php';
}

const SP_MAX_TRIES = 3;
const SP_MAX_PER_RUN = 5;

function sp_config(): array
{
    static $cfg = null;
    if ($cfg === null) {
        $p = AN_ROOT . '/data/social_config.php';
        $c = is_file($p) ? include $p : [];
        $cfg = (is_array($c) ? $c : []) + [
            'site_url' => 'https://www.desilalkaar.com',
            'facebook_enabled' => false,
            'facebook_page_id' => '',
            'facebook_page_token' => '',
            'facebook_api_version' => 'v26.0',
            'x_enabled' => false,
            'x_api_key' => '',
            'x_api_secret' => '',
            'x_access_token' => '',
            'x_access_secret' => '',
            'dry_run' => false,
        ];
    }
    return $cfg;
}

function sp_state_path(): string
{
    return AN_ROOT . '/data/social_state.json';
}

function sp_load_state(): array
{
    $raw = @file_get_contents(sp_state_path());
    $d = $raw !== false ? json_decode($raw, true) : null;
    return is_array($d) ? $d + ['queue' => []] : ['queue' => []];
}

function sp_save_state(array $s): void
{
    $p = sp_state_path();
    $tmp = $p . '.tmp';
    if (file_put_contents($tmp, json_encode($s, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX) === false || !@rename($tmp, $p)) {
        throw new RuntimeException('social state file नहीं लिखी जा सकी: ' . $p);
    }
}

/** नया छपा लेख कतार में डालें। post अगले run (या sp_process_queue()) में होगा। */
function sp_queue_article(int $articleId, string $title): void
{
    if ($articleId <= 0) {
        return;
    }
    // भेजने वाला run चल रहा हो तो उसके खत्म होने तक रुकें, ताकि state न बिगड़े
    $lock = fopen(AN_ROOT . '/data/social_post.lock', 'c');
    if (!$lock || !flock($lock, LOCK_EX)) {
        throw new RuntimeException('social lock नहीं मिला');
    }
    try {
        $s = sp_load_state();
        $key = (string)$articleId;
        if (!isset($s['queue'][$key])) {
            $s['queue'][$key] = [
                'title' => mb_substr(trim(strip_tags($title)), 0, 300),
                'queued_at' => date('c'),
                'facebook' => ['status' => 'pending', 'tries' => 0],
                'x' => ['status' => 'pending', 'tries' => 0],
            ];
            sp_save_state($s);
        }
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

function sp_article_url(int $id): string
{
    return rtrim((string)sp_config()['site_url'], '/') . '/article.php?id=' . $id;
}

function sp_http(string $method, string $url, array $headers, ?string $body): array
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_CONNECTTIMEOUT => 15,
        CURLOPT_TIMEOUT => 45,
        CURLOPT_USERAGENT => 'desilalkaar-autonews',
        CURLOPT_HTTPHEADER => $headers,
    ]);
    if ($body !== null) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
    }
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    if ($resp === false) {
        throw new RuntimeException("network: $err");
    }
    return [$code, (string)$resp];
}

/** Facebook Page पर लिंक post। Return: post id */
function sp_post_facebook(string $title, string $url): string
{
    $c = sp_config();
    if ($c['facebook_page_id'] === '' || $c['facebook_page_token'] === '') {
        throw new RuntimeException('facebook_page_id / facebook_page_token config में नहीं');
    }
    $endpoint = 'https://graph.facebook.com/' . rawurlencode((string)$c['facebook_api_version']) . '/' . rawurlencode((string)$c['facebook_page_id']) . '/feed';
    [$code, $resp] = sp_http('POST', $endpoint, ['Content-Type: application/x-www-form-urlencoded'], http_build_query([
        'message' => $title,
        'link' => $url,
        'access_token' => $c['facebook_page_token'],
    ]));
    $d = json_decode($resp, true);
    if ($code !== 200 || empty($d['id'])) {
        throw new RuntimeException("Facebook HTTP $code: " . mb_substr((string)($d['error']['message'] ?? $resp), 0, 300));
    }
    return (string)$d['id'];
}

function sp_oauth_header(string $method, string $url, array $c, ?string $nonce = null, ?int $ts = null): string
{
    $enc = fn(string $v) => rawurlencode($v);
    $oauth = [
        'oauth_consumer_key' => (string)$c['x_api_key'],
        'oauth_nonce' => $nonce ?? bin2hex(random_bytes(16)),
        'oauth_signature_method' => 'HMAC-SHA1',
        'oauth_timestamp' => (string)($ts ?? time()),
        'oauth_token' => (string)$c['x_access_token'],
        'oauth_version' => '1.0',
    ];
    // JSON body signature में शामिल नहीं होती
    $params = $oauth;
    ksort($params);
    $pairs = [];
    foreach ($params as $k => $v) {
        $pairs[] = $enc($k) . '=' . $enc($v);
    }
    $base = strtoupper($method) . '&' . $enc($url) . '&' . $enc(implode('&', $pairs));
    $key = $enc((string)$c['x_api_secret']) . '&' . $enc((string)$c['x_access_secret']);
    $oauth['oauth_signature'] = base64_encode(hash_hmac('sha1', $base, $key, true));
    $h = [];
    foreach ($oauth as $k => $v) {
        $h[] = $enc($k) . '="' . $enc($v) . '"';
    }
    return 'Authorization: OAuth ' . implode(', ', $h);
}

/** X पर post (title + link)। Return: post id */
function sp_post_x(string $title, string $url): string
{
    $c = sp_config();
    foreach (['x_api_key', 'x_api_secret', 'x_access_token', 'x_access_secret'] as $k) {
        if ((string)$c[$k] === '') {
            throw new RuntimeException("$k config में नहीं");
        }
    }
    // X में link = 23 अक्षर; हिंदी (देवनागरी) अक्षर 1 गिने जाते हैं। 280 की सीमा में सुरक्षित रहें।
    if (mb_strlen($title) > 240) {
        $title = mb_substr($title, 0, 239) . '…';
    }
    $endpoint = 'https://api.x.com/2/tweets';
    [$code, $resp] = sp_http('POST', $endpoint, [
        sp_oauth_header('POST', $endpoint, $c),
        'Content-Type: application/json',
    ], json_encode(['text' => $title . "\n\n" . $url], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    $d = json_decode($resp, true);
    if ($code !== 201 || empty($d['data']['id'])) {
        $msg = $d['detail'] ?? ($d['title'] ?? $resp);
        throw new RuntimeException("X HTTP $code: " . mb_substr((string)$msg, 0, 300));
    }
    return (string)$d['data']['id'];
}

/** कतार के बचे post भेजें */
function sp_process_queue(): void
{
    $c = sp_config();
    $platforms = [];
    if ($c['facebook_enabled']) {
        $platforms['facebook'] = 'sp_post_facebook';
    }
    if ($c['x_enabled']) {
        $platforms['x'] = 'sp_post_x';
    }
    if (!$platforms) {
        return;
    }
    // एक साथ दो run (cron + github_reports) न चलें, वरना post दोहरा सकता है
    $lock = fopen(AN_ROOT . '/data/social_post.lock', 'c');
    if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) {
        return;
    }
    try {
        sp_send_pending($platforms, $c);
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

function sp_send_pending(array $platforms, array $c): void
{
    $s = sp_load_state();
    $sent = 0;
    ksort($s['queue'], SORT_NUMERIC);
    foreach ($s['queue'] as $id => &$item) {
        foreach ($platforms as $p => $fn) {
            $st = &$item[$p];
            if (($st['status'] ?? '') !== 'pending' || (int)($st['tries'] ?? 0) >= SP_MAX_TRIES) {
                continue;
            }
            if ($sent >= SP_MAX_PER_RUN) {
                break 2;
            }
            $url = sp_article_url((int)$id);
            if ($c['dry_run']) {
                an_log("Social (dry run): $p ← लेख #$id {$item['title']} $url");
                $st['status'] = 'dry_run';
                continue;
            }
            $st['tries'] = (int)($st['tries'] ?? 0) + 1;
            try {
                $st['post_id'] = $fn((string)$item['title'], $url);
                $st['status'] = 'done';
                $st['at'] = date('c');
                an_log("Social: लेख #$id → $p ({$st['post_id']})");
            } catch (Throwable $e) {
                $st['error'] = $e->getMessage();
                if ($st['tries'] >= SP_MAX_TRIES) {
                    $st['status'] = 'failed';
                }
                an_log("Social: लेख #$id $p पर नहीं गया (कोशिश {$st['tries']}) — " . $e->getMessage());
            }
            $sent++;
            unset($st);
            sp_save_state($s); // हर post के बाद याद रखें, ताकि दोबारा न जाए
        }
    }
    unset($item);
    sp_save_state($s);
}

// सीधे चलाने पर (cron): कतार process करें
if (realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    try {
        // टेस्ट: php social_post.php --queue=795 "शीर्षक"
        foreach ($argv as $i => $a) {
            if (str_starts_with($a, '--queue=')) {
                sp_queue_article((int)substr($a, 8), (string)($argv[$i + 1] ?? ''));
            }
        }
        sp_process_queue();
    } catch (Throwable $e) {
        an_log('Social error: ' . $e->getMessage());
        exit(1);
    }
}

<?php
/**
 * देसी ललकार — ई-पेपर import (GitHub → वेबसाइट)
 *
 * GitHub repo के epaper/editions.json को पढ़कर नए संस्करणों की PDF और पहले पेज की तस्वीर
 * public_html/epaper/files/ में रखता है। ई-पेपर पेज (public_html/epaper/index.php) इसी folder को पढ़ता है।
 * यह लेखों (reports/) को नहीं छूता और किसी database की ज़रूरत नहीं।
 *
 * जगह:  public_html/autonews/github_epaper.php
 * Cron (हर 30 मिनट): 15,45 * * * * /usr/local/bin/php /home2/desil840/public_html/autonews/github_epaper.php >/dev/null 2>&1
 * पूरा तरीका: tools/EPAPER_SETUP.md
 */
declare(strict_types=1);

const EP_REPO = 'phdvijay01-ops/desilalkaar-reports';
const EP_BRANCH = 'main';
const EP_KEEP = 90;              // वेबसाइट पर ज़्यादा से ज़्यादा इतने दिन के संस्करण
const EP_MAX_PDF = 25000000;     // 25 MB

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit('forbidden');
}
@set_time_limit(300);

$siteRoot = dirname(__DIR__);                 // public_html
$dir = $siteRoot . '/epaper/files';
$logFile = $dir . '/import.log';

function ep_log(string $msg): void
{
    global $logFile;
    @file_put_contents($logFile, date('c') . ' ' . $msg . "\n", FILE_APPEND | LOCK_EX);
}

function ep_get(string $path): string
{
    $url = 'https://raw.githubusercontent.com/' . EP_REPO . '/' . EP_BRANCH . '/' . $path;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_CONNECTTIMEOUT => 15,
        CURLOPT_TIMEOUT => 120,
        CURLOPT_USERAGENT => 'desilalkaar-epaper',
    ]);
    $body = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($body === false || $code !== 200) {
        throw new RuntimeException("HTTP $code — $path");
    }
    return (string)$body;
}

function ep_save(string $dest, string $bin): void
{
    $tmp = $dest . '.tmp';
    if (file_put_contents($tmp, $bin, LOCK_EX) === false || !@rename($tmp, $dest)) {
        throw new RuntimeException('file save नहीं हुई: ' . $dest);
    }
}

if (!is_dir($dir) && !@mkdir($dir, 0755, true)) {
    exit(1);
}
$lock = fopen($dir . '/.lock', 'c');
if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) {
    exit(0);
}

try {
    $remote = json_decode(ep_get('epaper/editions.json'), true);
    if (!is_array($remote) || !isset($remote['editions']) || !is_array($remote['editions'])) {
        throw new RuntimeException('editions.json समझ नहीं आई');
    }
    // logo एक बार
    if (!is_file($dir . '/logo.png')) {
        $logo = ep_get('tools/brand/logo.png');
        if (substr($logo, 0, 8) === "\x89PNG\r\n\x1a\n") {
            ep_save($dir . '/logo.png', $logo);
        }
    }
    $local = [];
    $keep = [];
    foreach (array_slice($remote['editions'], 0, EP_KEEP) as $ed) {
        $keep[(string)($ed['date'] ?? '')] = true;
    }
    foreach (array_slice($remote['editions'], 0, EP_KEEP) as $ed) {
        $d = (string)($ed['date'] ?? '');
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $d)) {
            continue;
        }
        try {
            $pdf = $dir . '/' . $d . '.pdf';
            $want = (int)($ed['size_kb'] ?? 0);
            // नया संस्करण, या उसी दिन दोबारा बना (आकार बदला) तो फिर से उतारें
            if (!is_file($pdf) || ($want > 0 && intdiv((int)filesize($pdf), 1024) !== $want)) {
                $bin = ep_get('epaper/' . $d . '.pdf');
                if (strlen($bin) > EP_MAX_PDF || substr($bin, 0, 5) !== '%PDF-') {
                    throw new RuntimeException('PDF सही नहीं');
                }
                ep_save($pdf, $bin);
                @unlink($dir . '/' . $d . '.jpg');
                ep_log("ई-पेपर $d उतारा (" . intdiv(strlen($bin), 1024) . ' KB)');
            }
            $thumb = '';
            if (!empty($ed['thumb'])) {
                $jpg = $dir . '/' . $d . '.jpg';
                if (!is_file($jpg)) {
                    $bin = ep_get('epaper/' . $d . '.jpg');
                    if (substr($bin, 0, 3) === "\xFF\xD8\xFF" && strlen($bin) < 3000000) {
                        ep_save($jpg, $bin);
                    }
                }
                $thumb = is_file($jpg) ? $d . '.jpg' : '';
            }
            $local[] = [
                'date' => $d,
                'pdf' => $d . '.pdf',
                'thumb' => $thumb,
                'pages' => (int)($ed['pages'] ?? 0),
                'size_kb' => intdiv((int)filesize($pdf), 1024),
                'lead' => mb_substr(strip_tags((string)($ed['lead'] ?? '')), 0, 300),
                'headlines' => array_slice(array_map(fn($h) => mb_substr(strip_tags((string)$h), 0, 300), (array)($ed['headlines'] ?? [])), 0, 20),
            ];
        } catch (Throwable $e) {
            ep_log("ई-पेपर $d में दिक्कत — " . $e->getMessage());
        }
    }
    if ($local) {
        ep_save($dir . '/editions.json', json_encode(['editions' => $local], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }
    // GitHub सूची के आखिरी EP_KEEP संस्करणों से पुराने हटाएँ (किसी एक की दिक्कत से बाकी नहीं हटते)
    foreach (glob($dir . '/????-??-??.{pdf,jpg}', GLOB_BRACE) ?: [] as $f) {
        if ($keep && !isset($keep[substr(basename($f), 0, 10)])) {
            @unlink($f);
        }
    }
} catch (Throwable $e) {
    ep_log('ई-पेपर error: ' . $e->getMessage());
    exit(1);
} finally {
    flock($lock, LOCK_UN);
    fclose($lock);
}

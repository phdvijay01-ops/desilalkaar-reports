<?php
/**
 * देसी ललकार — ई-पेपर पेज
 *
 * जगह: public_html/epaper/index.php  →  https://www.desilalkaar.com/epaper/
 *   /epaper/              सबसे नया संस्करण और पुराने संस्करणों की सूची
 *   /epaper/?d=2026-11-10 उस दिन का ई-पेपर (पढ़ें / डाउनलोड करें)
 * डेटा: public_html/epaper/files/ (tools/github_epaper.php cron भरता है)
 */
declare(strict_types=1);

$files = __DIR__ . '/files';
$data = json_decode((string)@file_get_contents($files . '/editions.json'), true);
$eds = is_array($data['editions'] ?? null) ? $data['editions'] : [];

function h(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

function hdate(string $d): string
{
    $m = ['जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर'];
    $w = ['रविवार', 'सोमवार', 'मंगलवार', 'बुधवार', 'गुरुवार', 'शुक्रवार', 'शनिवार'];
    $t = strtotime($d . ' 12:00:00');
    return $w[(int)date('w', $t)] . ', ' . (int)date('j', $t) . ' ' . $m[(int)date('n', $t) - 1] . ' ' . date('Y', $t);
}

$sel = null;
$idx = -1;
$d = (string)($_GET['d'] ?? '');
if ($d !== '' && preg_match('/^\d{4}-\d{2}-\d{2}$/', $d)) {
    foreach ($eds as $i => $e) {
        if ($e['date'] === $d) {
            $sel = $e;
            $idx = $i;
        }
    }
    if (!$sel) {
        http_response_code(404);
    }
}
$latest = $eds[0] ?? null;
$title = $sel ? 'ई-पेपर: ' . hdate($sel['date']) . ' | देसी ललकार' : 'ई-पेपर | देसी ललकार';
$desc = $sel ? (string)$sel['lead'] : 'देसी ललकार का रोज़ का ई-पेपर: शोध-आधारित विश्लेषण, आँकड़े और मध्य प्रदेश की खबरें, PDF में पढ़ें और डाउनलोड करें।';
$logo = is_file($files . '/logo.png') ? 'files/logo.png' : '';
?><!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= h($title) ?></title>
<meta name="description" content="<?= h($desc) ?>">
<link rel="canonical" href="https://www.desilalkaar.com/epaper/<?= $sel ? '?d=' . h($sel['date']) : '' ?>">
<?php if ($sel && $sel['thumb']): ?><meta property="og:image" content="https://www.desilalkaar.com/epaper/files/<?= h($sel['thumb']) ?>"><?php endif; ?>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Mukta:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root{--red:#b8232a;--maroon:#5c0f12;--cream:#fbf7f2;--ink:#2a1414;--muted:#6f5f5a;--line:#ead9d2}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);font-family:Mukta,'Noto Sans Devanagari',sans-serif;line-height:1.5}
a{color:inherit}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
header{background:#fff;border-bottom:3px solid var(--maroon)}
header .wrap{display:flex;align-items:center;gap:14px;padding-top:10px;padding-bottom:10px}
header img{height:58px}
.brand{font-weight:800;font-size:30px;color:var(--maroon);line-height:1;text-decoration:none}
.brand small{display:block;font-size:15px;color:var(--red);font-weight:600;margin-top:4px}
header nav{margin-left:auto;display:flex;gap:16px;font-weight:600}
header nav a{text-decoration:none;color:var(--maroon)}
.tri{height:5px;background:linear-gradient(90deg,#ff9933 0 33%,#fff 33% 66%,#138808 66%)}
h1{color:var(--maroon);font-size:30px;margin:22px 0 4px}
.sub{color:var(--muted);margin:0 0 18px}
.btn{display:inline-block;background:var(--red);color:#fff;text-decoration:none;font-weight:700;padding:9px 18px;border-radius:6px;margin:4px 8px 4px 0}
.btn.alt{background:#fff;color:var(--maroon);border:1.5px solid var(--maroon)}
.lead{display:grid;grid-template-columns:minmax(0,340px) 1fr;gap:26px;background:#fff;border:1px solid var(--line);border-left:6px solid var(--red);border-radius:10px;padding:20px;margin-bottom:28px}
.lead img,.card img{width:100%;border:1px solid var(--line);border-radius:6px;display:block}
.kick{display:inline-block;background:var(--red);color:#fff;font-weight:800;font-size:14px;padding:2px 10px;border-radius:4px}
.lead h2{color:var(--maroon);margin:8px 0;font-size:24px;line-height:1.3}
.lead ul{padding-left:20px;margin:8px 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px;margin-bottom:40px}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px;text-decoration:none}
.card b{display:block;color:var(--maroon);margin-top:8px}
.card span{font-size:14px;color:var(--muted)}
.viewer{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:14px 0 20px}
.viewer iframe{width:100%;height:88vh;border:0;display:block}
.mob{display:none}
.nav2{display:flex;justify-content:space-between;margin:10px 0 40px;font-weight:700}
footer{background:var(--maroon);color:#fff;padding:14px 0;font-size:14px}
footer b{color:#ffcf3f}
@media (max-width:760px){
 .lead{grid-template-columns:1fr}
 header nav{display:none}
 .brand{font-size:24px}
 .viewer iframe{display:none}
 .mob{display:block;padding:14px}
 h1{font-size:24px}
}
</style>
</head>
<body>
<header><div class="wrap">
<?php if ($logo): ?><a href="/"><img src="<?= h($logo) ?>" alt="देसी ललकार"></a><?php endif; ?>
<a class="brand" href="/epaper/">ई-पेपर<small>देसी ललकार · शोध-आधारित विश्लेषण</small></a>
<nav><a href="/">होम</a><a href="/epaper/">ई-पेपर</a></nav>
</div></header>
<div class="tri"></div>
<main class="wrap">
<?php if (!$eds): ?>
  <h1>ई-पेपर</h1><p class="sub">पहला संस्करण जल्द यहाँ उपलब्ध होगा।</p>
<?php elseif ($d !== '' && !$sel): ?>
  <h1>यह संस्करण उपलब्ध नहीं है</h1>
  <p class="sub"><a class="btn" href="/epaper/">आज का ई-पेपर देखें</a></p>
<?php elseif ($sel): $pdf = 'files/' . $sel['pdf']; ?>
  <h1>ई-पेपर: <?= h(hdate($sel['date'])) ?></h1>
  <p class="sub"><?= (int)$sel['pages'] ?> पेज · <?= count($sel['headlines']) ?> लेख · <?= number_format($sel['size_kb'] / 1024, 1) ?> MB</p>
  <a class="btn" href="<?= h($pdf) ?>" target="_blank" rel="noopener">पूरा ई-पेपर खोलें</a>
  <a class="btn alt" href="<?= h($pdf) ?>" download="desilalkaar-epaper-<?= h($sel['date']) ?>.pdf">PDF डाउनलोड करें</a>
  <div class="viewer">
    <iframe src="<?= h($pdf) ?>#view=FitH" title="देसी ललकार ई-पेपर <?= h($sel['date']) ?>"></iframe>
    <div class="mob">
      <?php if ($sel['thumb']): ?><a href="<?= h($pdf) ?>" target="_blank" rel="noopener"><img src="files/<?= h($sel['thumb']) ?>" alt="पहला पेज" style="width:100%"></a><?php endif; ?>
      <p>मोबाइल पर ई-पेपर पढ़ने के लिए ऊपर "पूरा ई-पेपर खोलें" दबाएँ।</p>
    </div>
  </div>
  <h2 style="color:var(--maroon)">इस अंक में</h2>
  <ul><?php foreach ($sel['headlines'] as $hl): ?><li><?= h($hl) ?></li><?php endforeach; ?></ul>
  <div class="nav2">
    <span><?php if (isset($eds[$idx + 1])): ?><a href="?d=<?= h($eds[$idx + 1]['date']) ?>">← पिछला अंक</a><?php endif; ?></span>
    <span><?php if ($idx > 0): ?><a href="?d=<?= h($eds[$idx - 1]['date']) ?>">अगला अंक →</a><?php endif; ?></span>
  </div>
<?php else: ?>
  <h1>आज का ई-पेपर</h1>
  <p class="sub">रोज़ के शोध-आधारित विश्लेषण अख़बार के रूप में, पढ़ें या PDF डाउनलोड करें।</p>
  <section class="lead">
    <a href="?d=<?= h($latest['date']) ?>"><?php if ($latest['thumb']): ?><img src="files/<?= h($latest['thumb']) ?>" alt="ई-पेपर <?= h($latest['date']) ?> का पहला पेज"><?php endif; ?></a>
    <div>
      <span class="kick"><?= h(hdate($latest['date'])) ?></span>
      <h2><?= h($latest['lead']) ?></h2>
      <ul><?php foreach (array_slice($latest['headlines'], 1) as $hl): ?><li><?= h($hl) ?></li><?php endforeach; ?></ul>
      <a class="btn" href="?d=<?= h($latest['date']) ?>">ई-पेपर पढ़ें</a>
      <a class="btn alt" href="files/<?= h($latest['pdf']) ?>" download="desilalkaar-epaper-<?= h($latest['date']) ?>.pdf">PDF डाउनलोड</a>
    </div>
  </section>
  <?php if (count($eds) > 1): ?>
  <h2 style="color:var(--maroon)">पिछले अंक</h2>
  <div class="grid">
    <?php foreach (array_slice($eds, 1) as $e): ?>
    <a class="card" href="?d=<?= h($e['date']) ?>">
      <?php if ($e['thumb']): ?><img src="files/<?= h($e['thumb']) ?>" alt="" loading="lazy"><?php endif; ?>
      <b><?= h(hdate($e['date'])) ?></b><span><?= count($e['headlines']) ?> लेख · <?= (int)$e['pages'] ?> पेज</span>
    </a>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>
<?php endif; ?>
</main>
<footer><div class="wrap">© देसी ललकार · <b>desilalkaar.com</b></div></footer>
</body>
</html>

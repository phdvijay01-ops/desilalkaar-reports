<?php
/**
 * नमूना config — इसे server पर public_html/autonews/data/social_config.php नाम से copy करें
 * और असली keys वहीं भरें। असली keys वाली file GitHub में कभी न डालें।
 */
return [
    'site_url' => 'https://www.desilalkaar.com',

    // पहली बार true रखें: कुछ post नहीं होगा, सिर्फ log में दिखेगा क्या जाता
    'dry_run' => true,

    // Facebook Page (developers.facebook.com → App → pages_manage_posts वाला Page Access Token)
    'facebook_enabled' => false,
    'facebook_page_id' => '',
    'facebook_page_token' => '',
    'facebook_api_version' => 'v26.0',

    // X (console.x.com → App → Read and write → 4 keys)
    // ध्यान: link वाली हर post का X शुल्क लेता है (अक्टूबर 2026: $0.20 प्रति post)
    'x_enabled' => false,
    'x_api_key' => '',
    'x_api_secret' => '',
    'x_access_token' => '',
    'x_access_secret' => '',
];

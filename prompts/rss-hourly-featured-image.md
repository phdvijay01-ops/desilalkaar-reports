# Hourly RSS portal content and featured image instructions

Goal: prepare one RSS-related Hindi news/feature topic per hourly run for DesiLalkaar.com, with a real featured image workflow.

## Topic and writing rules
- Write in Hindi (Devanagari), portal/news-feature style, not academic research style.
- Maintain a positive focus on RSS-related social service, culture, community work, education, disaster relief, youth, rural work and public activities, while keeping every factual claim verifiable and clearly attributed.
- Do not invent numbers, quotes, events, or claims. Prefer primary/official sources and include working source URLs.
- Avoid repeating topics or angles found in recent reports/logs.

## Featured image requirements
- A prompt alone is not a generated image. The report must use an actual image file created by the repository's image workflow.
- Prefer the repository's existing cover-image workflow: a new JSON report pushed under reports/*.json triggers .github/workflows/auto-cover-images.yml, which runs tools/auto_cover.py and writes reports/images/<slug>-cover.png. The generated JSON must set featured_image to images/<slug>-cover.png.
- Use a landscape editorial cover, ideally 16:9, Indian setting, no fabricated real-person likenesses, no misleading visuals, no violence, and no organization logos unless legally/explicitly intended.
- Keep the cover aligned with the actual report topic. If the existing workflow creates a designed title-card instead of an illustrative image, do not describe it as a generated photograph or illustration.
- Validate the JSON schema and local image path before pushing.

## Publish path
- Follow the current report schema and category allowlist in tools/validate.py.
- Put the article JSON in reports/ and record it in log.md.
- Do not claim that publication succeeded merely because a GitHub commit succeeded; check the site's importer/cron if site publication status is available.
- Do not store API keys, credentials, or secrets in this repository.

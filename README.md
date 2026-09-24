# hanayo.cn Hexo source recovery

This local project reconstructs the missing Hexo source from the published
`AlanJager/alanjager.github.io` `github_pages` branch at commit
`8c57db6625056a49c8a6973b7e0f923f16439d38` (2026-09-23). It has not
been pushed or deployed.

## What was recovered

- `source/_posts/`: 47 published article bodies, dates, titles, permalinks,
  categories, tags, and descriptions, extracted from rendered HTML. These are
  EJS/HTML posts, because Markdown source syntax cannot be recovered exactly
  from HTML.
- `source/`: published images and other static assets, plus the handwritten
  `/tools/` pages.
- `themes/landscape/`: a local copy of the author's Landscape theme fork,
  from commit `7cbaf604a2715c7aff45c58c0e06145ff81c8545`. The published
  CSS and JavaScript snapshots are retained in `source/`.
- `scripts/seo-geo-aeo.js`: the script already present in the published repo's
  `hexo-seo` package, so generated pages keep SEO metadata and produce
  `robots.txt`, `sitemap.xml`, and `llms.txt`.
- `recovery/legacy-jekyll/`: exact files from the old `temp` branch. Its 15
  original Markdown posts are a separate, older Jekyll site.
- `recovery/github_pages-8c57db6.tar.gz`: an exact archive of the published
  branch at recovery time. SHA-256:
  `abfe8c6437ae488a36f35c17043ed70d9303851ca79b54839a3bdab0c2d0c638`.
- `source/_drafts/model-quantization-principles.ejs`: the prepared interactive
  quantization article. It is a draft, so a normal build does not publish it.

## Build and check

```bash
cd /Users/kayo/workspace/alanjager-hexo-recovered
npm ci
npm run build
python3 recovery/verify_recovery.py /Users/kayo/workspace/alanjager.github.io
```

The verifier compares all 47 article bodies and their content URLs with the
published pages, and verifies copied static assets byte for byte. A normal
build emits `public/`, including the home page, archives, tags, categories,
feed, and SEO files. The site theme and some generated metadata may differ
from older published pages; the original output archive is the byte-exact
record.

To preview drafts in generated output, run `npx hexo generate --draft`. Run
`npm run build` afterward to restore a publication build without drafts.

## Publish a new post later

Move a reviewed post from `source/_drafts/` to `source/_posts/`, run the build
and verification commands, then deploy `public/` to `github_pages` using the
site's release process. There is intentionally no deploy command in this
recovered project until the desired remote publishing flow is confirmed.

## Limits

Rendered HTML does not retain the author's exact Markdown, comments, source
file names, local draft history, Hexo plugin versions, or unpublished content.
Some old pages had no article heading, so the recovery used their Open Graph
title. The 2019 Jekyll source was preserved separately rather than mixed into
the Hexo posts.

# Hexo 联动（SEO / AEO / GEO）

本仓库 `github_pages` 是 Hexo 生成结果。源项目（含 `source/_posts`）不在这个 git 仓库里。

要让 `robots.txt`、`sitemap.xml`、`llms.txt` 和 JSON-LD 在下次 `hexo generate` 后还在：

1. 把 [`/hexo-seo/scripts/seo-geo-aeo.js`](/hexo-seo/scripts/seo-geo-aeo.js) 拷到源项目的 `scripts/`
2. 把 [`/hexo-seo/_config.snippet.yml`](/hexo-seo/_config.snippet.yml) 合并进源项目 `_config.yml`（`url` 必须是 `https://hanayo.cn`）
3. 把 `tools/` 拷到源项目 `source/tools/`，并设置 `skip_render: [tools/**]`

说明见 [`/hexo-seo/README.md`](/hexo-seo/README.md)。

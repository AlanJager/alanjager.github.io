# hexo-seo

把 SEO / AEO / GEO 接到 **Hexo 生成链路**里，而不是改 `github_pages` 上已经生成的 HTML。

`hanayo.cn` 当前仓库的 `github_pages` 分支是 `hexo generate` 的产物。下次在源项目里执行 `hexo clean && hexo g` 再整目录覆盖时，只改生成结果会被刷掉。要留下的文件必须出现在 Hexo 的 `source/` 或由 `scripts/` 里的 generator 写进 `public/`。

这个仓库里 **没有** 带 `source/_posts` 的 Hexo 源项目（`blog` 分支是 Replica 主题，和线上 Landscape 主题不是同一套）。本目录是给源项目用的插件包。

## Hexo 会保留什么

| 放哪 | `hexo g` 之后 |
|------|----------------|
| `<site>/source/robots.txt` | 原样复制到 `public/robots.txt` |
| `<site>/source/tools/**` + `skip_render: tools/**` | 原样复制，工具页不会被主题包一层 |
| `<site>/scripts/seo-geo-aeo.js` | 每次生成 `sitemap.xml`、`llms.txt`、`robots.txt`，并给 HTML 注入 JSON-LD、补 `lang`、把 `http://hanayo.cn` 改成 https |
| 手工改 `github_pages/**/*.html` | **会被覆盖** |

## 接到源项目

在真正跑 Hexo 的目录（有 `_config.yml` 和 `source/_posts` 的那份）：

```bash
# 1. 脚本：Hexo 会自动加载 scripts/*.js
cp hexo-seo/scripts/seo-geo-aeo.js /path/to/hexo-site/scripts/

# 2. 工具页（已发布的 resume-hub 等）
cp -R tools /path/to/hexo-site/source/tools

# 3. 把 hexo-seo/_config.snippet.yml 里的字段合并进站点 _config.yml
#    关键是 url: https://hanayo.cn 和 skip_render: tools/**
```

主题 `themes/landscape/_config.yml`（或你实际用的主题）菜单加上工具入口，和线上一致：

```yaml
menu:
  首页: /
  归档: /archives
  工具: /tools
```

然后：

```bash
hexo clean && hexo generate
# public/robots.txt  public/sitemap.xml  public/llms.txt
# 每篇文章 </head> 前会有 BlogPosting JSON-LD
```

把 `public/` 部署到 `github_pages` 时，这些文件会一起上去。

## 文章怎么写才对 AEO / GEO 有用

front-matter 请带 `description`（40–60 字结论）。脚本会把它写进 `llms.txt` 和 JSON-LD。

```markdown
---
title: XFS 报错但根因不在 XFS：一次 uprobe 越界写排查
description: 两台 Linux 虚拟机因 XFS 元数据损坏 forced shutdown，根因是 uprobe 在边界检查前写出了 per-CPU buffer。
tags: [kernel, linux, security]
---

**结论：** （同上，独立成段）

## 检索句形式的 H2
第一句就是完整答案。
```

## 和当前线上站点的关系

本仓库根目录的 `robots.txt` / `sitemap.xml` / `llms.txt` 是脚本的**当前快照**，给还没接上源项目之前的 GitHub Pages 用。源项目接好之后，以 `hexo generate` 输出为准。

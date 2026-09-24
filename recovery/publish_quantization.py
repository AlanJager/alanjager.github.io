#!/usr/bin/env python3
"""Apply the new article to an existing generated github_pages checkout.

This deliberately preserves old generated article pages. Run after `npm run
build`; review the target checkout's diff before pushing it.
"""

import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup


target = Path(sys.argv[1]).resolve()
built = Path(__file__).resolve().parents[1] / "public"
slug = "/2026/09/24/model-quantization-principles/"
old_slug = "/2026/09/23/juicefs-nfs-format-nfs3-nfs4/"
title = "模型量化原理：从单个权重到逐层推理"
description = "用图解、交互实验和公式理解大模型权重、激活与 KV Cache 量化，并估算推理时的存储与显存占用。"


def replace_once(path, old, new):
    file = target / path
    text = file.read_text(encoding="utf-8")
    if slug in text:
        raise RuntimeError(f"Article already listed in {path}")
    if text.count(old) != 1:
        raise RuntimeError(f"Expected one insertion marker in {path}; found {text.count(old)}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


article = built / slug.lstrip("/") / "index.html"
if not article.exists():
    raise RuntimeError("Build the Hexo source first")
destination = target / slug.lstrip("/") / "index.html"
if destination.exists():
    raise RuntimeError(f"Article already exists: {destination}")

home = BeautifulSoup((built / "index.html").read_text(), "html.parser")
teaser = home.select_one("#post-model-quantization-principles")
if teaser is None:
    raise RuntimeError("Generated homepage teaser missing")
teaser_html = str(teaser).replace(slug + "#more", slug)
archive = BeautifulSoup((built / "archives/2026/index.html").read_text(), "html.parser")
archive_item = next((a for a in archive.select("article.archive-article") if a.select_one(f'a[href="{slug}"]')), None)
if archive_item is None:
    raise RuntimeError("Generated archive item missing")
archive_html = str(archive_item)

# Validate every target marker before writing any file.
home_path = target / "index.html"
if old_slug not in home_path.read_text(encoding="utf-8"):
    raise RuntimeError("Current homepage is not the expected published version")
for rel in (
    "archives/index.html",
    "archives/2026/index.html",
    "archives/2026/09/index.html",
    "categories/arch-notes/index.html",
):
    html = (target / rel).read_text(encoding="utf-8")
    if slug in html or old_slug not in html:
        raise RuntimeError(f"Unexpected archive/category state: {rel}")
if slug in (target / "atom.xml").read_text(encoding="utf-8"):
    raise RuntimeError("Article already in feed")

destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(article, destination)

# Keep existing pagination and old pages byte-identical. The first page gains
# one additional teaser; subsequent pages retain their original boundaries.
home_text = home_path.read_text(encoding="utf-8")
old_article_start = home_text.rfind("<article", 0, home_text.index(old_slug))
if old_article_start < 0:
    raise RuntimeError("Could not locate first homepage article")
home_path.write_text(home_text[:old_article_start] + teaser_html + "\n\n" + home_text[old_article_start:], encoding="utf-8")

for rel in (
    "archives/index.html",
    "archives/2026/index.html",
    "archives/2026/09/index.html",
    "categories/arch-notes/index.html",
):
    path = target / rel
    text = path.read_text(encoding="utf-8")
    start = text.rfind("<article", 0, text.index(old_slug))
    if start < 0:
        raise RuntimeError(f"Could not locate first article in {rel}")
    path.write_text(text[:start] + archive_html + text[start:], encoding="utf-8")

for tag in ("llm", "quantization", "inference"):
    old = built / f"tags/{tag}/index.html"
    new = target / f"tags/{tag}/index.html"
    if new.exists():
        raise RuntimeError(f"Tag page already exists: {new}")
    new.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(old, new)
    new.write_text("\n".join(line.rstrip() for line in new.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")

# The tag directory page is a pre-generated Hexo page, so add only these tags.
tags_path = target / "tags/index.html"
tags_html = tags_path.read_text(encoding="utf-8")
match = re.search(r'<ul class="tag-list"[^>]*>.*?</ul>', tags_html, re.S)
if not match or slug in tags_html:
    raise RuntimeError("Tag directory could not be updated safely")
tags = "".join(
    f'<li class="tag-list-item"><a class="tag-list-link" href="/tags/{tag}/" rel="tag">{tag}</a></li>'
    for tag in ("inference", "llm", "quantization")
)
new_list = match.group(0).replace("</ul>", tags + "</ul>")
tags_path.write_text(tags_html[:match.start()] + new_list + tags_html[match.end():], encoding="utf-8")

feed_html = (built / "atom.xml").read_text(encoding="utf-8")
feed_entry = re.search(r"<entry>.*?</entry>", feed_html, re.S)
if not feed_entry:
    raise RuntimeError("Generated feed entry missing")
feed_item = "\n".join(line.rstrip() for line in feed_entry.group(0).splitlines())
feed_path = target / "atom.xml"
feed_old = feed_path.read_text(encoding="utf-8")
feed_new = feed_old.replace("<updated>2026-09-23T08:00:00.000Z</updated>", "<updated>2026-09-24T07:00:00.000Z</updated>", 1)
feed_new = feed_new.replace("  <entry>", "  " + feed_item + "\n\n  <entry>", 1)
if feed_new == feed_old:
    raise RuntimeError("Feed did not change")
feed_path.write_text(feed_new, encoding="utf-8")

sitemap_path = target / "sitemap.xml"
sitemap_old = sitemap_path.read_text(encoding="utf-8")
sitemap_new = sitemap_old.replace("<lastmod>2026-09-22</lastmod>", "<lastmod>2026-09-24</lastmod>", 1)
url_entry = (
    "  <url>\n"
    f"    <loc>https://hanayo.cn{slug}</loc>\n"
    "    <lastmod>2026-09-24</lastmod>\n"
    "    <changefreq>monthly</changefreq>\n"
    "    <priority>0.8</priority>\n"
    "  </url>\n"
)
sitemap_new = sitemap_new.replace("</urlset>", url_entry + "</urlset>", 1)
sitemap_path.write_text(sitemap_new, encoding="utf-8")

replace_once(
    "llms.txt",
    "## 近期文章\n\n",
    f"## 近期文章\n\n- [{title}](https://hanayo.cn{slug}) — {description}\n",
)
print("Published article and updated homepage, archives, category, tags, feed, sitemap, and llms.txt")

#!/usr/bin/env python3
"""Recover editable Hexo posts and assets from a published Hexo output tree."""

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup


published = Path(sys.argv[1]).resolve()
project = Path(__file__).resolve().parents[1]
posts = project / "source/_posts"
posts.mkdir(parents=True, exist_ok=True)
manifest = []


def local_date(iso):
    if not iso:
        return None
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(
        ZoneInfo("Asia/Shanghai")
    ).strftime("%Y-%m-%d %H:%M:%S")


for page in sorted(published.glob("20??/??/??/*/index.html")):
    relative = page.relative_to(published)
    html = page.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    body = soup.select_one(".article-entry[itemprop='articleBody']")
    title_tag = soup.select_one("h1.article-title")
    if body is None:
        raise RuntimeError(f"Article body missing: {relative}")
    fallback_title = soup.select_one('meta[property="og:title"]')
    title = title_tag.get_text(" ", strip=True) if title_tag else (
        fallback_title.get("content", relative.parts[3]) if fallback_title else relative.parts[3]
    )
    category = [x.get_text(" ", strip=True) for x in soup.select(".article-category-link")]
    tags = [x.get_text(" ", strip=True) for x in soup.select(".article-tag-list-link")]
    description_tag = soup.select_one('meta[name="description"]')
    published_tag = soup.select_one('meta[property="article:published_time"]')
    modified_tag = soup.select_one('meta[property="article:modified_time"]')
    date = local_date(published_tag.get("content")) if published_tag else None
    date = date or f"{relative.parts[0]}-{relative.parts[1]}-{relative.parts[2]} 00:00:00"
    front = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"date: {json.dumps(date)}",
        f"permalink: {json.dumps(relative.parent.as_posix() + '/')}",
    ]
    updated = local_date(modified_tag.get("content")) if modified_tag else None
    if updated:
        front.append(f"updated: {json.dumps(updated)}")
    if description_tag and description_tag.get("content"):
        front.append(f"description: {json.dumps(description_tag['content'], ensure_ascii=False)}")
    if category:
        front.append(f"categories: {json.dumps(category, ensure_ascii=False)}")
    if tags:
        front.append(f"tags: {json.dumps(tags, ensure_ascii=False)}")
    front += ["disableNunjucks: true", "---", ""]
    content = body.decode_contents(formatter="minimal").strip()
    if "<%" in content or "%>" in content:
        raise RuntimeError(f"EJS delimiter in article body: {relative}")
    name = f"{relative.parts[0]}-{relative.parts[1]}-{relative.parts[2]}-{relative.parts[3]}.ejs"
    target = posts / name
    target.write_text("\n".join(front) + "\n" + content + "\n", encoding="utf-8")
    manifest.append({
        "page": relative.as_posix(),
        "source": target.relative_to(project).as_posix(),
        "sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
        "title": title,
        "date": date,
        "categories": category,
        "tags": tags,
    })

for asset in published.rglob("*"):
    if not asset.is_file() or ".git" in asset.parts:
        continue
    rel = asset.relative_to(published)
    if asset.name == ".gitignore" or asset.suffix.lower() in {".html", ".xml"} or rel.parts[0] in {
        "archives", "categories", "tags", "page", "hexo-seo", "maintenance"
    }:
        continue
    if rel.name in {"robots.txt", "llms.txt", "sitemap.xml"}:
        continue
    target = project / "source" / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(asset, target)

# These are handcrafted pages in the deployed tree, not generated article pages.
for rel in [Path("tools/index.html"), Path("tools/resume-hub/index.html")]:
    old = published / rel
    if old.exists():
        new = project / "source" / rel
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old, new)

(project / "recovery/manifest.json").write_text(
    json.dumps({"source_commit": "8c57db6625056a49c8a6973b7e0f923f16439d38", "articles": manifest}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"Recovered {len(manifest)} articles and static assets")

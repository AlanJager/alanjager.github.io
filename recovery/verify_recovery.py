#!/usr/bin/env python3
"""Check every reconstructed article against its published source."""

import hashlib
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup


published = Path(sys.argv[1]).resolve()
project = Path(__file__).resolve().parents[1]
manifest = json.loads((project / "recovery/manifest.json").read_text())
errors = []

for article in manifest["articles"]:
    rel = Path(article["page"])
    original = published / rel
    built = project / "public" / rel
    if not built.exists():
        errors.append(f"Missing output: {rel}")
        continue
    if hashlib.sha256(original.read_bytes()).hexdigest() != article["sha256"]:
        errors.append(f"Published input changed: {rel}")
        continue
    old = BeautifulSoup(original.read_text(encoding="utf-8"), "html.parser")
    new = BeautifulSoup(built.read_text(encoding="utf-8"), "html.parser")
    old_body = old.select_one(".article-entry[itemprop='articleBody']")
    new_body = new.select_one(".article-entry[itemprop='articleBody']")
    if old_body is None or new_body is None:
        errors.append(f"Body missing: {rel}")
        continue
    if old_body.get_text(" ", strip=True) != new_body.get_text(" ", strip=True):
        errors.append(f"Body text mismatch: {rel}")
    for old_tag, new_tag in zip(old_body.select("a[href], img[src]"), new_body.select("a[href], img[src]")):
        attr = "href" if old_tag.name == "a" else "src"
        if old_tag.get(attr) != new_tag.get(attr):
            errors.append(f"Content URL mismatch: {rel}: {old_tag.get(attr)} != {new_tag.get(attr)}")
    if len(old_body.select("a[href], img[src]")) != len(new_body.select("a[href], img[src]")):
        errors.append(f"Content URL count mismatch: {rel}")

for asset in (project / "source").rglob("*"):
    if not asset.is_file() or "_posts" in asset.parts or "_drafts" in asset.parts:
        continue
    rel = asset.relative_to(project / "source")
    built = project / "public" / rel
    if not built.exists() or hashlib.sha256(asset.read_bytes()).digest() != hashlib.sha256(built.read_bytes()).digest():
        errors.append(f"Static asset mismatch: {rel}")

if errors:
    print("\n".join(errors[:30]))
    print(f"{len(errors)} total errors")
    sys.exit(1)
print(f"Verified {len(manifest['articles'])} article bodies and all copied static assets")

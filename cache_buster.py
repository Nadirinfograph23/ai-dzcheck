#!/usr/bin/env python3
"""
AI DZ CHECK — Cache Busting System
====================================
Hashes static assets and updates all references, then writes a clean
production build to dist/.  Idempotent: unchanged files keep their
existing hash so the dist/ output is stable across runs.

Usage
-----
  python3 cache_buster.py          # build dist/
  python3 cache_buster.py --clean  # delete dist/ and rebuild from scratch
  python3 cache_buster.py --check  # print current hash status (dry-run)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

ROOT       = Path(__file__).parent.resolve()
DIST       = ROOT / "dist"
MANIFEST   = ROOT / "hash_manifest.json"

# Files whose content will be hashed and renamed (relative to ROOT)
HASHABLE = [
    "style.css",
    "script.js",
    "icon-192.png",
    "icon-512.png",
    "apple-touch-icon.png",
]

# Files that are copied as-is (no renaming, but their content IS updated
# to reference hashed filenames)
PASSTHROUGH = [
    "index.html",
    "sw.js",
    "manifest.json",
    "vercel.json",
]

# Source files where old asset references are replaced with hashed ones.
# Order matters: process sw.js after we know all hashes.
UPDATE_REFERENCES_IN = [
    "index.html",
    "sw.js",
    "manifest.json",
]

# Directories / files to ignore when copying everything else
IGNORE = {
    ".git", ".github", ".local", ".agents", ".cache", ".replit",
    "dist", "__pycache__", "node_modules",
    "cache_buster.py", "hash_manifest.json",
    "replit.md",
}

HASH_LENGTH = 8   # characters of the hex digest to embed in filename

# ── Helpers ───────────────────────────────────────────────────────────────────

def md5(path: Path) -> str:
    """Return a hex-encoded MD5 digest of a file's content."""
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hashed_name(original: str, digest: str) -> str:
    """
    'style.css', 'a1b2c3d4'  →  'style.a1b2c3d4.css'
    'icon-192.png', 'ff00ff00' → 'icon-192.ff00ff00.png'
    """
    stem, _, ext = original.rpartition(".")
    return f"{stem}.{digest[:HASH_LENGTH]}.{ext}"


def load_manifest() -> dict:
    if MANIFEST.exists():
        with MANIFEST.open() as fh:
            return json.load(fh)
    return {}


def save_manifest(data: dict) -> None:
    with MANIFEST.open("w") as fh:
        json.dump(data, fh, indent=2)
    print(f"  📄  hash_manifest.json updated")


def copy_tree(src: Path, dst: Path) -> None:
    """Recursively copy src → dst, respecting IGNORE list."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in IGNORE or item.name.startswith("."):
            continue
        target = dst / item.name
        if item.is_dir():
            copy_tree(item, target)
        else:
            shutil.copy2(item, target)


# ── Reference-replacement helpers ─────────────────────────────────────────────

def build_replace_map(rename_map: dict) -> dict:
    """
    Build all the string substitutions we need to make.
    rename_map:  { 'style.css': 'style.a1b2c3.css', ... }

    We need to catch references like:
      href="style.css"
      href="style.css?v=20"
      href='/style.css'
      src="./script.js"
      /style.css            (inside sw.js ASSETS array)
    """
    replacements = {}
    for original, hashed in rename_map.items():
        # Bare filename with optional query-string param
        # e.g.  style.css?v=20  →  style.a1b2c3.css
        replacements[re.escape(original) + r"(\?[^\"'\s]*)?" ] = hashed

        # Absolute-path variant: /style.css → /style.a1b2c3.css
        replacements[r"/" + re.escape(original) + r"(\?[^\"'\s]*)?"] = (
            "/" + hashed
        )
    return replacements


def replace_references(content: str, replace_map: dict) -> str:
    """Apply all regex substitutions from replace_map to content string."""
    for pattern, replacement in replace_map.items():
        content = re.sub(pattern, replacement, content)
    return content


def bump_sw_cache_version(content: str, new_version: str) -> str:
    """
    Replace  var CACHE_NAME = 'aidzcheck-vXX';
    with     var CACHE_NAME = 'aidzcheck-<new_version>';
    """
    return re.sub(
        r"(var\s+CACHE_NAME\s*=\s*['\"])aidzcheck-[^'\"]+(['\"])",
        rf"\g<1>aidzcheck-{new_version}\g<2>",
        content,
    )


def strip_query_params_from_hashed(content: str, rename_map: dict) -> str:
    """
    After replacement, ensure no leftover ?v=XX survives next to
    already-hashed filenames (belt-and-suspenders pass).
    """
    for hashed in rename_map.values():
        content = re.sub(
            re.escape(hashed) + r"\?[^\"'\s]*",
            hashed,
            content,
        )
    return content


# ── Core build routine ────────────────────────────────────────────────────────

def build(clean: bool = False) -> dict:
    print("\n🔧  AI DZ CHECK — Cache Buster")
    print("=" * 48)

    if clean and DIST.exists():
        shutil.rmtree(DIST)
        print("  🗑   dist/ cleaned")

    # 1. Compute hashes for all hashable assets
    old_manifest = load_manifest()
    new_manifest = {}
    rename_map   = {}   # { 'style.css': 'style.a1b2c3.css' }
    changed      = []

    print("\n📊  Computing hashes …")
    for name in HASHABLE:
        src = ROOT / name
        if not src.exists():
            print(f"  ⚠   {name} not found — skipped")
            continue

        digest      = md5(src)[:HASH_LENGTH]
        new_name    = hashed_name(name, digest)
        new_manifest[name] = {
            "hashed": new_name,
            "md5"   : digest,
        }
        rename_map[name] = new_name

        old_entry = old_manifest.get(name, {})
        if old_entry.get("md5") == digest:
            status = "unchanged ✓"
        else:
            status = "CHANGED  ↑"
            changed.append(name)

        print(f"  {name:30s}  →  {new_name:42s}  [{status}]")

    # 2. Copy entire project to dist/
    print("\n📁  Copying files to dist/ …")
    copy_tree(ROOT, DIST)

    # 3. Rename hashed assets inside dist/
    print("\n✂   Renaming hashed files in dist/ …")
    for original, hashed in rename_map.items():
        src = DIST / original
        dst = DIST / hashed
        if src.exists():
            if dst.exists():
                dst.unlink()
            src.rename(dst)
            print(f"  {original}  →  {hashed}")

    # 4. Build replacement map and version string
    replace_map   = build_replace_map(rename_map)
    build_version = md5(ROOT / "index.html")[:8] if (ROOT / "index.html").exists() else "0"

    # 5. Update references in HTML / SW / manifest
    print("\n🔗  Updating asset references …")
    for fname in UPDATE_REFERENCES_IN:
        fpath = DIST / fname
        if not fpath.exists():
            continue

        original_text = fpath.read_text(encoding="utf-8")
        updated_text  = replace_references(original_text, replace_map)
        updated_text  = strip_query_params_from_hashed(updated_text, rename_map)

        # Bump service-worker cache key so browsers pick up new assets
        if fname == "sw.js":
            updated_text = bump_sw_cache_version(updated_text, build_version)
            print(f"  sw.js CACHE_NAME  →  aidzcheck-{build_version}")

        if updated_text != original_text:
            fpath.write_text(updated_text, encoding="utf-8")
            print(f"  {fname:20s} references updated ✅")
        else:
            print(f"  {fname:20s} no changes needed")

    # 6. Remove vercel.json from dist/ — Vercel reads it from repo root only
    dist_vercel = DIST / "vercel.json"
    if dist_vercel.exists():
        dist_vercel.unlink()

    # 7. Persist the manifest
    save_manifest(new_manifest)

    # 8. Summary
    print(f"\n✅  Build complete  →  dist/")
    if changed:
        print(f"   Changed files : {', '.join(changed)}")
    else:
        print("   All files unchanged (hashes match previous run)")
    print()

    return new_manifest




# ── Check (dry-run) ────────────────────────────────────────────────────────────

def check() -> None:
    print("\n🔍  Hash status (dry-run — no files written)")
    print("=" * 56)
    old = load_manifest()
    for name in HASHABLE:
        src = ROOT / name
        if not src.exists():
            print(f"  ⚠   {name:30s} NOT FOUND")
            continue
        digest   = md5(src)[:HASH_LENGTH]
        new_name = hashed_name(name, digest)
        old_md5  = old.get(name, {}).get("md5", "—")
        flag     = "✓ same" if old_md5 == digest else "↑ changed"
        print(f"  {name:30s}  {new_name:42s}  [{flag}]")
    print()


# ── CLI entry point ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="AI DZ CHECK cache buster")
    parser.add_argument("--clean", action="store_true",
                        help="Delete dist/ before rebuilding")
    parser.add_argument("--check", action="store_true",
                        help="Dry-run: print hash status only")
    args = parser.parse_args()

    if args.check:
        check()
        sys.exit(0)

    build(clean=args.clean)


if __name__ == "__main__":
    main()

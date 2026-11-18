#!/usr/bin/env python3
"""Fail if a cached game file changed but sw.js CACHE did not.
Usage: check_cache.py <base_sha> <head_sha>
Docs-only changes (*.md, tools/, .github/, ...) never need a version bump."""
import re, subprocess, sys

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout

base, head = sys.argv[1], sys.argv[2]
if set(base) <= {"0"}:           # first push of a branch: nothing to compare
    print("no base commit, skipping"); sys.exit(0)

def cache_of(rev):
    m = re.search(r"const CACHE\s*=\s*'([^']+)'", git("show", f"{rev}:sw.js"))
    return m.group(1) if m else None

pre = re.search(r"const PRECACHE\s*=\s*\[(.*?)\]", git("show", f"{head}:sw.js"), re.S).group(1)
cached = set()
for p in re.findall(r'"\./([^"]*)"', pre):
    cached.add(p or "index.html")
cached.add("index.html")

changed = [f for f in git("diff", "--name-only", base, head).split("\n") if f]
hit = sorted(f for f in changed if f in cached)
print("changed files:", changed)
print("cached game files changed:", hit)
if not hit:
    print("OK: no cached file changed, no version bump needed"); sys.exit(0)
b, h = cache_of(base), cache_of(head)
print(f"CACHE: {b} -> {h}")
if b == h:
    print("ERROR: cached files changed but sw.js CACHE was not bumped"); sys.exit(1)
print("OK"); sys.exit(0)

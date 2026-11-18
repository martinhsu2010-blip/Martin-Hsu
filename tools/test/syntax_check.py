#!/usr/bin/env python3
"""Cheap pre-PR check: extract every inline <script> from index.html and syntax-check it with node.
Also verifies sw.js parses and every PRECACHE file exists. Usage: python3 tools/test/syntax_check.py"""
import re, subprocess, sys, tempfile, os, json
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
html = open(os.path.join(root, "index.html"), encoding="utf-8").read()
fail = 0
for i, m in enumerate(re.finditer(r"<script([^>]*)>(.*?)</script>", html, re.S)):
    attrs, body = m.group(1), m.group(2)
    if "src=" in attrs or not body.strip():
        continue
    if "importmap" in attrs:
        try: json.loads(body); print(f"script {i}: importmap JSON ok")
        except Exception as e: print(f"script {i}: importmap INVALID {e}"); fail = 1
        continue
    ext = ".mjs" if "module" in attrs else ".js"
    with tempfile.NamedTemporaryFile("w", suffix=ext, delete=False, encoding="utf-8") as f:
        f.write(body); p = f.name
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    os.unlink(p)
    print(f"script {i} ({ext}, {len(body)} chars):", "ok" if r.returncode == 0 else "SYNTAX ERROR\n" + r.stderr[:1500])
    fail |= r.returncode != 0
sw = open(os.path.join(root, "sw.js"), encoding="utf-8").read()
for p in re.findall(r'"\./([^"]*)"', re.search(r"PRECACHE\s*=\s*\[(.*?)\]", sw, re.S).group(1)):
    if p and not os.path.exists(os.path.join(root, p)):
        print("MISSING precache file:", p); fail = 1
print("RESULT:", "FAIL" if fail else "PASS"); sys.exit(fail)

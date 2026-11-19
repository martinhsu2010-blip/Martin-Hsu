"""CI gate for the centralized locale table and untranslated visible CJK.
Comments, shader comments and console diagnostics are implementation details.
Run from any directory; an optional HTML path supports negative fixture checks.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')

def decoded(value):
    return re.sub(r'\\u(?:\{([0-9a-fA-F]+)\}|([0-9a-fA-F]{4}))', lambda m: chr(int(m[1] or m[2], 16)), value)

def literals(code):
    i = 0
    while i < len(code):
        if code.startswith('//', i):
            n = code.find('\n', i); i = len(code) if n < 0 else n
        elif code.startswith('/*', i):
            n = code.find('*/', i + 2); i = len(code) if n < 0 else n + 2
        elif code[i] in "'\"`":
            start = i; quote = code[i]; i += 1
            while i < len(code):
                if code[i] == '\\': i += 2; continue
                if code[i] == quote: break
                i += 1
            i += 1
            yield start, decoded(code[start + 1:i - 1])
        else:
            i += 1

def inspect(source):
    errors = []
    class Markup(HTMLParser):
        def __init__(self): super().__init__(); self.skip = False
        def handle_starttag(self, tag, attrs):
            if tag in ('script', 'style'): self.skip = True
            for key, value in attrs:
                if value and CJK.search(value): errors.append(f'HTML attribute {key}: {value[:70]}')
        def handle_endtag(self, tag):
            if tag in ('script', 'style'): self.skip = False
        def handle_data(self, value):
            if not self.skip and CJK.search(value): errors.append(f'HTML text: {value.strip()[:70]}')
    Markup().feed(source)
    for script in re.finditer(r'<script\b[^>]*>([\s\S]*?)</script>', source):
        code = script[1]
        for offset, value in literals(code):
            line = code[code.rfind('\n', 0, offset) + 1:code.find('\n', offset) if '\n' in code[offset:] else len(code)]
            if re.search(r'\bconsole\.(log|warn|error|info|debug)\(', line): continue
            # GLSL strings contain source comments, not UI text.
            if '#include' in value or re.search(r'\b(?:vec[234]|float|uniform)\s+\w+', value) and '\n' in value:
                value = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', value)
            if CJK.search(value): errors.append(f'JS literal: {value[:70]}')
    return errors

def main():
    source = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else (ROOT / 'index.html').read_text()
    match = re.search(r'// I18N_TABLE_START\s*const STRINGS = ([\s\S]*?);\s*// I18N_TABLE_END', source)
    assert match, 'Missing centralized string table'
    table = json.loads(match[1])
    assert set(table) == {'en', 'zh-TW'}
    assert set(table['en']) == set(table['zh-TW']), 'Mismatched locale keys'
    for lang, entries in table.items():
        assert all(isinstance(v, str) and v for v in entries.values()), lang
    remainder = source[:match.start()] + source[match.end():]
    keys = set(re.findall(r"\btr\('([^']+)'\)", remainder))
    keys.update(re.findall(r'data-i18n(?:-(?:aria-label|title|placeholder|alt))?="([^"]+)"', remainder))
    assert not keys - set(table['en']), f'Missing keys: {keys - set(table["en"])}'
    errors = inspect(remainder)
    for lang, path in [('en', 'manifest.webmanifest'), ('zh-TW', 'manifest.zh-TW.webmanifest')]:
        manifest = json.loads((ROOT / path).read_text())
        assert manifest['description'] == table[lang]['description'], path
        assert manifest['lang'] == lang and manifest['start_url'] == './index.html', path
    # Check the scanner itself against raw/escaped text, templates, attributes and comments.
    for fixture in ['<p>漏譯</p>', '<button aria-label="漏譯"></button>', '<script>showBanner("漏譯");</script>', r'<script>const text="\u6f0f\u8b6f";</script>', '<script>const text=`漏譯 ${count}`;</script>']:
        assert inspect(fixture), fixture
    assert not inspect('<!-- 註解 --><script>// 註解\n/* 註解 */const id="STUNT";</script>')
    if errors:
        print('\n'.join(errors)); raise SystemExit('RESULT: FAIL (untranslated CJK)')
    print(f'RESULT: PASS ({len(table["en"])} bilingual keys; no visible CJK outside the table)')

if __name__ == '__main__': main()

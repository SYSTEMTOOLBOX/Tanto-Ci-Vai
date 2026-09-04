from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
old = 'community-ui-v2.js?v=2'
new = 'community-ui-v2.js?v=3'
if old not in s and new not in s:
    raise SystemExit('community-ui-v2 script tag not found')
if old in s:
    s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('Community profile UI cache version:', new)

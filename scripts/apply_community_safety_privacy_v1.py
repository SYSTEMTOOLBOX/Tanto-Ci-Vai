from pathlib import Path
import re

idx = Path('index.html')
html = idx.read_text(encoding='utf-8')

if 'community-safety.js' not in html:
    pat = r'(<script[^>]+src=["\']community-routes\.js\?v=\d+["\'][^>]*></script>)'
    html2, n = re.subn(pat, r'\1\n<script src="community-safety.js?v=1"></script>', html, count=1)
    if n != 1:
        raise SystemExit('community-routes script tag not found')
    html = html2
else:
    html = re.sub(r'community-safety\.js\?v=\d+', 'community-safety.js?v=1', html, count=1)

idx.write_text(html, encoding='utf-8')
print('Community safety/privacy layer wired into index.html')

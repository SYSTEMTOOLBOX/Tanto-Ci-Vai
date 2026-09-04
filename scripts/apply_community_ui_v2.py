from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<script src="./community-profile.js?v=1"></script>'
insert=marker+'\n<script src="./community-ui-v2.js?v=1"></script>'
if 'community-ui-v2.js' not in s:
    if marker not in s:
        raise SystemExit('community-profile script marker not found')
    s=s.replace(marker,insert,1)
p.write_text(s,encoding='utf-8')

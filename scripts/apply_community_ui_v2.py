from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

profile_pattern=r'<script src="\./community-profile\.js\?v=\d+"></script>'
ui_pattern=r'<script src="\./community-ui-v2\.js\?v=\d+"></script>'
fix_pattern=r'<script src="\./community-document-ui-fix\.js\?v=\d+"></script>'
qr_pattern=r'<script src="\./community-qr\.js\?v=\d+"></script>'
account_pattern=r'<script src="\./community-phone-verification\.js\?v=\d+"></script>'

profile_match=re.search(profile_pattern,s)
if not profile_match:
    raise SystemExit('community-profile script marker not found')

ui_tag='<script src="./community-ui-v2.js?v=9"></script>'
fix_tag='<script src="./community-document-ui-fix.js?v=2"></script>'
qr_tag='<script src="./community-qr.js?v=2"></script>'
account_tag='<script src="./community-phone-verification.js?v=4"></script>'

if re.search(ui_pattern,s):
    s=re.sub(ui_pattern,ui_tag,s,count=1)
else:
    s=s.replace(profile_match.group(0),profile_match.group(0)+'\n'+ui_tag,1)

if re.search(fix_pattern,s):
    s=re.sub(fix_pattern,fix_tag,s,count=1)
else:
    s=s.replace(ui_tag,ui_tag+'\n'+fix_tag,1)

if re.search(qr_pattern,s):
    s=re.sub(qr_pattern,qr_tag,s,count=1)
else:
    s=s.replace(fix_tag,fix_tag+'\n'+qr_tag,1)

if re.search(account_pattern,s):
    s=re.sub(account_pattern,account_tag,s,count=1)
else:
    s=s.replace(ui_tag,account_tag+'\n'+ui_tag,1)

p.write_text(s,encoding='utf-8')

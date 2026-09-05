from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

profile_pattern=r'<script src="\./community-profile\.js\?v=\d+"></script>'
ui_pattern=r'<script src="\./community-ui-v2\.js\?v=\d+"></script>'
fix_pattern=r'<script src="\./community-document-ui-fix\.js\?v=\d+"></script>'
qr_pattern=r'<script src="\./community-qr\.js\?v=\d+"></script>'
account_pattern=r'<script src="\./community-phone-verification\.js\?v=\d+"></script>'
satispay_status_pattern=r'<script src="\./satispay-profile-status\.js\?v=\d+"></script>'
compact_profile_pattern=r'<script src="\./community-profile-compact\.js\?v=\d+"></script>'
photo_only_pattern=r'<script src="\./community-profile-photo-only\.js\?v=\d+"></script>'

profile_match=re.search(profile_pattern,s)
if not profile_match:
    raise SystemExit('community-profile script marker not found')

ui_tag='<script src="./community-ui-v2.js?v=9"></script>'
fix_tag='<script src="./community-document-ui-fix.js?v=2"></script>'
qr_tag='<script src="./community-qr.js?v=2"></script>'
account_tag='<script src="./community-phone-verification.js?v=6"></script>'
satispay_status_tag='<script src="./satispay-profile-status.js?v=2"></script>'
compact_profile_tag='<script src="./community-profile-compact.js?v=2"></script>'
photo_only_tag='<script src="./community-profile-photo-only.js?v=6"></script>'

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

if re.search(satispay_status_pattern,s):
    s=re.sub(satispay_status_pattern,satispay_status_tag,s,count=1)
else:
    s=s.replace(account_tag,account_tag+'\n'+satispay_status_tag,1)

if re.search(compact_profile_pattern,s):
    s=re.sub(compact_profile_pattern,compact_profile_tag,s,count=1)
else:
    s=s.replace(satispay_status_tag,satispay_status_tag+'\n'+compact_profile_tag,1)

if re.search(photo_only_pattern,s):
    s=re.sub(photo_only_pattern,photo_only_tag,s,count=1)
else:
    s=s.replace(compact_profile_tag,compact_profile_tag+'\n'+photo_only_tag,1)

p.write_text(s,encoding='utf-8')

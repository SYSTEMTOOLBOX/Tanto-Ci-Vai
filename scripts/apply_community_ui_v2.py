from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

profile_pattern=r'<script src="\./community-profile\.js\?v=\d+"></script>'
ui_pattern=r'<script src="\./community-ui-v2\.js\?v=\d+"></script>'
fix_pattern=r'<script src="\./community-document-ui-fix\.js\?v=\d+"></script>'
qr_pattern=r'<script src="\./community-qr\.js\?v=\d+"></script>'
qr_auth_pattern=r'<script src="\./community-qr-auth-fix\.js\?v=\d+"></script>'
account_pattern=r'<script src="\./community-phone-verification\.js\?v=\d+"></script>'
satispay_status_pattern=r'<script src="\./satispay-profile-status\.js\?v=\d+"></script>'
compact_profile_pattern=r'<script src="\./community-profile-compact\.js\?v=\d+"></script>'
photo_only_pattern=r'<script src="\./community-profile-photo-only\.js\?v=\d+"></script>'
role_gate_pattern=r'<script src="\./community-role-gates\.js\?v=\d+"></script>'
registration_gate_pattern=r'<script src="\./community-registration-gates\.js\?v=\d+"></script>'
driver_experience_pattern=r'<script src="\./community-driver-experience\.js\?v=\d+"></script>'
public_readonly_pattern=r'<script src="\./community-public-profile-readonly\.js\?v=\d+"></script>'
crime_alerts_pattern=r'<script src="\./community-crime-alerts\.js\?v=\d+"></script>'
header_profile_pattern=r'<script src="\./community-header-profile\.js\?v=\d+"></script>'

profile_match=re.search(profile_pattern,s)
if not profile_match:
    raise SystemExit('community-profile script marker not found')

ui_tag='<script src="./community-ui-v2.js?v=10"></script>'
fix_tag='<script src="./community-document-ui-fix.js?v=2"></script>'
qr_tag='<script src="./community-qr.js?v=2"></script>'
qr_auth_tag='<script src="./community-qr-auth-fix.js?v=3"></script>'
account_tag='<script src="./community-phone-verification.js?v=6"></script>'
satispay_status_tag='<script src="./satispay-profile-status.js?v=2"></script>'
compact_profile_tag='<script src="./community-profile-compact.js?v=4"></script>'
photo_only_tag='<script src="./community-profile-photo-only.js?v=6"></script>'
role_gate_tag='<script src="./community-role-gates.js?v=2"></script>'
registration_gate_tag='<script src="./community-registration-gates.js?v=2"></script>'
driver_experience_tag='<script src="./community-driver-experience.js?v=1"></script>'
public_readonly_tag='<script src="./community-public-profile-readonly.js?v=1"></script>'
crime_alerts_tag='<script src="./community-crime-alerts.js?v=2"></script>'
header_profile_tag='<script src="./community-header-profile.js?v=2"></script>'

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

if re.search(qr_auth_pattern,s):
    s=re.sub(qr_auth_pattern,qr_auth_tag,s,count=1)
else:
    s=s.replace(qr_tag,qr_tag+'\n'+qr_auth_tag,1)

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

if re.search(role_gate_pattern,s):
    s=re.sub(role_gate_pattern,role_gate_tag,s,count=1)
else:
    s=s.replace(photo_only_tag,photo_only_tag+'\n'+role_gate_tag,1)

if re.search(registration_gate_pattern,s):
    s=re.sub(registration_gate_pattern,registration_gate_tag,s,count=1)
else:
    s=s.replace(role_gate_tag,role_gate_tag+'\n'+registration_gate_tag,1)

if re.search(driver_experience_pattern,s):
    s=re.sub(driver_experience_pattern,driver_experience_tag,s,count=1)
else:
    s=s.replace(fix_tag,fix_tag+'\n'+driver_experience_tag,1)

if re.search(public_readonly_pattern,s):
    s=re.sub(public_readonly_pattern,public_readonly_tag,s,count=1)
else:
    s=s.replace(driver_experience_tag,driver_experience_tag+'\n'+public_readonly_tag,1)

if re.search(crime_alerts_pattern,s):
    s=re.sub(crime_alerts_pattern,crime_alerts_tag,s,count=1)
else:
    s=s.replace(public_readonly_tag,public_readonly_tag+'\n'+crime_alerts_tag,1)

if re.search(header_profile_pattern,s):
    s=re.sub(header_profile_pattern,header_profile_tag,s,count=1)
else:
    s=s.replace(crime_alerts_tag,crime_alerts_tag+'\n'+header_profile_tag,1)

p.write_text(s,encoding='utf-8')
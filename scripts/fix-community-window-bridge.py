from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
marker = '/* TCV_COMMUNITY_WINDOW_BRIDGE_V1 */'
if marker in s:
    print('Community window bridge already present')
    raise SystemExit(0)

pat = re.compile(r"(let AUTH_MODE='login',SESSION=null,PROFILE=null,[^\n]+;)")
m = pat.search(s)
if not m:
    raise SystemExit('Main app state declaration not found')

bridge = r'''\1
/* TCV_COMMUNITY_WINDOW_BRIDGE_V1 */
window.db=db;
Object.defineProperty(window,'SESSION',{configurable:true,get:()=>SESSION});
Object.defineProperty(window,'PROFILE',{configurable:true,get:()=>PROFILE});
'''
s = pat.sub(bridge, s, count=1)

# Force fresh Community modules in case the browser still has old script responses.
s = re.sub(r'community-safety\.js\?v=\d+', 'community-safety.js?v=2', s, count=1)
s = re.sub(r'community-profile\.js\?v=\d+', 'community-profile.js?v=2', s, count=1)
s = re.sub(r'community-ui-v2\.js\?v=\d+', 'community-ui-v2.js?v=4', s, count=1)

p.write_text(s, encoding='utf-8')
print('Installed Community window bridge and bumped module versions')

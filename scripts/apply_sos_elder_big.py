from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

marker = '/* TCV_SOS_ELDER_BIG_V1 */'
css = r'''
/* TCV_SOS_ELDER_BIG_V1 */
.home-sos-wrap{padding:10px 0 28px!important}
.home-sos-round{
  width:176px!important;
  height:176px!important;
  border-width:8px!important;
  box-shadow:0 18px 42px rgba(183,18,45,.40),inset 0 0 0 3px rgba(255,255,255,.25)!important;
}
.home-sos-icon{font-size:50px!important;margin-bottom:6px!important}
.home-sos-round b{font-size:38px!important;letter-spacing:.055em!important}
.home-sos-round small{font-size:11px!important;letter-spacing:.12em!important;margin-top:8px!important}
@media(max-width:380px){
  .home-sos-round{width:164px!important;height:164px!important}
  .home-sos-icon{font-size:46px!important}
  .home-sos-round b{font-size:35px!important}
}
'''.strip()

if marker in s:
    s = re.sub(r'/\* TCV_SOS_ELDER_BIG_V1 \*/.*?(?=</style>)', css + '\n', s, flags=re.S)
else:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
print('SOS home button enlarged for accessibility')

from pathlib import Path
import re

p=Path('presentazione.html')
s=p.read_text(encoding='utf-8')

replacement='''<div class="phone-stage"><div class="glow"></div><div class="floating f1"><b>4 servizi</b>Spesa · Farmacia<br>Pacco · Altro</div><div class="phone"><div class="phone-screen logo-only"><img src="assets/tcv-splash-logo.jpg" alt="Tanto Ci Vai"></div></div><div class="floating f2"><b>GPS + mappa</b>Ritiro e consegna<br>con punti precisi</div></div></div></section>'''

pat=r'<div class="logo-stage">.*?</div></div></section>'
s2,n=re.subn(pat,replacement,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'hero logo block not found or ambiguous: {n}')

css='''.phone-screen.logo-only{display:grid;place-items:center;background:radial-gradient(circle at 50% 42%,#ffffff 0 28%,#eef7ff 62%,#e7fff8 100%)}.phone-screen.logo-only img{width:78%;height:auto;object-fit:contain;border-radius:34px;box-shadow:0 22px 48px rgba(7,26,61,.14)}\n'''
if '.phone-screen.logo-only{' not in s2:
    s2=s2.replace('</style>',css+'</style>',1)

p.write_text(s2,encoding='utf-8')
print('restored phone mockup with static logo')

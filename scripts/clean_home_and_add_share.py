from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

# 1) Keep the home minimal: remove the blue explanatory hero/stats block.
s, n = re.subn(r'<section class="hero">.*?</section>', '', s, count=1, flags=re.S)
if n != 1 and 'Uno spostamento può aiutare più di una persona.' in s:
    raise SystemExit('Could not remove home hero')

# 2) Put sharing in Profile, away from the Home.
marker = 'TCV_SHARE_PROFILE_V1'
if marker not in s:
    anchor = '<div class="notice green" style="margin-top:10px">✓ Profilo, richieste e missioni sono salvati online in modo sicuro.</div>`}'
    share_card = '<div class="req" style="margin-top:10px"><h3>↗ Condividi Tanto Ci Vai</h3><p>Invita una persona della tua zona a entrare nella rete della comunità.</p><button class="btn teal full" style="margin-top:9px" onclick="tcvShareApp()">Condividi app</button></div>'
    if anchor not in s:
        raise SystemExit('Profile anchor not found')
    s = s.replace(anchor, share_card + anchor, 1)

    fn_anchor = 'async function saveProfile(){'
    share_fn = '''// TCV_SHARE_PROFILE_V1\nasync function tcvShareApp(){\n  const url=location.origin+location.pathname;\n  const data={title:'Tanto ci vai?',text:'Unisciti a Tanto Ci Vai, la rete di aiuto e commissioni della comunità.',url};\n  try{\n    if(navigator.share){await navigator.share(data);return}\n    if(navigator.clipboard){await navigator.clipboard.writeText(url);alert('Link copiato. Ora puoi condividerlo dove vuoi.');return}\n    prompt('Copia questo link:',url)\n  }catch(e){if(e?.name!=='AbortError')console.warn('Share failed',e)}\n}\n'''
    if fn_anchor not in s:
        raise SystemExit('saveProfile anchor not found')
    s = s.replace(fn_anchor, share_fn + fn_anchor, 1)

if s == original:
    print('No changes needed')
else:
    p.write_text(s, encoding='utf-8')
    print('Home cleaned and share moved to Profile')

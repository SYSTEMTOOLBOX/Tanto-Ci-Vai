from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s
marker = '/* TCV_SOS_V4_30S */'

if marker in s:
    print('SOS 30s quick-reasons patch already applied')
    raise SystemExit(0)

css = r'''
/* TCV_SOS_V4_30S */
.sos-presets-title{margin:13px 0 7px;font-size:10px;font-weight:950;letter-spacing:.04em;color:#7e2636;text-align:center}
.sos-presets{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 0 12px}
.sos-preset{border:1px solid #f0c2ca;background:#fff7f8;border-radius:16px;min-height:66px;padding:10px 8px;font-size:22px;text-align:center;color:var(--ink);font-weight:900}
.sos-preset b{display:block;font-size:10px;line-height:1.25;margin-top:4px}.sos-preset:active,.sos-preset.chosen{background:#ffe4e8;border-color:#d74a61;transform:scale(.985)}
@media(max-width:380px){.sos-presets{grid-template-columns:1fr}.sos-preset{min-height:58px}}
'''
if '</style>' not in s:
    raise SystemExit('style close tag not found')
s = s.replace('</style>', css + '</style>', 1)

# Home copy and SOS explanatory text.
s = s.replace('1 tocco · prende il GPS · se non annulli parte automaticamente tra 60 secondi',
              '1 tocco · prende il GPS · se non annulli parte automaticamente tra 30 secondi')
s = s.replace('// TCV SOS V3: one-tap, 60-second automatic fallback, GPS and third-person help.',
              '// TCV SOS V4: one-tap, 30-second automatic fallback, GPS, quick reasons and third-person help.')
s = s.replace("tra un minuto viene inviata la tua posizione agli utenti con le notifiche attive.",
              "tra 30 secondi viene inviata la tua posizione agli utenti con le notifiche attive.")

# Shorter local countdown.
s = s.replace('Date.now()+60000', 'Date.now()+30000')

state_old = "let TCV_SOS_ARMED=false,TCV_SOS_ALERT_ID=null,TCV_SOS_DEADLINE=0,TCV_SOS_TIMER=null,TCV_SOS_POS=null,TCV_SOS_MESSAGE_TIMER=null,TCV_SOS_SENDING=false;"
state_new = "let TCV_SOS_ARMED=false,TCV_SOS_ALERT_ID=null,TCV_SOS_DEADLINE=0,TCV_SOS_TIMER=null,TCV_SOS_POS=null,TCV_SOS_MESSAGE_TIMER=null,TCV_SOS_SENDING=false,TCV_SOS_LAST_AUTO_ATTEMPT=0;"
if state_old not in s:
    raise SystemExit('SOS state anchor not found')
s = s.replace(state_old, state_new, 1)

open_old = "TCV_SOS_ARMED=true;TCV_SOS_ALERT_ID=null;TCV_SOS_POS=null;TCV_SOS_DEADLINE=Date.now()+30000;TCV_SOS_SENDING=false;"
open_new = "TCV_SOS_ARMED=true;TCV_SOS_ALERT_ID=null;TCV_SOS_POS=null;TCV_SOS_DEADLINE=Date.now()+30000;TCV_SOS_SENDING=false;TCV_SOS_LAST_AUTO_ATTEMPT=0;"
if open_old not in s:
    raise SystemExit('SOS open/reset anchor not found')
s = s.replace(open_old, open_new, 1)

# Prevent a failed backend from being hammered every 250 ms; retry automatically every 5 s instead.
tick_old = "if(TCV_SOS_ARMED&&tcvSosSeconds()<=0&&!TCV_SOS_SENDING)tcvSendSosNow(true)"
tick_new = "if(TCV_SOS_ARMED&&tcvSosSeconds()<=0&&!TCV_SOS_SENDING&&Date.now()-TCV_SOS_LAST_AUTO_ATTEMPT>5000){TCV_SOS_LAST_AUTO_ATTEMPT=Date.now();tcvSendSosNow(true)}"
if tick_old not in s:
    raise SystemExit('SOS tick anchor not found')
s = s.replace(tick_old, tick_new, 1)

# Large one-tap reasons while the 30 second fallback remains armed.
field_anchor = '<div class="field"><label>COSA SUCCEDE? · FACOLTATIVO</label><textarea id="sosMessage"'
if field_anchor not in s:
    raise SystemExit('SOS message field anchor not found')
presets = '''<div class="sos-presets-title">SE RIESCI, TOCCA IL MOTIVO · L'SOS PARTE SUBITO</div><div class="sos-presets"><button type="button" class="sos-preset" onclick="tcvSosPreset('Auto in panne / macchina ferma',this)">🚗<b>Auto in panne</b></button><button type="button" class="sos-preset" onclick="tcvSosPreset('Casa allagata / perdita acqua',this)">💧<b>Casa allagata</b></button><button type="button" class="sos-preset" onclick="tcvSosPreset('Malore / mi sento male',this)">❤️<b>Mi sento male</b></button><button type="button" class="sos-preset" onclick="tcvSosPreset('Caduta / mi sono fatto male',this)">🩹<b>Caduta / ferita</b></button><button type="button" class="sos-preset" onclick="tcvSosPreset('Sono bloccato / mi serve una mano',this)">🚪<b>Sono bloccato</b></button><button type="button" class="sos-preset" onclick="tcvSosPreset('Altro aiuto urgente',this)">🆘<b>Altro aiuto</b></button></div>'''
s = s.replace(field_anchor, presets + field_anchor, 1)

fn_anchor = 'function tcvSosMessageChanged(){'
if fn_anchor not in s:
    raise SystemExit('SOS message function anchor not found')
fn = r'''function tcvSosPreset(text,btn){
  if(TCV_SOS_SENDING)return;
  const ta=document.getElementById('sosMessage');if(ta)ta.value=text;
  document.querySelectorAll('.sos-preset').forEach(x=>x.classList.remove('chosen'));if(btn)btn.classList.add('chosen');
  const st=document.getElementById('sosStatus');if(st)st.textContent='🆘 '+text+' · invio immediato…';
  tcvSendSosNow(false)
}
'''
s = s.replace(fn_anchor, fn + fn_anchor, 1)

# If SEND NOW is tapped during the first fraction of a second, allow ARM to return its alert id first.
send_anchor = "async function tcvSendSosNow(automatic=false){\n  if(TCV_SOS_SENDING)return;TCV_SOS_SENDING=true;"
if send_anchor not in s:
    raise SystemExit('SOS send function anchor not found')
send_new = "async function tcvSendSosNow(automatic=false){\n  if(TCV_SOS_SENDING)return;TCV_SOS_SENDING=true;\n  if(!TCV_SOS_ALERT_ID){for(let i=0;i<15&&!TCV_SOS_ALERT_ID&&TCV_SOS_ARMED;i++)await new Promise(r=>setTimeout(r,100));}"
s = s.replace(send_anchor, send_new, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('SOS fixed: 30 seconds, quick reasons, throttled retry and early-send race guard')

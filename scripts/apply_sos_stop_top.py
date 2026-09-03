from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')

css='''\n/* TCV_SOS_STOP_TOP_V1 */\n.sos-stop-top{width:100%;border:0;border-radius:18px;padding:16px 14px;margin:10px 0 12px;background:#fff0f1;color:#a51020;border:3px solid #d92132;font-size:15px;font-weight:950;box-shadow:0 9px 22px rgba(217,33,50,.14)}\n.sos-stop-top:active{transform:scale(.985)}\n'''
if 'TCV_SOS_STOP_TOP_V1' not in text:
    text=text.replace('</style>',css+'\n</style>',1)

# Put the existing pause/report action right at the top of the SOS screen,
# immediately before the countdown, so an accidental SOS can be stopped fast.
needle='<div class="sos-countdown"><strong id="sosSeconds">${sec}</strong><span id="sosCountdownText">secondi prima dell\'invio automatico</span></div>'
insert='<button type="button" class="sos-stop-top" onclick="tcvPauseSosForReport()">✋ FERMA SUBITO IL COUNTDOWN</button>'+needle
if 'class="sos-stop-top" onclick="tcvPauseSosForReport()"' not in text:
    if needle not in text:
        raise SystemExit('SOS countdown anchor not found')
    text=text.replace(needle,insert,1)

# Remove the old copy from the bottom action stack; keep INVIA SUBITO / ANNULLA / other-person help.
old='<div class="sos-big-actions"><button class="sos-pause" onclick="tcvPauseSosForReport()">⏸ FERMA COUNTDOWN / SEGNALA CON CALMA</button><button class="sos-send-now" onclick="tcvSendSosNow(false)">🆘 INVIA SUBITO</button>'
new='<div class="sos-big-actions"><button class="sos-send-now" onclick="tcvSendSosNow(false)">🆘 INVIA SUBITO</button>'
if old in text:
    text=text.replace(old,new,1)
elif '⏸ FERMA COUNTDOWN / SEGNALA CON CALMA' in text:
    text=re.sub(r'<button class="sos-pause" onclick="tcvPauseSosForReport\(\)">⏸ FERMA COUNTDOWN / SEGNALA CON CALMA</button>','',text,count=1)

text=re.sub(r'sw\.js\?v=\d+', 'sw.js?v=7', text)
path.write_text(text,encoding='utf-8')
print('Moved SOS countdown stop control to the top of the SOS screen')

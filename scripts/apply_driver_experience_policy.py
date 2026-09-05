from pathlib import Path
import re


def must_replace(text, old, new, label):
    if old not in text:
        raise SystemExit(f'Missing expected text for {label}')
    return text.replace(old, new, 1)

# 1) Remove the old five-year exclusion while keeping licence validity checks.
p = Path('community-documents.js')
s = p.read_text(encoding='utf-8')
if 'TCV_DRIVER_EXPERIENCE_POLICY_V1' not in s:
    s = s.replace('/* TCV_COMMUNITY_DOCUMENTS_V1 */', '/* TCV_COMMUNITY_DOCUMENTS_V1 */\n/* TCV_DRIVER_EXPERIENCE_POLICY_V1 */', 1)

pattern = re.compile(
    r"  function fiveYearsAfter\(d\)\{.*?  window\.tcvCommunityDriverEligibility=driverEligibility;\n",
    re.S,
)
new_block = r'''  function splitName(v){const p=String(v||'').trim().replace(/\s+/g,' ').split(' ').filter(Boolean);return {first:p.shift()||'',last:p.join(' ')}}
  function typeLabel(t){return t==='driving_license'?'Patente di guida':'Carta d’identità'}

  function licenseExperienceText(bSince){
    const b=parseDateOnly(bSince),today=todayLocal();
    if(!b||b>today)return '';
    let months=(today.getFullYear()-b.getFullYear())*12+(today.getMonth()-b.getMonth());
    if(today.getDate()<b.getDate())months--;
    months=Math.max(0,months);
    if(months===0)return 'meno di 1 mese';
    if(months<12)return `${months} ${months===1?'mese':'mesi'}`;
    const years=Math.floor(months/12),rem=months%12;
    const y=`${years} ${years===1?'anno':'anni'}`;
    return rem?`${y} e ${rem} ${rem===1?'mese':'mesi'}`:y;
  }

  function driverEligibility(bSince,expires){
    const b=parseDateOnly(bSince),exp=parseDateOnly(expires),today=todayLocal();
    if(!b)return {ok:false,reason:'Inserisci la data di conseguimento della categoria B.'};
    if(b>today)return {ok:false,reason:'La data di conseguimento della categoria B non può essere nel futuro.'};
    if(!exp)return {ok:false,reason:'Inserisci la data di scadenza della patente.'};
    if(exp<b)return {ok:false,reason:'La data di scadenza della patente non è valida.'};
    if(exp<today)return {ok:false,reason:`Patente scaduta il ${fmtDate(expires)}. Puoi continuare a usare Tanto Ci Vai come passeggero, ma non come guidatore.`};
    return {ok:true,reason:`✓ Patente valida. Esperienza di guida: ${licenseExperienceText(bSince)}. Scadenza ${fmtDate(expires)}.`};
  }
  window.tcvCommunityDriverEligibility=driverEligibility;
  window.tcvCommunityLicenseExperienceText=licenseExperienceText;
'''

s2, n = pattern.subn(new_block, s, count=1)
if n != 1:
    raise SystemExit('Could not replace old five-year driver eligibility block')
s = s2
s = must_replace(
    s,
    'Patente obbligatoria e almeno 5 anni dalla categoria B.',
    'Patente B valida obbligatoria. Gli altri utenti vedranno da quanto tempo guidi.',
    'driver role copy',
)
s = must_replace(
    s,
    "${docType==='driving_license'?'<br>✓ Requisito minimo di 5 anni e scadenza controllati.':''}",
    "${docType==='driving_license'?'<br>✓ Patente valida e anzianità di guida registrata.':''}",
    'document save success copy',
)
s = must_replace(
    s,
    "body=`Patente registrata · B dal ${esc(fmtDate(doc.license_b_since))} · scadenza ${esc(fmtDate(doc.license_expires_on))}.<br>${esc(chk.reason)}`;",
    "body=`Patente registrata · ${esc(licenseExperienceText(doc.license_b_since))} di esperienza · scadenza ${esc(fmtDate(doc.license_expires_on))}.`;",
    'profile licence summary',
)
p.write_text(s, encoding='utf-8')

# 2) Remove the five-year wording from the role-selection overlay.
p = Path('community-registration-gates.js')
s = p.read_text(encoding='utf-8')
s = s.replace('/* TCV_COMMUNITY_REGISTRATION_GATES_V1', '/* TCV_COMMUNITY_REGISTRATION_GATES_V1\n   TCV_DRIVER_EXPERIENCE_POLICY_V1', 1)
s = must_replace(
    s,
    "driver.querySelector('small').textContent='Puoi offrire e ricevere passaggi. Patente obbligatoria e almeno 5 anni dalla categoria B.';",
    "driver.querySelector('small').textContent='Puoi offrire e ricevere passaggi. Patente B valida obbligatoria; mostriamo da quanto tempo guidi.';",
    'registration driver copy',
)
p.write_text(s, encoding='utf-8')

# 3) Force a fresh load of the modified document module.
p = Path('community-ui-v2.js')
s = p.read_text(encoding='utf-8')
s = must_replace(s, "s.src='./community-documents.js?v=2';", "s.src='./community-documents.js?v=3';", 'community documents cache version')
p.write_text(s, encoding='utf-8')

# 4) Wire all current Community scripts into index.html using the canonical helper.
exec(Path('scripts/apply_community_ui_v2.py').read_text(encoding='utf-8'), {'__name__':'__main__'})

print('Driver experience policy applied')
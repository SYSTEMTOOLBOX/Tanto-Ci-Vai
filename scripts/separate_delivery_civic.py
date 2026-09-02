from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
MARK='DELIVERY_CIVIC_SEPARATE_V1'
if MARK in s:
    print('already applied')
    raise SystemExit(0)

old='<div class="field autocomplete-wrap"><label>VIA E NUMERO CIVICO</label><input id="nrStreet" value="" placeholder="Es. Via Anselmina 14/A" autocomplete="off" oninput="deliveryStreetChanged()"><div id="deliveryStreetSuggest" class="autocomplete-box"></div></div>'
new='<div class="field autocomplete-wrap"><label>VIA</label><input id="nrStreet" value="" placeholder="Es. Via Anselmina" autocomplete="off" oninput="deliveryStreetChanged()"><div id="deliveryStreetSuggest" class="autocomplete-box"></div></div><div class="field"><label>NUMERO CIVICO</label><input id="nrCivic" value="" placeholder="Es. 14/A" autocomplete="off" inputmode="text" oninput="deliveryCivicChanged()"><div class="notice" style="margin-top:7px">Mappa e GPS compilano il civico automaticamente quando disponibile.</div></div>'
if old not in s: raise SystemExit('delivery field anchor not found')
s=s.replace(old,new,1)

js=r'''
/* DELIVERY_CIVIC_SEPARATE_V1 */
function deliveryStreetParts(pt){
  const raw=pt?.raw||{};
  const civic=String(raw.housenumber||raw.house_number||pt?.civic||'').trim();
  let street=String(raw.street||raw.road||raw.pedestrian||raw.path||pt?.street||pt?.name||'').trim();
  if(civic&&street.toLowerCase().endsWith((' '+civic).toLowerCase())) street=street.slice(0,-civic.length).trim();
  return {street,civic};
}
function deliveryCivicChanged(){HOME_POS=null;document.getElementById('deliveryPicked')?.classList.add('hidden')}
const _tcvReverseDeliveryPoint=reverseDeliveryPoint;
reverseDeliveryPoint=async function(pos){
  const pt=await _tcvReverseDeliveryPoint(pos),parts=deliveryStreetParts(pt),c=document.getElementById('nrCivic');
  if(c)c.value=parts.civic||'';
  return {...pt,street:parts.street,civic:parts.civic};
};
const _tcvChooseDeliveryStreet=chooseDeliveryStreet;
chooseDeliveryStreet=async function(i){
  const pt=DELIVERY_STREET_RESULTS[i],parts=deliveryStreetParts(pt);
  await _tcvChooseDeliveryStreet(i);
  const st=document.getElementById('nrStreet'),cv=document.getElementById('nrCivic'),city=document.getElementById('nrCity');
  if(st&&parts.street)st.value=parts.street;if(cv&&parts.civic)cv.value=parts.civic;
  if(HOME_POS){const full=[st?.value||parts.street,cv?.value||parts.civic].filter(Boolean).join(' ');HOME_POS={...HOME_POS,street:full,streetText:st?.value||parts.street,civicText:cv?.value||parts.civic,label:canonicalDeliveryLabel(full,city?.value||HOME_POS.city)}}
  showPickedDelivery(HOME_POS||pt);if(cv&&!cv.value)cv.focus();
};
showPickedDelivery=function(pt){
  const el=document.getElementById('deliveryPicked');if(!el||!pt)return;
  const city=pt.cityText||document.getElementById('nrCity')?.value||pt.city;
  const parts=deliveryStreetParts(pt),street=pt.streetText||document.getElementById('nrStreet')?.value||parts.street,civic=pt.civicText||document.getElementById('nrCivic')?.value||parts.civic;
  el.classList.remove('hidden');el.innerHTML=`✓ Destinazione impostata<br><b>${esc(canonicalDeliveryLabel([street,civic].filter(Boolean).join(' '),city))}</b>`;
};
const _tcvPublishRequest=publishRequest;
publishRequest=async function(){
  const st=document.getElementById('nrStreet'),cv=document.getElementById('nrCivic'),status=document.getElementById('nrStatus');
  const base=st?.value.trim()||'',civic=cv?.value.trim()||'';
  if(!civic){if(status)status.textContent='Inserisci il numero civico di consegna.';cv?.focus();return}
  if(st)st.value=[base,civic].filter(Boolean).join(' ');
  try{return await _tcvPublishRequest()}finally{if(st)st.value=base}
};
'''
pos=s.rfind('</script>')
if pos<0: raise SystemExit('script close not found')
s=s[:pos]+js+'\n'+s[pos:]
p.write_text(s,encoding='utf-8')
print('delivery street/civic separated')

from pathlib import Path
import re

p = Path('community-routes.js')
s = p.read_text(encoding='utf-8')

if 'TCV_TWO_STAGE_LOCATION_V1' not in s:
    s = s.replace('/* TCV_COMMUNITY_ROUTES_V1', '/* TCV_COMMUNITY_ROUTES_V1\n   TCV_TWO_STAGE_LOCATION_V1', 1)

# Extra UI styles for Comune -> Via/Piazza/Luogo and route-name labels on the map.
css_anchor = "      .tcv-autowrap{position:relative}.tcv-autobox{display:grid;gap:5px;margin-top:5px}.tcv-autoitem{width:100%;border:1px solid #dfe8f4;background:#fff;border-radius:12px;padding:10px 11px;text-align:left;color:#0b1834;font-size:10px;line-height:1.35}.tcv-autoitem b{display:block;font-size:11px}.tcv-autoitem small{display:block;color:#6c7891;margin-top:2px}\n"
css_new = css_anchor + "      .tcv-place-block{padding:10px;border:1px solid #dfe8f4;border-radius:17px;background:#fbfdff;margin:9px 0}.tcv-place-block .field{margin-bottom:8px}.tcv-place-block .field:last-child{margin-bottom:0}.tcv-place-step{display:inline-block;font-size:8px;font-weight:950;color:#0b66ff;background:#eaf3ff;border-radius:999px;padding:4px 7px;margin-bottom:5px}.tcv-route-name{background:#0b1834!important;color:#fff!important;border:0!important;border-radius:999px!important;padding:4px 8px!important;font-size:9px!important;font-weight:900!important;box-shadow:0 2px 8px rgba(11,24,52,.22)!important}.tcv-route-name:before{display:none!important}\n"
if '.tcv-place-block{' not in s:
    if css_anchor not in s:
        raise SystemExit('CSS autocomplete anchor not found')
    s = s.replace(css_anchor, css_new, 1)

# Add helpers after clearBox. They keep municipality selection separate from the exact local address.
helper_anchor = "  function clearBox(id){const b=document.getElementById(id);if(b)b.innerHTML=''}\n"
helpers = r'''  function clearBox(id){const b=document.getElementById(id);if(b)b.innerHTML=''}
  function tcvPlaceDetail(pt){
    const label=String(pt?.label||'').trim(),town=tcvTownFromPoint(pt);if(!label)return '';
    const first=label.split(',')[0].trim();
    if(tcvTownNorm(first)===tcvTownNorm(town))return '';
    return first.replace(/\s*·\s*.*$/,'').trim()
  }
  function tcvSeedTownInput(townId,placeId,pt){
    const townEl=document.getElementById(townId),placeEl=document.getElementById(placeId);if(!townEl)return;
    const town=tcvTownFromPoint(pt);if(town)townEl.value=town;
    if(pt&&Number.isFinite(Number(pt.lat))&&Number.isFinite(Number(pt.lng))){townEl.dataset.lat=String(pt.lat);townEl.dataset.lng=String(pt.lng)}
    townEl.dataset.town=town||'';if(placeEl)placeEl.disabled=!town
  }
  function tcvTownPointFromInput(townId){
    const el=document.getElementById(townId);if(!el)return null;
    const town=String(el.dataset.town||el.value||'').trim(),lat=Number(el.dataset.lat),lng=Number(el.dataset.lng);
    if(!town)return null;
    return {lat:Number.isFinite(lat)?lat:NaN,lng:Number.isFinite(lng)?lng:NaN,label:town,town}
  }
  function tcvTownRows(fs,q){
    const wanted=tcvTownNorm(q),seen=new Set(),out=[];
    for(const f of (Array.isArray(fs)?fs:[])){
      const raw=tcvFeatureTown(f)||String(featureLabel(f)||'').split(',')[0]||'',town=String(raw).trim();if(!town)continue;
      const norm=tcvTownNorm(town);if(wanted&&!(norm.includes(wanted)||wanted.includes(norm)))continue;if(seen.has(norm))continue;seen.add(norm);
      const p=featurePoint(f);if(!Number.isFinite(p.lat)||!Number.isFinite(p.lng))continue;p.town=town;p.label=town;
      out.push({f,p,town,sub:featureSub(f)});if(out.length>=8)break
    }
    return out
  }
  function bindTownAutocomplete(townId,boxId,placeId,placeBoxId,key,target='trip'){
    const input=document.getElementById(townId),place=document.getElementById(placeId);if(!input)return;
    input.setAttribute('autocomplete','off');
    input.addEventListener('input',()=>{
      const state=target==='trip'?draft:rideDraft;state[key]=null;delete input.dataset.lat;delete input.dataset.lng;delete input.dataset.town;
      if(place){place.value='';place.disabled=true}clearBox(placeBoxId);clearTimeout(searchTimers[townId]);
      const q=input.value.trim();if(q.length<2){clearBox(boxId);return}
      searchTimers[townId]=setTimeout(async()=>{
        const box=document.getElementById(boxId);if(!box)return;box.innerHTML='<div class="notice">Cerco il comune…</div>';
        try{
          const rows=tcvTownRows(await photon(q,14,null),q);
          box.innerHTML=rows.length?rows.map((r,i)=>`<button type="button" class="tcv-autoitem" data-i="${i}"><b>📍 ${safe(r.town)}</b><small>${safe(r.sub||'Italia')}</small></button>`).join(''):'<div class="notice yellow">Comune non trovato. Continua a scrivere il nome completo.</div>';
          box.querySelectorAll('button[data-i]').forEach(btn=>btn.addEventListener('pointerdown',ev=>{ev.preventDefault();const r=rows[Number(btn.dataset.i)];if(!r)return;
            input.value=r.town;input.dataset.town=r.town;input.dataset.lat=String(r.p.lat);input.dataset.lng=String(r.p.lng);state[key]=r.p;clearBox(boxId);
            if(place){place.disabled=false;place.focus()}
            if(target==='trip')tcvMaybeAutoPreview();else tcvMaybeRidePreview()
          }))
        }catch(e){console.warn('community town autocomplete',e);box.innerHTML='<div class="notice yellow">Ricerca comune momentaneamente lenta.</div>'}
      },220)
    })
  }
  function bindLocalAutocomplete(townId,inputId,boxId,key,target='trip'){
    const input=document.getElementById(inputId);if(!input)return;input.setAttribute('autocomplete','off');
    input.addEventListener('input',()=>{
      const state=target==='trip'?draft:rideDraft;state[key]=null;clearTimeout(searchTimers[inputId]);const q=input.value.trim();
      const townPt=tcvTownPointFromInput(townId),town=townPt?.town||'';
      if(!town){const box=document.getElementById(boxId);if(box)box.innerHTML='<div class="notice yellow">Prima scegli il comune.</div>';return}
      if(q.length<2){clearBox(boxId);state[key]=townPt;if(target==='trip')tcvMaybeAutoPreview();else tcvMaybeRidePreview();return}
      searchTimers[inputId]=setTimeout(async()=>{
        const box=document.getElementById(boxId);if(!box)return;box.innerHTML=`<div class="notice">Cerco solo dentro <b>${safe(town)}</b>…</div>`;
        try{
          const wanted=tcvTownNorm(town),raw=await photon(q,14,townPt);
          const fs=(Array.isArray(raw)?raw:[]).filter(f=>{const got=tcvTownNorm(tcvFeatureTown(f));return got&&(got===wanted||got.includes(wanted)||wanted.includes(got))});
          box.innerHTML=fs.length?fs.slice(0,8).map((f,i)=>`<button type="button" class="tcv-autoitem" data-i="${i}"><b>${safe(featureLabel(f)||q)}</b><small>${safe(featureSub(f))}</small></button>`).join(''):`<div class="notice yellow">Nessun risultato in ${safe(town)}. Prova con un nome più completo.</div>`;
          box.querySelectorAll('button[data-i]').forEach(btn=>btn.addEventListener('pointerdown',ev=>{ev.preventDefault();const f=fs[Number(btn.dataset.i)],p=featurePoint(f);if(!Number.isFinite(p.lat)||!Number.isFinite(p.lng))return;
            input.value=tcvPlaceDetail(p)||featureLabel(f)||q;state[key]=p;clearBox(boxId);if(target==='trip')tcvMaybeAutoPreview();else tcvMaybeRidePreview()
          }))
        }catch(e){console.warn('community local autocomplete',e);box.innerHTML=`<div class="notice yellow">Ricerca indirizzo lenta. Il comune resta ${safe(town)}.</div>`}
      },220)
    })
  }
  async function resolvePlace(townId,inputId,key,target='trip'){
    const state=target==='trip'?draft:rideDraft,place=String(document.getElementById(inputId)?.value||'').trim();
    if(state[key]&&Number.isFinite(Number(state[key].lat))&&place)return state[key];
    const townPt=tcvTownPointFromInput(townId);if(!townPt)throw new Error('Prima scegli il comune di partenza e di destinazione.');
    if(!place){state[key]=townPt;return townPt}
    const wanted=tcvTownNorm(townPt.town),fs=await photon(place,12,townPt),exact=(Array.isArray(fs)?fs:[]).filter(f=>{const got=tcvTownNorm(tcvFeatureTown(f));return got&&(got===wanted||got.includes(wanted)||wanted.includes(got))});
    if(!exact.length)throw new Error(`Non trovo “${place}” nel comune di ${townPt.town}.`);
    const p=featurePoint(exact[0]);state[key]=p;document.getElementById(inputId).value=tcvPlaceDetail(p)||featureLabel(exact[0]);return p
  }
'''
if 'function bindTownAutocomplete' not in s:
    if helper_anchor not in s:
        raise SystemExit('clearBox anchor not found')
    s = s.replace(helper_anchor, helpers, 1)

# Keep old generic autocomplete available but move the main Community UI to the strict two-step flow.
trip_from_old = '''<div class="field tcv-autowrap"><label>DA DOVE PARTI · CITTÀ / VIA / PIAZZA / LUOGO</label><input id="tcvTripFrom" value="${safe(t?.from_label||'')}" placeholder="Es. Via Roma 12, Lauriano"><div id="tcvTripFromBox" class="tcv-autobox"></div></div>'''
trip_from_new = '''<div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI PARTENZA</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="tcvTripFromTown" value="${safe(tcvTownFromPoint(draft.from))}" placeholder="Es. Lauriano"><div id="tcvTripFromTownBox" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="tcvTripFrom" value="${safe(tcvPlaceDetail(draft.from))}" placeholder="Es. Piazza Risorgimento" ${tcvTownFromPoint(draft.from)?'':'disabled'}><div id="tcvTripFromBox" class="tcv-autobox"></div></div></div>'''
trip_to_old = '''<div class="field tcv-autowrap"><label>DOVE VAI · CITTÀ / VIA / PIAZZA / LUOGO</label><input id="tcvTripTo" value="${safe(t?.to_label||'')}" placeholder="Es. Piazza d'Armi, Chivasso"><div id="tcvTripToBox" class="tcv-autobox"></div></div>'''
trip_to_new = '''<div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI DESTINAZIONE</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="tcvTripToTown" value="${safe(tcvTownFromPoint(draft.to))}" placeholder="Es. Saluggia"><div id="tcvTripToTownBox" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="tcvTripTo" value="${safe(tcvPlaceDetail(draft.to))}" placeholder="Es. Via Roma" ${tcvTownFromPoint(draft.to)?'':'disabled'}><div id="tcvTripToBox" class="tcv-autobox"></div></div></div>'''
if trip_from_old in s:s=s.replace(trip_from_old,trip_from_new,1)
if trip_to_old in s:s=s.replace(trip_to_old,trip_to_new,1)

trip_bind_old = "setTimeout(()=>{bindAutocomplete('tcvTripFrom','tcvTripFromBox','from','trip');bindAutocomplete('tcvTripTo','tcvTripToBox','to','trip')},0)"
trip_bind_new = "setTimeout(()=>{tcvSeedTownInput('tcvTripFromTown','tcvTripFrom',draft.from);tcvSeedTownInput('tcvTripToTown','tcvTripTo',draft.to);bindTownAutocomplete('tcvTripFromTown','tcvTripFromTownBox','tcvTripFrom','tcvTripFromBox','from','trip');bindLocalAutocomplete('tcvTripFromTown','tcvTripFrom','tcvTripFromBox','from','trip');bindTownAutocomplete('tcvTripToTown','tcvTripToTownBox','tcvTripTo','tcvTripToBox','to','trip');bindLocalAutocomplete('tcvTripToTown','tcvTripTo','tcvTripToBox','to','trip')},0)"
if trip_bind_old in s:s=s.replace(trip_bind_old,trip_bind_new,1)

s=s.replace("resolveInput('tcvTripFrom','from','trip')","resolvePlace('tcvTripFromTown','tcvTripFrom','from','trip')")
s=s.replace("resolveInput('tcvTripTo','to','trip')","resolvePlace('tcvTripToTown','tcvTripTo','to','trip')")

trip_gps_old = "draft.from=pt;const el=document.getElementById('tcvTripFrom');if(el)el.value=pt.label;clearBox('tcvTripFromBox');if(st)st.textContent='✓ Partenza compilata automaticamente dal GPS.'"
trip_gps_new = "draft.from=pt;tcvSeedTownInput('tcvTripFromTown','tcvTripFrom',pt);const el=document.getElementById('tcvTripFrom');if(el)el.value=tcvPlaceDetail(pt);clearBox('tcvTripFromTownBox');clearBox('tcvTripFromBox');if(st)st.textContent='✓ Comune e punto di partenza compilati automaticamente dal GPS.'"
if trip_gps_old in s:s=s.replace(trip_gps_old,trip_gps_new,1)

ride_from_old = '''<div class="field tcv-autowrap"><label>DA DOVE PARTI · CITTÀ / VIA / PIAZZA / LUOGO</label><input id="rideFrom" value="${safe(rideDraft.from?.label||'')}" placeholder="Es. Via Roma 12, Lauriano"><div id="rideFromAuto" class="tcv-autobox"></div></div>'''
ride_from_new = '''<div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI PARTENZA</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="rideFromTown" value="${safe(tcvTownFromPoint(rideDraft.from))}" placeholder="Es. Lauriano"><div id="rideFromTownAuto" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="rideFrom" value="${safe(tcvPlaceDetail(rideDraft.from))}" placeholder="Es. Piazza Risorgimento" ${tcvTownFromPoint(rideDraft.from)?'':'disabled'}><div id="rideFromAuto" class="tcv-autobox"></div></div></div>'''
ride_to_old = '''<div class="field tcv-autowrap"><label>DOVE DEVI ANDARE · CITTÀ / VIA / PIAZZA / LUOGO</label><input id="rideTo" value="${safe(rideDraft.to?.label||'')}" placeholder="Es. Piazza d'Armi, Chivasso"><div id="rideToAuto" class="tcv-autobox"></div></div>'''
ride_to_new = '''<div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI DESTINAZIONE</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="rideToTown" value="${safe(tcvTownFromPoint(rideDraft.to))}" placeholder="Es. Saluggia"><div id="rideToTownAuto" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="rideTo" value="${safe(tcvPlaceDetail(rideDraft.to))}" placeholder="Es. Via Roma" ${tcvTownFromPoint(rideDraft.to)?'':'disabled'}><div id="rideToAuto" class="tcv-autobox"></div></div></div>'''
if ride_from_old in s:s=s.replace(ride_from_old,ride_from_new,1)
if ride_to_old in s:s=s.replace(ride_to_old,ride_to_new,1)

ride_bind_old = "setTimeout(()=>{bindAutocomplete('rideFrom','rideFromAuto','from','ride');bindAutocomplete('rideTo','rideToAuto','to','ride')},0)"
ride_bind_new = "setTimeout(()=>{tcvSeedTownInput('rideFromTown','rideFrom',rideDraft.from);tcvSeedTownInput('rideToTown','rideTo',rideDraft.to);bindTownAutocomplete('rideFromTown','rideFromTownAuto','rideFrom','rideFromAuto','from','ride');bindLocalAutocomplete('rideFromTown','rideFrom','rideFromAuto','from','ride');bindTownAutocomplete('rideToTown','rideToTownAuto','rideTo','rideToAuto','to','ride');bindLocalAutocomplete('rideToTown','rideTo','rideToAuto','to','ride')},0)"
if ride_bind_old in s:s=s.replace(ride_bind_old,ride_bind_new,1)

s=s.replace("resolveInput('rideFrom','from','ride')","resolvePlace('rideFromTown','rideFrom','from','ride')")
s=s.replace("resolveInput('rideTo','to','ride')","resolvePlace('rideToTown','rideTo','to','ride')")

ride_gps_old = "rideDraft.from=pt;const el=document.getElementById('rideFrom');if(el)el.value=pt.label;clearBox('rideFromAuto');if(st)st.textContent='✓ Partenza compilata automaticamente dal GPS.'"
ride_gps_new = "rideDraft.from=pt;tcvSeedTownInput('rideFromTown','rideFrom',pt);const el=document.getElementById('rideFrom');if(el)el.value=tcvPlaceDetail(pt);clearBox('rideFromTownAuto');clearBox('rideFromAuto');if(st)st.textContent='✓ Comune e punto di partenza compilati automaticamente dal GPS.'"
if ride_gps_old in s:s=s.replace(ride_gps_old,ride_gps_new,1)

# Make the traveller name explicit in the route popup and visible directly on the line.
s=s.replace("<div class=\"row\">👤 ${safe(t.driver_name||'Utente')} · 👥 ${Number(t.seats||1)} posti</div>","<div class=\"row\">👤 <b>Viaggiatore: ${safe(t.driver_name||'Utente')}</b> · 👥 ${Number(t.seats||1)} posti</div>")
old_tooltip = "line.bindTooltip(`${safe(t.from_label)} → ${safe(t.to_label)} · ${money(num(t.distance_km)*RATE_PER_KM)}/persona`,{sticky:true})"
new_tooltip = "line.bindTooltip(`👤 ${safe(t.driver_name||'Utente')}`,{permanent:true,direction:'center',opacity:.92,className:'tcv-route-name'})"
if old_tooltip in s:s=s.replace(old_tooltip,new_tooltip,1)

p.write_text(s, encoding='utf-8')

idx=Path('index.html')
html=idx.read_text(encoding='utf-8')
html2=re.sub(r'community-routes\.js\?v=\d+', 'community-routes.js?v=5', html, count=1)
if html2==html and 'community-routes.js?v=5' not in html:
    raise SystemExit('community-routes script tag not found')
idx.write_text(html2,encoding='utf-8')

print('Community location flow upgraded: Comune first, then local address; traveller name shown on active map routes')

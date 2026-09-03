/* TCV_COMMUNITY_ROUTES_V1
   TCV_TWO_STAGE_LOCATION_V1
   Community car-pooling: recurring routes, full place autocomplete,
   transparent €0.35/km/person contribution and active routes on safety map.
*/
(function(){
  'use strict';

  const RATE_PER_KM=0.35;
  const PLATFORM_FEE=0.50;
  const DAY_DEFS=[
    ['mon','Lunedì',1],['tue','Martedì',2],['wed','Mercoledì',3],['thu','Giovedì',4],
    ['fri','Venerdì',5],['sat','Sabato',6],['sun','Domenica',0]
  ];
  const DEFAULT_SCHEDULE={
    mon:{enabled:true,out:'07:30',back:'17:30'},
    tue:{enabled:true,out:'07:30',back:'17:30'},
    wed:{enabled:true,out:'07:30',back:'17:30'},
    thu:{enabled:true,out:'07:30',back:'17:30'},
    fri:{enabled:true,out:'07:30',back:'17:30'},
    sat:{enabled:false,out:'09:00',back:'18:00'},
    sun:{enabled:false,out:'09:00',back:'18:00'}
  };

  let TRIPS=[];
  let draft={from:null,to:null,route:null};
  let rideDraft={from:null,to:null,tripId:null,route:null};
  let searchTimers={};
  let realtimeChannel=null;

  function money(v){return new Intl.NumberFormat('it-IT',{style:'currency',currency:'EUR'}).format(Number(v)||0)}
  function num(v){const n=Number(v);return Number.isFinite(n)?n:0}
  function safe(v){try{return esc(v)}catch(e){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}}
  function daySchedule(s,k){return (s&&typeof s==='object'&&s[k])?s[k]:DEFAULT_SCHEDULE[k]}

  function injectStyles(){
    if(document.getElementById('tcvCommunityRoutesCss'))return;
    const st=document.createElement('style');st.id='tcvCommunityRoutesCss';st.textContent=`
      .tcv-route-hero{padding:15px;border-radius:18px;background:#eef6ff;border:1px solid #d6e6ff;margin:10px 0 12px}
      .tcv-route-hero b{display:block;font-size:15px;color:#0b66ff}.tcv-route-hero span{display:block;font-size:10px;line-height:1.45;color:#5d6d88;margin-top:4px}
      .tcv-autowrap{position:relative}.tcv-autobox{display:grid;gap:5px;margin-top:5px}.tcv-autoitem{width:100%;border:1px solid #dfe8f4;background:#fff;border-radius:12px;padding:10px 11px;text-align:left;color:#0b1834;font-size:10px;line-height:1.35}.tcv-autoitem b{display:block;font-size:11px}.tcv-autoitem small{display:block;color:#6c7891;margin-top:2px}
      .tcv-place-block{padding:10px;border:1px solid #dfe8f4;border-radius:17px;background:#fbfdff;margin:9px 0}.tcv-place-block .field{margin-bottom:8px}.tcv-place-block .field:last-child{margin-bottom:0}.tcv-place-step{display:inline-block;font-size:8px;font-weight:950;color:#0b66ff;background:#eaf3ff;border-radius:999px;padding:4px 7px;margin-bottom:5px}.tcv-route-name{background:#0b1834!important;color:#fff!important;border:0!important;border-radius:999px!important;padding:4px 8px!important;font-size:9px!important;font-weight:900!important;box-shadow:0 2px 8px rgba(11,24,52,.22)!important}.tcv-route-name:before{display:none!important}
      .tcv-price-card{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.tcv-price-card>div{padding:12px;border-radius:15px;background:#f7faff;border:1px solid #e1eaf6}.tcv-price-card small{display:block;color:#6c7891;font-size:8px;font-weight:900}.tcv-price-card b{display:block;font-size:17px;margin-top:3px}
      .tcv-calendar{display:grid;gap:7px;margin:10px 0}.tcv-day{display:grid;grid-template-columns:88px 1fr 1fr;gap:7px;align-items:center;border:1px solid #dfe8f4;border-radius:14px;padding:9px;background:#fff}.tcv-day.off{opacity:.5}.tcv-day-name{display:flex;align-items:center;gap:6px;font-size:9px;font-weight:950}.tcv-day-name input{width:18px;height:18px;margin:0}.tcv-day-time label{display:block;font-size:7px;color:#6c7891;font-weight:900;margin-bottom:3px}.tcv-day-time input{padding:8px;font-size:12px}
      .tcv-mytrips{display:grid;gap:8px;margin:10px 0 14px}.tcv-tripcard{padding:13px;border:1px solid #dfe8f4;border-radius:17px;background:#fff}.tcv-tripcard.active{border-color:#9bdccb;background:#f3fff9}.tcv-triphead{display:flex;justify-content:space-between;gap:8px;align-items:center}.tcv-triphead strong{font-size:10px}.tcv-triphead span{font-size:8px;padding:5px 7px;border-radius:999px;background:#eef4ff;color:#0b66ff;font-weight:950}.tcv-tripcard.active .tcv-triphead span{background:#dcfff1;color:#08785f}.tcv-tripcard h3{font-size:14px;margin:8px 0 4px}.tcv-tripcard p{font-size:9px;color:#6c7891;line-height:1.45;margin:0}.tcv-tripactions{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:9px}.tcv-tripactions button{border:1px solid #dfe8f4;background:#fff;border-radius:11px;padding:9px 6px;font-size:8px;font-weight:900}.tcv-tripactions .toggle{background:#0b66ff;color:#fff;border-color:#0b66ff}.tcv-tripcard.active .tcv-tripactions .toggle{background:#fff0f1;color:#9c2534;border-color:#f1c6cb}
      .tcv-route-preview{padding:12px;border-radius:15px;background:#effff8;border:1px solid #d0efdf;font-size:10px;line-height:1.5;color:#285f4c;margin-top:8px}.tcv-route-preview strong{font-size:15px;color:#0b1834}
      .tcv-map-route-key{display:inline-flex;align-items:center;gap:5px}.tcv-map-route-line{display:inline-block;width:22px;height:4px;border-radius:99px;background:#0b66ff}
      .tcv-map-popup{min-width:210px}.tcv-map-popup b{display:block;font-size:13px;margin-bottom:5px}.tcv-map-popup .row{font-size:10px;line-height:1.45;margin-top:4px}.tcv-map-popup button{width:100%;border:0;border-radius:10px;background:#0b66ff;color:#fff;padding:9px;margin-top:8px;font-weight:900;font-size:9px}
      .tcv-ride-price{padding:12px;border-radius:15px;background:#fff8df;border:1px solid #f4dda0;font-size:10px;line-height:1.5;margin:9px 0}
      @media(max-width:420px){.tcv-day{grid-template-columns:80px 1fr 1fr;gap:5px;padding:8px}.tcv-day-time input{padding:7px 5px}.tcv-tripactions{grid-template-columns:1fr 1fr}.tcv-tripactions button:last-child{grid-column:1/-1}}
    `;document.head.appendChild(st)
  }

  function featureLabel(f){
    const p=f?.properties||{};
    const first=[p.name,p.street].filter(Boolean).join(' · ');
    const civic=p.housenumber?` ${p.housenumber}`:'';
    const town=p.city||p.town||p.village||p.locality||p.county||'';
    const parts=[];
    if(first)parts.push(first+civic);else if(p.street)parts.push(p.street+civic);
    if(town&&!parts.some(x=>x===town))parts.push(town);
    if(p.state)parts.push(p.state);
    if(!parts.length&&p.country)parts.push(p.country);
    return parts.join(', ')
  }
  function featureSub(f){const p=f?.properties||{};return [p.postcode,p.county,p.country].filter(Boolean).join(' · ')}
  function featurePoint(f){
    const c=f?.geometry?.coordinates||[],p=f?.properties||{};
    const town=p.city||p.town||p.village||p.municipality||p.locality||'';
    return {lat:Number(c[1]),lng:Number(c[0]),label:featureLabel(f),town}
  }
  function tcvAddressLike(q){return /^(via|viale|vicolo|piazza|piazzale|p\.?le|corso|strada|borgata|frazione|largo|localita|località)\b/i.test(String(q||'').trim())}
  function tcvTownNorm(v){return String(v||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'')}
  function tcvTownFromPoint(pt){
    if(pt?.town)return String(pt.town).trim();
    const parts=String(pt?.label||'').split(',').map(x=>x.trim()).filter(Boolean);
    if(parts.length>1&&tcvAddressLike(parts[0]))return parts[1];
    return parts[0]||''
  }
  function tcvFeatureTown(f){const p=f?.properties||{};return p.city||p.town||p.village||p.municipality||p.locality||''}
  function tcvPointDistanceKm(a,b){
    if(!a||!b||!Number.isFinite(Number(a.lat))||!Number.isFinite(Number(a.lng))||!Number.isFinite(Number(b.lat))||!Number.isFinite(Number(b.lng)))return Infinity;
    const R=6371,toRad=x=>Number(x)*Math.PI/180,dLat=toRad(Number(b.lat)-Number(a.lat)),dLng=toRad(Number(b.lng)-Number(a.lng));
    const la1=toRad(a.lat),la2=toRad(b.lat),h=Math.sin(dLat/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dLng/2)**2;
    return 2*R*Math.asin(Math.sqrt(h))
  }

  function tcvNominatimFeature(x){
    const a=x?.address||{};
    const city=a.city||a.town||a.village||a.municipality||a.hamlet||a.locality||'';
    const street=a.road||a.pedestrian||a.residential||a.footway||a.path||'';
    const name=x?.name||street||city||String(x?.display_name||'').split(',')[0]||'';
    return {
      type:'Feature',
      properties:{
        name,
        street,
        housenumber:a.house_number||'',
        city,
        town:a.town||'',
        village:a.village||'',
        locality:a.locality||a.suburb||a.neighbourhood||'',
        county:a.county||'',
        state:a.state||'',
        postcode:a.postcode||'',
        country:a.country||'Italia',
        countrycode:'IT'
      },
      geometry:{type:'Point',coordinates:[Number(x?.lon),Number(x?.lat)]}
    };
  }

  async function photon(q,limit=6,anchor=null){
    const query=String(q||'').trim();if(query.length<2)return [];
    const anchorTown=(!query.includes(',')&&tcvAddressLike(query))?tcvTownFromPoint(anchor):'';
    const searches=anchorTown?[`${query}, ${anchorTown}`,query]:[query];

    const localFilter=(fs,isLocal)=>{
      const rows=Array.isArray(fs)?fs.filter(Boolean):[];if(!isLocal||!anchorTown)return rows;
      const wanted=tcvTownNorm(anchorTown);
      const same=rows.filter(f=>{const got=tcvTownNorm(tcvFeatureTown(f));return got&&(got===wanted||got.includes(wanted)||wanted.includes(got))});
      if(same.length)return same;
      if(anchor){
        const near=rows.filter(f=>tcvPointDistanceKm(anchor,featurePoint(f))<=25);
        if(near.length)return near;
      }
      return [];
    };

    for(let attempt=0;attempt<searches.length;attempt++){
      const candidate=searches[attempt],isLocal=!!anchorTown&&attempt===0;

      try{
        if(typeof nominatimDeliverySearch==='function'){
          const ns=await nominatimDeliverySearch(candidate,Math.max(limit,8));
          const fs=localFilter((Array.isArray(ns)?ns:[]).map(tcvNominatimFeature).filter(f=>Number.isFinite(f.geometry.coordinates[0])&&Number.isFinite(f.geometry.coordinates[1])),isLocal);
          if(fs.length)return fs.slice(0,limit);
        }
      }catch(e){console.warn('community nominatim app helper',e)}

      try{
        if(typeof photonSearch==='function'){
          const fs=localFilter(await photonSearch(`https://photon.komoot.io/api/?q=${encodeURIComponent(candidate)}&limit=${Math.max(limit,8)}`),isLocal);
          if(fs.length)return fs.slice(0,limit);
        }
      }catch(e){console.warn('community photon app helper',e)}

      try{
        const ctrl=typeof AbortController!=='undefined'?new AbortController():null;
        const timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
        try{
          const r=await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=it&addressdetails=1&limit=${Math.max(limit,8)}&q=${encodeURIComponent(candidate)}`,
            ctrl?{signal:ctrl.signal,headers:{'Accept-Language':'it'}}:{headers:{'Accept-Language':'it'}});
          if(r.ok){
            const ns=await r.json();
            const fs=localFilter((Array.isArray(ns)?ns:[]).map(tcvNominatimFeature).filter(f=>Number.isFinite(f.geometry.coordinates[0])&&Number.isFinite(f.geometry.coordinates[1])),isLocal);
            if(fs.length)return fs.slice(0,limit);
          }
        }finally{if(timer)clearTimeout(timer)}
      }catch(e){console.warn('community nominatim direct',e)}

      try{
        if(typeof db!=='undefined'&&db?.functions?.invoke){
          const {data,error}=await db.functions.invoke('community-place-search',{body:{q:candidate,limit:Math.max(limit,8)}});
          const fs=localFilter(!error&&Array.isArray(data?.features)?data.features:[],isLocal);
          if(fs.length)return fs.slice(0,limit);
        }
      }catch(e){console.warn('community place proxy',e)}

      try{
        const ctrl=typeof AbortController!=='undefined'?new AbortController():null;
        const timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
        try{
          const r=await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(candidate+', Italia')}&limit=${Math.max(limit,8)}&lang=it`,ctrl?{signal:ctrl.signal}:undefined);
          if(r.ok){const j=await r.json();const fs=localFilter(Array.isArray(j.features)?j.features:[],isLocal);if(fs.length)return fs.slice(0,limit)}
        }finally{if(timer)clearTimeout(timer)}
      }catch(e){console.warn('community photon direct',e)}
    }
    return [];
  }
  async function reversePoint(lat,lng){
    try{
      if(typeof reverseGeocodePoint==='function'){
        const p=await reverseGeocodePoint({lat,lng});
        const label=p?.label||[p?.street,p?.area,p?.city].filter(Boolean).join(', ');
        if(label)return {lat,lng,label}
      }
    }catch(e){}
    try{
      const r=await fetch(`https://photon.komoot.io/reverse?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lng)}&lang=it`),j=await r.json(),f=j?.features?.[0];
      if(f)return {...featurePoint(f),lat,lng}
    }catch(e){}
    return {lat,lng,label:`${lat.toFixed(5)}, ${lng.toFixed(5)}`}
  }

  function clearBox(id){const b=document.getElementById(id);if(b)b.innerHTML=''}
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
  function bindAutocomplete(inputId,boxId,key,target='trip'){
    const input=document.getElementById(inputId);if(!input)return;
    input.setAttribute('autocomplete','off');
    input.addEventListener('input',()=>{
      const state=target==='trip'?draft:rideDraft,anchor=state[key==='from'?'to':'from'];
      state[key]=null;
      clearTimeout(searchTimers[inputId]);
      const q=input.value.trim();if(q.length<2){clearBox(boxId);return}
      searchTimers[inputId]=setTimeout(async()=>{
        const box=document.getElementById(boxId);if(!box)return;
        const anchorTown=(!q.includes(',')&&tcvAddressLike(q))?tcvTownFromPoint(anchor):'';
        box.innerHTML=`<div class="notice">${anchorTown?`Cerco prima nel comune di <b>${safe(anchorTown)}</b>…`:'Cerco città, via, piazza e luogo…'}</div>`;
        try{
          const fs=await photon(q,7,anchor);
          box.innerHTML=fs.length?fs.map((f,i)=>`<button type="button" class="tcv-autoitem" data-i="${i}"><b>${safe(featureLabel(f)||q)}</b><small>${safe(featureSub(f))}</small></button>`).join(''):'<div class="notice yellow">Nessun luogo trovato. Se vuoi un altro paese scrivi anche il comune, per esempio “Piazza …, Chivasso”.</div>';
          box.querySelectorAll('button[data-i]').forEach(btn=>btn.addEventListener('pointerdown',(ev)=>{ev.preventDefault();
            const f=fs[Number(btn.dataset.i)],p=featurePoint(f);if(!Number.isFinite(p.lat)||!Number.isFinite(p.lng))return;
            input.value=p.label||q;state[key]=p;clearBox(boxId);
            if(target==='trip')tcvMaybeAutoPreview();else tcvMaybeRidePreview()
          }))
        }catch(e){console.warn('community autocomplete',e);box.innerHTML='<div class="notice yellow">Ricerca momentaneamente lenta: continua a scrivere città, via o piazza.</div>'}
      },250)
    })
  }

  async function resolveInput(inputId,key,target='trip'){
    const state=target==='trip'?draft:rideDraft;
    if(state[key]&&Number.isFinite(state[key].lat))return state[key];
    const val=document.getElementById(inputId)?.value.trim()||'';if(!val)throw new Error('Inserisci partenza e destinazione.');
    const gps=val.match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
    if(gps){const p=await reversePoint(Number(gps[1]),Number(gps[2]));state[key]=p;document.getElementById(inputId).value=p.label;return p}
    const anchor=state[key==='from'?'to':'from'];
    const fs=await photon(val,1,anchor);if(!fs.length)throw new Error(`Non trovo “${val}”. Scrivi anche il comune.`);
    const p=featurePoint(fs[0]);state[key]=p;document.getElementById(inputId).value=p.label;return p
  }

  async function routeDetails(a,b){
    const url=`https://router.project-osrm.org/route/v1/driving/${a.lng},${a.lat};${b.lng},${b.lat}?overview=full&geometries=geojson&steps=false`;
    const r=await fetch(url);if(!r.ok)throw new Error('Percorso stradale non disponibile');
    const j=await r.json();const rr=j?.routes?.[0];if(j.code!=='Ok'||!rr)throw new Error('Percorso non trovato');
    return {distanceKm:rr.distance/1000,durationMin:rr.duration/60,coords:rr.geometry?.coordinates||[]}
  }

  function scheduleFromForm(){
    const s={};DAY_DEFS.forEach(([k])=>{s[k]={enabled:!!document.getElementById(`tcvDay_${k}`)?.checked,out:document.getElementById(`tcvOut_${k}`)?.value||'',back:document.getElementById(`tcvBack_${k}`)?.value||''}});return s
  }
  function scheduleText(s,compact=false){
    const rows=DAY_DEFS.filter(([k])=>daySchedule(s,k).enabled).map(([k,label])=>{
      const d=daySchedule(s,k),times=[d.out?`→ ${d.out}`:'',d.back?`← ${d.back}`:''].filter(Boolean).join(' · ');return `${compact?label.slice(0,3):label} ${times}`
    });return rows.length?rows.join(compact?' · ':'<br>'):'Nessun giorno attivo'
  }
  function dayRowsHtml(s){
    return DAY_DEFS.map(([k,label])=>{const d=daySchedule(s,k),on=!!d.enabled;return `<div id="tcvDayRow_${k}" class="tcv-day ${on?'':'off'}"><label class="tcv-day-name"><input id="tcvDay_${k}" type="checkbox" ${on?'checked':''} onchange="tcvTripDayToggle('${k}')"><span>${label}</span></label><div class="tcv-day-time"><label>ANDATA</label><input id="tcvOut_${k}" type="time" value="${safe(d.out||'')}" ${on?'':'disabled'}></div><div class="tcv-day-time"><label>RITORNO</label><input id="tcvBack_${k}" type="time" value="${safe(d.back||'')}" ${on?'':'disabled'}></div></div>`}).join('')
  }

  window.tcvTripDayToggle=function(k){
    const on=!!document.getElementById(`tcvDay_${k}`)?.checked,row=document.getElementById(`tcvDayRow_${k}`);row?.classList.toggle('off',!on);
    for(const id of [`tcvOut_${k}`,`tcvBack_${k}`]){const el=document.getElementById(id);if(el)el.disabled=!on}
  };

  async function loadTrips(){
    if(typeof SESSION==='undefined'||!SESSION)return [];
    const {data,error}=await db.from('community_trips').select('*').order('updated_at',{ascending:false});if(error){console.warn('community trips',error);return TRIPS}
    TRIPS=data||[];window.TCV_COMMUNITY_TRIPS=TRIPS;return TRIPS
  }
  window.tcvLoadCommunityTrips=loadTrips;

  function ownTripsHtml(){
    const mine=TRIPS.filter(t=>String(t.user_id)===String(SESSION?.user?.id));
    if(!mine.length)return '<div class="notice">Non hai ancora registrato un percorso abituale.</div>';
    return `<div class="tcv-mytrips">${mine.map(t=>`<article class="tcv-tripcard ${t.active?'active':''}"><div class="tcv-triphead"><strong>${t.active?'● GIRO ATTIVO':'○ GIRO DISATTIVATO'}</strong><span>${num(t.distance_km).toFixed(1)} km</span></div><h3>${safe(t.from_label)} → ${safe(t.to_label)}</h3><p>${scheduleText(t.schedule)}<br>👥 ${Number(t.seats||1)} posti · <b>${money(num(t.distance_km)*RATE_PER_KM)}</b> a persona · €0,35/km</p><div class="tcv-tripactions"><button class="toggle" onclick="tcvToggleCommunityTrip('${t.id}',${t.active?'false':'true'})">${t.active?'DISATTIVA':'ATTIVA'}</button><button onclick="openTripSearch('${t.id}')">MODIFICA</button><button onclick="tcvDeleteCommunityTrip('${t.id}')">ELIMINA</button></div></article>`).join('')}</div>`
  }

  function resetTripDraft(t){
    draft={from:t?{lat:num(t.from_lat),lng:num(t.from_lng),label:t.from_label}:null,to:t?{lat:num(t.to_lat),lng:num(t.to_lng),label:t.to_label}:null,route:t?{distanceKm:num(t.distance_km),durationMin:null,coords:Array.isArray(t.route_coords)?t.route_coords:[]}:null}
  }

  window.openTripSearch=async function(editId=''){
    injectStyles();await loadTrips();
    const t=editId?TRIPS.find(x=>String(x.id)===String(editId)&&String(x.user_id)===String(SESSION?.user?.id)):null;resetTripDraft(t||null);
    const schedule=t?.schedule||DEFAULT_SCHEDULE;
    openSheet(`${head('STO GIÀ ANDANDO',t?'🚗 Modifica il tuo percorso':'🚗 Registra il tuo percorso','Prima esiste il tuo viaggio. Le persone che devono andare nella stessa direzione possono chiederti un posto e dividere le spese.')}<div class="tcv-route-hero"><b>CONTRIBUTO TRASPARENTE: € 0,35 / KM / PERSONA</b><span>Tanto Ci Vai calcola la distanza stradale reale. Il contributo del passeggero e la commissione TCV da € 0,50 vengono mostrati separatamente.</span></div>${!t?`<div class="sect" style="margin-top:10px"><h2>I miei giri</h2><span>${TRIPS.filter(x=>String(x.user_id)===String(SESSION?.user?.id)).length}</span></div>${ownTripsHtml()}`:''}<div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI PARTENZA</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="tcvTripFromTown" value="${safe(tcvTownFromPoint(draft.from))}" placeholder="Es. Lauriano"><div id="tcvTripFromTownBox" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="tcvTripFrom" value="${safe(tcvPlaceDetail(draft.from))}" placeholder="Es. Piazza Risorgimento" ${tcvTownFromPoint(draft.from)?'':'disabled'}><div id="tcvTripFromBox" class="tcv-autobox"></div></div></div><button type="button" class="gpsbtn" onclick="tcvUseGpsTripCommunity()">📍 Usa la mia posizione GPS</button><div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI DESTINAZIONE</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="tcvTripToTown" value="${safe(tcvTownFromPoint(draft.to))}" placeholder="Es. Saluggia"><div id="tcvTripToTownBox" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="tcvTripTo" value="${safe(tcvPlaceDetail(draft.to))}" placeholder="Es. Via Roma" ${tcvTownFromPoint(draft.to)?'':'disabled'}><div id="tcvTripToBox" class="tcv-autobox"></div></div></div><div class="grid2"><div class="field"><label>POSTI DISPONIBILI</label><select id="tcvTripSeats">${[1,2,3,4,5,6,7].map(n=>`<option value="${n}" ${Number(t?.seats||3)===n?'selected':''}>${n} ${n===1?'posto':'posti'}</option>`).join('')}</select></div><div class="field"><label>STATO DEL GIRO</label><select id="tcvTripActive"><option value="1" ${t?.active===false?'':'selected'}>Attivo · visibile</option><option value="0" ${t?.active===false?'selected':''}>Disattivato</option></select></div></div><button type="button" class="btn primary full" onclick="tcvComputeTripPreview()">🧭 CALCOLA PERCORSO E CONTRIBUTO</button><div id="tcvTripPreview">${t?tcvPreviewHtml(draft.route):'<div class="notice" style="margin-top:8px">Inserisci partenza e destinazione: la distanza verrà calcolata sulla strada reale.</div>'}</div><div class="sect" style="margin-top:15px"><h2>Calendario settimanale</h2><span>Lun → Dom</span></div><div class="notice green">Attiva solo i giorni in cui fai davvero questo tragitto. Per ogni giorno puoi indicare <b>andata e ritorno</b>.</div><div class="tcv-calendar">${dayRowsHtml(schedule)}</div><div id="tcvTripStatus" class="notice green">${t?'Modifica gli orari o il percorso e salva.':'Il giro sarà pubblico sulla mappa solo quando è attivo.'}</div><button id="tcvTripSave" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvSaveCommunityTrip('${t?.id||''}')">${t?'SALVA MODIFICHE':'SALVA E ATTIVA IL GIRO'}</button>${t?'<button class="btn outline full" style="margin-top:8px" onclick="openTripSearch()">← I miei giri</button>':'<button class="btn outline full" style="margin-top:8px" onclick="closeSheet();page(\'home\')">← Home</button>'}`);
    setTimeout(()=>{tcvSeedTownInput('tcvTripFromTown','tcvTripFrom',draft.from);tcvSeedTownInput('tcvTripToTown','tcvTripTo',draft.to);bindTownAutocomplete('tcvTripFromTown','tcvTripFromTownBox','tcvTripFrom','tcvTripFromBox','from','trip');bindLocalAutocomplete('tcvTripFromTown','tcvTripFrom','tcvTripFromBox','from','trip');bindTownAutocomplete('tcvTripToTown','tcvTripToTownBox','tcvTripTo','tcvTripToBox','to','trip');bindLocalAutocomplete('tcvTripToTown','tcvTripTo','tcvTripToBox','to','trip')},0)
  };

  function tcvPreviewHtml(r){
    if(!r||!num(r.distanceKm))return '<div class="notice">Percorso non ancora calcolato.</div>';
    const pp=num(r.distanceKm)*RATE_PER_KM;return `<div class="tcv-route-preview"><strong>${num(r.distanceKm).toFixed(1)} km · ${money(pp)} a persona</strong><br>Contributo conducente: ${money(RATE_PER_KM)}/km/persona${r.durationMin?` · circa ${Math.round(r.durationMin)} min`:''}.<br>Servizio Tanto Ci Vai: <b>${money(PLATFORM_FEE)}</b> separato al momento della prenotazione.</div>`
  }
  window.tcvComputeTripPreview=async function(){
    const st=document.getElementById('tcvTripStatus'),box=document.getElementById('tcvTripPreview');if(st)st.textContent='Calcolo la strada reale…';
    try{const [a,b]=await Promise.all([resolvePlace('tcvTripFromTown','tcvTripFrom','from','trip'),resolvePlace('tcvTripToTown','tcvTripTo','to','trip')]);const r=await routeDetails(a,b);draft.route=r;if(box)box.innerHTML=tcvPreviewHtml(r);if(st)st.textContent='✓ Percorso verificato. Controlla calendario e posti, poi salva.';return r}catch(e){if(st)st.textContent='Errore: '+e.message;throw e}
  };
  window.tcvMaybeAutoPreview=function(){if(draft.from&&draft.to)setTimeout(()=>window.tcvComputeTripPreview().catch(()=>{}),50)};
  function tcvMaybeAutoPreview(){window.tcvMaybeAutoPreview()}

  window.tcvUseGpsTripCommunity=function(){
    const st=document.getElementById('tcvTripStatus');if(st)st.textContent='Rilevo la tua posizione…';
    if(!navigator.geolocation){if(st)st.textContent='GPS non disponibile.';return}
    navigator.geolocation.getCurrentPosition(async p=>{const pt=await reversePoint(p.coords.latitude,p.coords.longitude);draft.from=pt;tcvSeedTownInput('tcvTripFromTown','tcvTripFrom',pt);const el=document.getElementById('tcvTripFrom');if(el)el.value=tcvPlaceDetail(pt);clearBox('tcvTripFromTownBox');clearBox('tcvTripFromBox');if(st)st.textContent='✓ Comune e punto di partenza compilati automaticamente dal GPS.';tcvMaybeAutoPreview()},()=>{if(st)st.textContent='Consenti la posizione al telefono oppure scrivi l’indirizzo.'},{enableHighAccuracy:true,timeout:12000})
  };

  window.tcvSaveCommunityTrip=async function(id=''){
    const st=document.getElementById('tcvTripStatus'),btn=document.getElementById('tcvTripSave');if(btn)btn.disabled=true;
    try{
      if(!draft.route||!num(draft.route.distanceKm))await window.tcvComputeTripPreview();
      const schedule=scheduleFromForm();if(!DAY_DEFS.some(([k])=>schedule[k].enabled))throw new Error('Attiva almeno un giorno della settimana.');
      for(const [k,label] of DAY_DEFS){const d=schedule[k];if(d.enabled&&!d.out&&!d.back)throw new Error(`Inserisci almeno un orario per ${label}.`)}
      const payload={user_id:SESSION.user.id,driver_name:PROFILE?.nome||'Utente',from_label:draft.from.label,from_lat:draft.from.lat,from_lng:draft.from.lng,to_label:draft.to.label,to_lat:draft.to.lat,to_lng:draft.to.lng,distance_km:Number(draft.route.distanceKm.toFixed(2)),price_per_km:RATE_PER_KM,seats:Number(document.getElementById('tcvTripSeats')?.value||3),schedule,route_coords:draft.route.coords||[],active:document.getElementById('tcvTripActive')?.value!=='0',updated_at:new Date().toISOString()};
      let error;if(id){({error}=await db.from('community_trips').update(payload).eq('id',id).eq('user_id',SESSION.user.id))}else{({error}=await db.from('community_trips').insert(payload))}if(error)throw error;
      await loadTrips();openSheet(`${head('PERCORSO SALVATO','🚗 Il tuo giro è pronto',payload.active?'È attivo e ora può essere visto sulla mappa della comunità.':'È salvato ma resta disattivato finché non lo attivi.')}<div class="tcv-route-preview"><strong>${safe(payload.from_label)} → ${safe(payload.to_label)}</strong><br>${payload.distance_km.toFixed(1)} km · ${money(payload.distance_km*RATE_PER_KM)} a persona · €0,35/km/persona<br>${scheduleText(schedule)}</div><button class="btn primary full" style="margin-top:10px" onclick="closeSheet();page('mapPage')">🗺️ VEDI SULLA MAPPA</button><button class="btn outline full" style="margin-top:8px" onclick="openTripSearch()">GESTISCI I MIEI GIRI</button>`)
    }catch(e){if(st)st.textContent='Errore: '+(e?.message||e);if(btn)btn.disabled=false}
  };

  window.tcvToggleCommunityTrip=async function(id,on){
    const {error}=await db.from('community_trips').update({active:!!on,updated_at:new Date().toISOString()}).eq('id',id).eq('user_id',SESSION.user.id);if(error){alert(error.message);return}await loadTrips();openTripSearch()
  };
  window.tcvDeleteCommunityTrip=async function(id){
    if(!confirm('Eliminare definitivamente questo percorso?'))return;const {error}=await db.from('community_trips').delete().eq('id',id).eq('user_id',SESSION.user.id);if(error){alert(error.message);return}await loadTrips();openTripSearch()
  };

  function nextTripSlot(t){
    const now=new Date(),candidates=[];
    for(let offset=0;offset<8;offset++){
      const d=new Date(now.getFullYear(),now.getMonth(),now.getDate()+offset);const jsDay=d.getDay(),def=DAY_DEFS.find(x=>x[2]===jsDay);if(!def)continue;const day=daySchedule(t.schedule,def[0]);if(!day.enabled)continue;
      for(const [dir,time] of [['out',day.out],['back',day.back]]){if(!time)continue;const [hh,mm]=time.split(':').map(Number),dt=new Date(d.getFullYear(),d.getMonth(),d.getDate(),hh||0,mm||0,0,0);if(dt.getTime()>now.getTime()+4*60000)candidates.push({date:dt,dir})}
    }
    candidates.sort((a,b)=>a.date-b.date);return candidates[0]||null
  }
  function localDateTimeValue(d){return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16)}
  function rideDefaultWhen(){const d=new Date(Date.now()+30*60000);d.setSeconds(0,0);d.setMinutes(Math.ceil(d.getMinutes()/5)*5);return localDateTimeValue(d)}

  window.tcvOpenRideFromTrip=async function(id){await loadTrips();const t=TRIPS.find(x=>String(x.id)===String(id));if(!t)return openRideRequest();const slot=nextTripSlot(t),back=slot?.dir==='back';openRideRequest(id,back,slot?.date||null)};

  window.openRideRequest=function(tripId='',returnDirection=false,slotDate=null){
    injectStyles();const t=tripId?TRIPS.find(x=>String(x.id)===String(tripId)):null;
    rideDraft={from:t?(returnDirection?{lat:num(t.to_lat),lng:num(t.to_lng),label:t.to_label}:{lat:num(t.from_lat),lng:num(t.from_lng),label:t.from_label}):null,to:t?(returnDirection?{lat:num(t.from_lat),lng:num(t.from_lng),label:t.from_label}:{lat:num(t.to_lat),lng:num(t.to_lng),label:t.to_label}):null,tripId:t?.id||null,route:t?{distanceKm:num(t.distance_km),coords:t.route_coords||[],durationMin:null}:null};
    const when=slotDate?localDateTimeValue(slotDate):rideDefaultWhen();
    openSheet(`${head('RICHIEDI PASSAGGIO','🚘 Dove devi andare?','Inserisci città, via, piazza o luogo: l’indirizzo viene completato automaticamente. Il contributo è sempre calcolato alla luce del sole.')}<div class="ride-request-hero"><b>PASSAGGIO COMMUNITY</b><span>€ 0,35/km a persona · chi passa di lì può offrirti un posto</span></div>${t?`<div class="notice green">Hai scelto il giro di <b>${safe(t.driver_name||'un utente')}</b>: ${safe(rideDraft.from.label)} → ${safe(rideDraft.to.label)}</div>`:''}<div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI PARTENZA</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="rideFromTown" value="${safe(tcvTownFromPoint(rideDraft.from))}" placeholder="Es. Lauriano"><div id="rideFromTownAuto" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="rideFrom" value="${safe(tcvPlaceDetail(rideDraft.from))}" placeholder="Es. Piazza Risorgimento" ${tcvTownFromPoint(rideDraft.from)?'':'disabled'}><div id="rideFromAuto" class="tcv-autobox"></div></div></div><button class="gpsbtn" onclick="tcvUseGpsRideCommunity()">📍 Usa la mia posizione GPS</button><div class="tcv-place-block"><span class="tcv-place-step">1 · COMUNE DI DESTINAZIONE</span><div class="field tcv-autowrap"><label>COMUNE</label><input id="rideToTown" value="${safe(tcvTownFromPoint(rideDraft.to))}" placeholder="Es. Saluggia"><div id="rideToTownAuto" class="tcv-autobox"></div></div><span class="tcv-place-step">2 · PUNTO PRECISO</span><div class="field tcv-autowrap"><label>VIA / PIAZZA / LUOGO · FACOLTATIVO</label><input id="rideTo" value="${safe(tcvPlaceDetail(rideDraft.to))}" placeholder="Es. Via Roma" ${tcvTownFromPoint(rideDraft.to)?'':'disabled'}><div id="rideToAuto" class="tcv-autobox"></div></div></div><div class="field"><label>QUANDO VUOI PARTIRE</label><input id="rideWhen" type="datetime-local" value="${when}"></div><div class="grid2"><div class="field"><label>FLESSIBILITÀ</label><select id="rideFlex"><option value="15">± 15 min</option><option value="30" selected>± 30 min</option><option value="60">± 1 ora</option><option value="120">± 2 ore</option></select></div><div class="field"><label>PERSONE</label><select id="ridePassengers" onchange="tcvRenderRidePrice()"><option value="1">1 persona</option><option value="2">2 persone</option><option value="3">3 persone</option><option value="4">4 persone</option><option value="5">5 persone</option><option value="6">6 persone</option></select></div></div><button class="btn primary full" onclick="tcvComputeRidePreview()">🧭 CALCOLA CONTRIBUTO</button><div id="ridePriceBox">${t?ridePriceHtml(rideDraft.route):'<div class="notice" style="margin-top:8px">La distanza stradale reale determina il contributo.</div>'}</div><div class="field"><label>NOTA · FACOLTATIVA</label><textarea id="rideNote" rows="3" maxlength="300" placeholder="Es. Ho un bambino, ho una borsa, posso aspettare 20 minuti…"></textarea></div><div id="rideStatus" class="notice green">La richiesta sarà visibile alle persone con un giro compatibile.</div><button id="ridePublishBtn" class="ride-publish full" onclick="publishRideRequest()">🚘 PUBBLICA RICHIESTA PASSAGGIO</button><button class="btn outline full" style="margin-top:8px" onclick="closeSheet();page('home')">← Torna alla Home</button>`);
    setTimeout(()=>{tcvSeedTownInput('rideFromTown','rideFrom',rideDraft.from);tcvSeedTownInput('rideToTown','rideTo',rideDraft.to);bindTownAutocomplete('rideFromTown','rideFromTownAuto','rideFrom','rideFromAuto','from','ride');bindLocalAutocomplete('rideFromTown','rideFrom','rideFromAuto','from','ride');bindTownAutocomplete('rideToTown','rideToTownAuto','rideTo','rideToAuto','to','ride');bindLocalAutocomplete('rideToTown','rideTo','rideToAuto','to','ride')},0)
  };

  function ridePriceHtml(r){
    if(!r||!num(r.distanceKm))return '<div class="notice">Percorso non ancora calcolato.</div>';
    const persons=Math.max(1,Number(document.getElementById('ridePassengers')?.value||1)),per=num(r.distanceKm)*RATE_PER_KM,driver=per*persons,total=driver+PLATFORM_FEE;
    return `<div class="tcv-ride-price"><b>${num(r.distanceKm).toFixed(1)} km</b><br>Contributo: <b>${money(per)} a persona</b> (${money(RATE_PER_KM)}/km).<br>${persons>1?`${persons} persone → contributo totale conducente <b>${money(driver)}</b>.<br>`:''}Servizio Tanto Ci Vai: <b>${money(PLATFORM_FEE)}</b> separato.<br>Totale previsto: <b>${money(total)}</b>.</div>`
  }
  window.tcvRenderRidePrice=function(){const b=document.getElementById('ridePriceBox');if(b)b.innerHTML=ridePriceHtml(rideDraft.route)};
  window.tcvComputeRidePreview=async function(){
    const st=document.getElementById('rideStatus');if(st)st.textContent='Calcolo la distanza stradale reale…';
    try{const [a,b]=await Promise.all([resolvePlace('rideFromTown','rideFrom','from','ride'),resolvePlace('rideToTown','rideTo','to','ride')]);const r=await routeDetails(a,b);rideDraft.route=r;window.tcvRenderRidePrice();if(st)st.textContent='✓ Percorso verificato e contributo calcolato.';return r}catch(e){if(st)st.textContent='Errore: '+e.message;throw e}
  };
  window.tcvMaybeRidePreview=function(){if(rideDraft.from&&rideDraft.to)setTimeout(()=>window.tcvComputeRidePreview().catch(()=>{}),50)};
  function tcvMaybeRidePreview(){window.tcvMaybeRidePreview()}
  window.tcvUseGpsRideCommunity=function(){
    const st=document.getElementById('rideStatus');if(st)st.textContent='Rilevo la tua posizione…';if(!navigator.geolocation){if(st)st.textContent='GPS non disponibile.';return}
    navigator.geolocation.getCurrentPosition(async p=>{const pt=await reversePoint(p.coords.latitude,p.coords.longitude);rideDraft.from=pt;tcvSeedTownInput('rideFromTown','rideFrom',pt);const el=document.getElementById('rideFrom');if(el)el.value=tcvPlaceDetail(pt);clearBox('rideFromTownAuto');clearBox('rideFromAuto');if(st)st.textContent='✓ Comune e punto di partenza compilati automaticamente dal GPS.';tcvMaybeRidePreview()},()=>{if(st)st.textContent='Consenti la posizione oppure scrivi l’indirizzo.'},{enableHighAccuracy:true,timeout:12000})
  };
  window.tcvUseGpsRideStart=window.tcvUseGpsRideCommunity;

  window.publishRideRequest=async function(){
    const when=document.getElementById('rideWhen')?.value||'',note=document.getElementById('rideNote')?.value.trim()||'',flex=Math.max(0,Math.min(180,Number(document.getElementById('rideFlex')?.value||30))),passengers=Math.max(1,Math.min(6,Number(document.getElementById('ridePassengers')?.value||1))),st=document.getElementById('rideStatus'),btn=document.getElementById('ridePublishBtn');
    const departure=new Date(when);if(!when||!Number.isFinite(departure.getTime())||departure.getTime()<Date.now()+5*60000){if(st)st.textContent='Scegli un orario almeno 5 minuti nel futuro.';return}
    if(btn)btn.disabled=true;
    try{
      if(!rideDraft.route||!num(rideDraft.route.distanceKm))await window.tcvComputeRidePreview();
      const [a,b]=await Promise.all([resolvePlace('rideFromTown','rideFrom','from','ride'),resolvePlace('rideToTown','rideTo','to','ride')]),per=num(rideDraft.route.distanceKm)*RATE_PER_KM;
      const payload={user_id:SESSION.user.id,from_label:a.label,from_lat:a.lat,from_lng:a.lng,to_label:b.label,to_lat:b.lat,to_lng:b.lng,departure_at:departure.toISOString(),flex_minutes:flex,passengers,note:note.slice(0,300),status:'open',distance_km:Number(num(rideDraft.route.distanceKm).toFixed(2)),contribution_per_person:Number(per.toFixed(2)),platform_fee:PLATFORM_FEE,community_trip_id:rideDraft.tripId||null};
      const {error}=await db.from('ride_requests').insert(payload);if(error)throw error;await loadRideRequests();closeSheet();page('myreq')
    }catch(e){if(st)st.textContent='Errore: '+(e?.message||e);if(btn)btn.disabled=false}
  };

  function tripPopup(t){
    const per=num(t.distance_km)*RATE_PER_KM;return `<div class="tcv-map-popup"><b>🚗 GIRO COMMUNITY ATTIVO</b><div class="row"><strong>${safe(t.from_label)} → ${safe(t.to_label)}</strong></div><div class="row">👤 <b>Viaggiatore: ${safe(t.driver_name||'Utente')}</b> · 👥 ${Number(t.seats||1)} posti</div><div class="row">📏 ${num(t.distance_km).toFixed(1)} km · 💶 ${money(per)} / persona</div><div class="row">🗓️ ${scheduleText(t.schedule,true)}</div><div class="row">Servizio TCV: ${money(PLATFORM_FEE)} separato</div><button onclick="tcvOpenRideFromTrip('${t.id}')">RICHIEDI UN POSTO</button></div>`
  }

  window.renderMapPage=function(){
    const mapPage=document.getElementById('mapPage');if(!mapPage)return;
    mapPage.innerHTML=`<div class="pagehead"><div class="k">MAPPA COMMUNITY</div><h2>Mappa della comunità</h2><p>SOS, pericoli e giri Community attivi. I ritiri Business non compaiono qui.</p></div><div class="map-community-legend"><span><i class="map-key-dot hazard"></i> Attenzione / pericolo</span><span><i class="map-key-dot help"></i> SOS attivo</span><span><i class="map-key-dot resolved"></i> SOS risolto</span><span class="tcv-map-route-key"><i class="tcv-map-route-line"></i> Giro attivo</span></div><div id="mapAlertStatus" class="notice" style="margin-bottom:9px">Aggiorno mappa e giri…</div><button class="gpsbtn" onclick="locateMe()">📍 Aggiorna la mia posizione</button><div class="map-shell"><div id="map"></div></div>`;
    Promise.all([typeof loadCommunityAlerts==='function'?loadCommunityAlerts():Promise.resolve(),loadTrips()]).finally(()=>setTimeout(()=>window.initMap(),60))
  };

  window.initMap=function(){
    if(typeof MAP!=='undefined'&&MAP){MAP.remove();MAP=null}
    MAP=L.map('map').setView([45.18,7.99],11);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(MAP);const pts=[];
    try{(COMMUNITY_ALERTS||[]).forEach(a=>{if(!Number.isFinite(Number(a.lat))||!Number.isFinite(Number(a.lng)))return;const ll=[Number(a.lat),Number(a.lng)];pts.push(ll);L.marker(ll,{icon:communityAlertIcon(a),zIndexOffset:a.kind==='hazard'?700:(a.resolved_at?850:1000)}).addTo(MAP).bindPopup(communityAlertPopup(a),{maxWidth:290})})}catch(e){console.warn('alerts map',e)}
    TRIPS.filter(t=>t.active).forEach(t=>{const coords=Array.isArray(t.route_coords)?t.route_coords:[];const latlngs=coords.map(c=>[Number(c[1]),Number(c[0])]).filter(c=>Number.isFinite(c[0])&&Number.isFinite(c[1]));if(latlngs.length<2)return;pts.push(latlngs[0],latlngs[latlngs.length-1]);const line=L.polyline(latlngs,{weight:6,opacity:.78}).addTo(MAP);line.bindPopup(tripPopup(t),{maxWidth:310});line.bindTooltip(`👤 ${safe(t.driver_name||'Utente')}`,{permanent:true,direction:'center',opacity:.92,className:'tcv-route-name'})});
    try{if(USER_POS){L.circleMarker([USER_POS.lat,USER_POS.lng],{radius:8,weight:4,fillOpacity:.9}).addTo(MAP).bindPopup('La tua posizione');pts.push([USER_POS.lat,USER_POS.lng])}}catch(e){}
    if(pts.length)MAP.fitBounds(pts,{padding:[30,30],maxZoom:14});const st=document.getElementById('mapAlertStatus');if(st)st.textContent=`${TRIPS.filter(t=>t.active).length} giri Community attivi · SOS e pericoli aggiornati`;
  };

  window.renderMyRideSection=function(){
    const rows=[...(typeof MY_RIDES!=='undefined'?MY_RIDES:[])].sort((a,b)=>new Date(b.created_at)-new Date(a.created_at)),active=rows.filter(r=>r.status==='open'||r.status==='matched');
    if(!rows.length)return `<section class="my-rides-section"><div class="my-rides-title"><div><span>🚘 PASSAGGI</span><h3>I miei passaggi</h3></div><b>0 attivi</b></div><div class="empty">Non hai ancora richiesto un passaggio.</div><button class="ride-publish full" style="margin-top:10px" onclick="openRideRequest()">+ RICHIEDI PASSAGGIO</button></section>`;
    return `<section class="my-rides-section"><div class="my-rides-title"><div><span>🚘 PASSAGGI</span><h3>I miei passaggi</h3></div><b>${active.length} attiv${active.length===1?'o':'i'}</b></div>${rows.map(r=>`<article class="my-ride-card ${r.status}"><div class="my-ride-head"><strong>${typeof tcvRideStatusLabel==='function'?tcvRideStatusLabel(r):String(r.status).toUpperCase()}</strong><small>${new Date(r.departure_at).toLocaleString('it-IT',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</small></div><h3>${safe(r.from_label)} → ${safe(r.to_label)}</h3><p>👥 ${Number(r.passengers||1)} · flessibilità ±${Number(r.flex_minutes||0)} min${num(r.distance_km)?`<br>📏 ${num(r.distance_km).toFixed(1)} km · 💶 <b>${money(r.contribution_per_person)} a persona</b> · servizio TCV ${money(r.platform_fee??PLATFORM_FEE)}`:''}${r.note?`<br>💬 ${safe(r.note)}`:''}</p>${r.status==='open'?`<button class="btn danger full" style="margin-top:9px" onclick="cancelRideRequest('${r.id}')">ANNULLA RICHIESTA PASSAGGIO</button>`:''}</article>`).join('')}<button class="ride-publish full" style="margin-top:10px" onclick="openRideRequest()">+ NUOVO PASSAGGIO</button></section>`
  };

  function setupRealtime(){
    if(realtimeChannel||typeof db==='undefined'||typeof SESSION==='undefined'||!SESSION)return;
    try{realtimeChannel=db.channel('tcv-community-trips-v1').on('postgres_changes',{event:'*',schema:'public',table:'community_trips'},async()=>{await loadTrips();const mp=document.getElementById('mapPage');if(mp&&!mp.classList.contains('hidden'))window.renderMapPage()}).subscribe()}catch(e){console.warn('trip realtime',e)}
  }

  injectStyles();
  let tries=0;const timer=setInterval(async()=>{tries++;if(typeof SESSION!=='undefined'&&SESSION){clearInterval(timer);await loadTrips();setupRealtime()}else if(tries>40)clearInterval(timer)},300);
})();

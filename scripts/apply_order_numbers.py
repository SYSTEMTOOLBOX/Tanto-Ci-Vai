from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

if '/* ORDER_NUMBERS_V1 */' in s:
    print('Order number UI already applied')
    raise SystemExit(0)

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(label + ' anchor not found')
    s = s.replace(old, new, 1)

# Shared formatter. Keep old beta requests unnumbered; new requests start at 0000 from Supabase.
anchor = "const cleanDeliveryAddress=v=>String(v||'').replace(/,\\s*Piazzo\\s*,/gi,', ').replace(/\\s{2,}/g,' ').trim();"
helper = """/* ORDER_NUMBERS_V1 */
const orderCode=r=>r?.numero_ordine==null?'':String(Math.max(0,Number(r.numero_ordine)||0)).padStart(4,'0');
const orderBadge=r=>r?.numero_ordine==null?'':`<span class=\"pill\">🧾 Ordine #${orderCode(r)}</span>`;
"""
replace_once(anchor, helper + anchor, 'order helper')

# Show the order number on every main request/mission card.
replace_once(
    '<span class="dist">${esc(statusLabel)}</span></div><h3>',
    '<div style="display:flex;align-items:center;gap:6px">${orderBadge(r)}<span class="dist">${esc(statusLabel)}</span></div></div><h3>',
    'card order badge'
)

# Details screen: make the order number immediately obvious.
replace_once(
    "head('DETTAGLI RICHIESTA',r.titolo,'Prima di accettare vedi ritiro, consegna e tutte le note.')",
    "head('DETTAGLI RICHIESTA',r.numero_ordine!=null?`Ordine #${orderCode(r)} · ${r.titolo}`:r.titolo,'Prima di accettare vedi ritiro, consegna e tutte le note.')",
    'request details order number'
)

# Pickup confirmation: runner can show/read the same number at the shop.
replace_once(
    "head('RITIRO COMPLETATO','Pacco ritirato','Imposta l’orario previsto di consegna. Il mittente lo vedrà subito.')",
    "head('RITIRO COMPLETATO',r.numero_ordine!=null?`Ordine #${orderCode(r)} · Pacco ritirato`:'Pacco ritirato','Imposta l’orario previsto di consegna. Il mittente lo vedrà subito.')",
    'pickup order number'
)

# Runner navigation carries the order number too.
replace_once(
    "head('NAVIGATORE RUNNER',r.titolo,'Percorso completo: dalla tua posizione al ritiro, poi alla consegna.')",
    "head('NAVIGATORE RUNNER',r.numero_ordine!=null?`Ordine #${orderCode(r)} · ${r.titolo}`:r.titolo,'Percorso completo: dalla tua posizione al ritiro, poi alla consegna.')",
    'runner navigation order number'
)

# Return the server-assigned number when publishing a request.
replace_once(
    ".select('id').single();if(error)throw error;try{await db.functions.invoke",
    ".select('id,numero_ordine').single();if(error)throw error;try{await db.functions.invoke",
    'publish select order number'
)
replace_once(
    "if(DELIVERY_MAP){DELIVERY_MAP.remove();DELIVERY_MAP=null;DELIVERY_MARKER=null}showRequestPublishedSuccess()",
    "if(DELIVERY_MAP){DELIVERY_MAP.remove();DELIVERY_MAP=null;DELIVERY_MARKER=null}showRequestPublishedSuccess(created.numero_ordine)",
    'publish success order number'
)

# Confirmation popup shows the newly-created order immediately.
replace_once(
    'function showRequestPublishedSuccess(){',
    'function showRequestPublishedSuccess(numeroOrdine){',
    'success popup signature'
)
replace_once(
    '<p>Perfetto! La tua richiesta è ora visibile ai runner della zona.</p>',
    '<p>${numeroOrdine!=null?`Ordine <b>#${String(Number(numeroOrdine)).padStart(4,\'0\')}</b> creato. `:\'\'}La tua richiesta è ora visibile ai runner della zona.</p>',
    'success popup order text'
)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Progressive order number UI applied')

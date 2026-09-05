/* TCV_QR_LOCAL_V1 */
(function(){
  'use strict';
  if(window.TCVLocalQR)return;

  function utf8Bytes(s){
    if(window.TextEncoder)return Array.from(new TextEncoder().encode(String(s)));
    const x=unescape(encodeURIComponent(String(s)));
    return Array.from(x,ch=>ch.charCodeAt(0));
  }

  const EXP=new Array(512),LOG=new Array(256);
  let x=1;
  for(let i=0;i<255;i++){
    EXP[i]=x;LOG[x]=i;x<<=1;if(x&0x100)x^=0x11d;
  }
  for(let i=255;i<512;i++)EXP[i]=EXP[i-255];

  function gfMul(a,b){return(!a||!b)?0:EXP[LOG[a]+LOG[b]]}
  function rsGenerator(n){
    let g=[1];
    for(let i=0;i<n;i++){
      const ng=new Array(g.length+1).fill(0);
      for(let j=0;j<g.length;j++){
        ng[j]^=g[j];
        ng[j+1]^=gfMul(g[j],EXP[i]);
      }
      g=ng;
    }
    return g;
  }
  function rsEcc(data,n){
    const gen=rsGenerator(n),res=new Array(n).fill(0);
    for(const b of data){
      const factor=b^res[0];res.shift();res.push(0);
      for(let j=0;j<n;j++)res[j]^=gfMul(gen[j+1],factor);
    }
    return res;
  }
  function pushBits(out,val,len){for(let i=len-1;i>=0;i--)out.push((val>>>i)&1)}
  function degree(v){let n=0;while(v){n++;v>>>=1}return n}
  function formatBits(mask){
    const data=mask; // ECC M = 00
    let d=data<<10;
    const g=0x537;
    while(degree(d)-degree(g)>=0)d^=g<<(degree(d)-degree(g));
    return((data<<10)|d)^0x5412;
  }

  function makeMatrix(text){
    // Version 6-M: 41x41, 108 data codewords, 4 blocks x (27 data + 16 ECC).
    // Enough for up to 106 UTF-8 bytes: well above a normal Tanto Ci Vai profile QR URL.
    const size=41,dataCw=108,ecCw=16,blocks=4;
    const bytes=utf8Bytes(text);
    if(bytes.length>106)throw new Error('QR troppo lungo. Rigenera il codice.');

    const bits=[];
    pushBits(bits,4,4); // byte mode
    pushBits(bits,bytes.length,8);
    for(const b of bytes)pushBits(bits,b,8);
    const capacity=dataCw*8;
    for(let i=0;i<4&&bits.length<capacity;i++)bits.push(0);
    while(bits.length%8)bits.push(0);

    const data=[];
    for(let i=0;i<bits.length;i+=8){
      let v=0;for(let j=0;j<8;j++)v=(v<<1)|(bits[i+j]||0);data.push(v);
    }
    let pad=0;
    while(data.length<dataCw)data.push((pad++%2===0)?0xec:0x11);

    const dblocks=[],eblocks=[];
    for(let b=0;b<blocks;b++){
      const d=data.slice(b*27,b*27+27);
      dblocks.push(d);eblocks.push(rsEcc(d,ecCw));
    }
    const code=[];
    for(let i=0;i<27;i++)for(let b=0;b<blocks;b++)code.push(dblocks[b][i]);
    for(let i=0;i<ecCw;i++)for(let b=0;b<blocks;b++)code.push(eblocks[b][i]);
    const dbits=[];
    for(const b of code)pushBits(dbits,b,8);
    for(let i=0;i<7;i++)dbits.push(0); // remainder bits for version 6

    const m=Array.from({length:size},()=>Array(size).fill(null));
    function finder(r,c){
      for(let dr=-1;dr<=7;dr++){
        if(r+dr<0||r+dr>=size)continue;
        for(let dc=-1;dc<=7;dc++){
          if(c+dc<0||c+dc>=size)continue;
          m[r+dr][c+dc]=(dr>=0&&dr<=6&&(dc===0||dc===6))||
            (dc>=0&&dc<=6&&(dr===0||dr===6))||
            (dr>=2&&dr<=4&&dc>=2&&dc<=4);
        }
      }
    }
    finder(0,0);finder(size-7,0);finder(0,size-7);

    for(let i=8;i<size-8;i++)if(m[i][6]===null)m[i][6]=(i%2===0);
    for(let i=8;i<size-8;i++)if(m[6][i]===null)m[6][i]=(i%2===0);

    const centers=[6,34];
    for(const r of centers)for(const c of centers){
      if(m[r][c]!==null)continue;
      for(let dr=-2;dr<=2;dr++)for(let dc=-2;dc<=2;dc++)
        m[r+dr][c+dc]=(Math.abs(dr)===2||Math.abs(dc)===2||(dr===0&&dc===0));
    }

    const fmt=formatBits(0); // mask 0
    for(let i=0;i<15;i++){
      const bit=((fmt>>i)&1)===1;
      if(i<6)m[i][8]=bit;else if(i<8)m[i+1][8]=bit;else m[size-15+i][8]=bit;
      if(i<8)m[8][size-i-1]=bit;else if(i<9)m[8][15-i]=bit;else m[8][15-i-1]=bit;
    }
    m[size-8][8]=true;

    let bi=0,inc=-1,row=size-1;
    for(let col=size-1;col>0;col-=2){
      if(col===6)col--;
      while(true){
        for(let off=0;off<2;off++){
          const c=col-off;
          if(m[row][c]===null){
            let dark=bi<dbits.length?dbits[bi]:0;
            if((row+c)%2===0)dark^=1;
            m[row][c]=!!dark;bi++;
          }
        }
        row+=inc;
        if(row<0||row>=size){row-=inc;inc=-inc;break}
      }
    }
    return m;
  }

  function toSvg(text){
    const m=makeMatrix(String(text)),border=4,n=m.length,total=n+border*2;
    let path='';
    for(let r=0;r<n;r++)for(let c=0;c<n;c++)if(m[r][c])path+=`M${c+border} ${r+border}h1v1h-1z`;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${total} ${total}" width="280" height="280" role="img" aria-label="QR Tanto Ci Vai" shape-rendering="crispEdges"><rect width="100%" height="100%" fill="#fff"/><path d="${path}" fill="#000"/></svg>`;
  }

  window.TCVLocalQR={toSvg};
})();

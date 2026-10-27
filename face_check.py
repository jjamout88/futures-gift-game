from playwright.sync_api import sync_playwright
import sys,json
from PIL import Image
STATES=['idle','happy','sad','panic','faint']
GAME=['idle','long','short','profit','loss']
res={};errs=[]
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);pg.on('pageerror',lambda e:errs.append(str(e)))
  for V,url in [('A','?mk=a'),('B','')]:
    pg.goto('http://127.0.0.1:8823/index.html'+url);pg.wait_for_timeout(700)
    # grid-level check: dark components (8-conn) per face
    r=pg.evaluate("""()=>{const T=__T,out={};for(const k of Object.keys(T.face)){const G=T.hiG(T.face[k]);const h=G.length,w=G[0].length;
      const dk=(i,j)=>{const v=(G[j]||[])[i];return v==='k'};const seen=new Set(),comps=[];
      for(let j=0;j<h;j++)for(let i=0;i<w;i++)if(dk(i,j)&&!seen.has(i+','+j)){let st=[[i,j]],c=[];seen.add(i+','+j);while(st.length){const[a,b2]=st.pop();c.push([a,b2]);for(let dx=-1;dx<2;dx++)for(let dy=-1;dy<2;dy++){const q=(a+dx)+','+(b2+dy);if(dk(a+dx,b2+dy)&&!seen.has(q)){seen.add(q);st.push([a+dx,b2+dy])}}}
        const xs=c.map(p=>p[0]),ys=c.map(p=>p[1]);comps.push({n:c.length,x:Math.min(...xs),y:Math.min(...ys),bw:Math.max(...xs)-Math.min(...xs)+1,bh:Math.max(...ys)-Math.min(...ys)+1})}
      out[k]=comps}return out}""")
    if V=='B':
      r2=pg.evaluate('''()=>{const T=__T,o={};for(const m of['idle','happy','sad','panic','faint','blink','up','down']){const g=T.mkFace(m==='blink'||m==='up'||m==='down'?'idle':m,m==='blink',m==='up'?-1:m==='down'?1:0);
        const E=(i,j)=>{const v=(g[j]||[])[i];return v==='k'||v==='w'};const seen=new Set(),cs=[];
        for(let j=0;j<12+2;j++)for(let i=0;i<20;i++)if(E(i,j)&&!seen.has(i+','+j)){const st=[[i,j]],c=[];seen.add(i+','+j);while(st.length){const[a,b]=st.pop();c.push([a,b]);for(let dx=-1;dx<2;dx++)for(let dy=-1;dy<2;dy++)if(E(a+dx,b+dy)&&!seen.has((a+dx)+','+(b+dy))){seen.add((a+dx)+','+(b+dy));st.push([a+dx,b+dy])}}
          const ws=c.filter(([a,b])=>g[b][a]==='w');cs.push({n:c.length,w:ws.length,wok:ws.every(([a,b])=>[[1,0],[-1,0],[0,1],[0,-1]].filter(([x,y])=>g[b+y][a+x]==='k').length>=3)})}
        const mouth=[];for(let j=13;j<17;j++)for(let i=7;i<13;i++)if('dr'.includes(g[j][i]))mouth.push(1);o[m]={eyes:cs,mouth:mouth.length}}return o}''')
      for k,v in r2.items():
        e=v['eyes'];ok=len(e)==2 and all(c['w']<=1 and c['wok'] for c in e) and v['mouth']>0 and len(set(c['n'] for c in e))==1
        if k in('happy','faint'):ok=ok and all(c['w']==0 for c in e)
        else:ok=ok and (k=='blink' or all(c['w']==1 for c in e))
        res['B:'+k]=ok
        if not ok:print('FAIL B',k,v)
      r={}
    for k,comps in r.items():
      K=2 if V=='A' else 3
      eyes=[c for c in comps if c['y']<4*K+1];mouth=[c for c in comps if c['y']>=4*K+1]
      ok=len(eyes)==2 and len(mouth)<=1 and (k=='happy' or all(c['n']==c['bw']*c['bh'] for c in eyes))
      if k in('idle','sad','faint'):ok=ok and len(mouth)==1
      res[V+':'+k]=ok
      if not ok:print('FAIL',V,k,comps)
    # in-game crops
    pg.click('#start',force=True);pg.wait_for_timeout(1000)
    for st in GAME+['happy','sad','panic','faint']:
      pg.evaluate("st=>{const T=__T;T.S.pos=null;if(['long','short','profit','loss'].includes(st))T.enter(st==='short'?-1:1);if(['happy','sad','panic','faint'].includes(st))T.setMood(st,1)}",st);pg.wait_for_timeout(700)
      if st in('profit','loss'):
        for _ in range(6):pg.evaluate("st=>{const S=__T.S,G=__T.G;if(!S.pos)return;const d=(st==='profit'?-0.5:0.6)*S.pos.bet/S.pos.pv;S.pos.px=G.price+d*S.pos.dir}",st);pg.wait_for_timeout(60)
      fn=f'/workspace/v25_face_{V}_{st}.png';pg.screenshot(path=fn,clip={'x':0,'y':844*0.56,'width':110,'height':110})
      Image.open(fn).resize((440,440),Image.NEAREST).save(fn)
      pg.evaluate("()=>{if(__T.S.pos)__T.S.pos=null}")
  b.close()
print('errs',errs);bad=[k for k,v in res.items() if not v];print('FACECHECK', 'PASS' if not bad else 'FAIL '+str(bad));sys.exit(1 if bad else 0)

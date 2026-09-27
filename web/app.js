const $=id=>document.getElementById(id);
const state={
  running:false,stream:null,language:'en-IN',lastSpeak:0,model:null,modelReady:false,
  detector:null,detectorReady:false,stable:0,lastLabel:null,evidence:0,webConfig:null,
  background:null,lastFrame:null,captures:[],viewPhase:0,lastCapture:0,objectBox:null
};
const phrases={
 en:{ready:"I’m ready. I’ll inspect the scene and collect evidence automatically.",scan:"I’m analyzing the scene now.",done:o=>`I’ve identified ${o}. I fused evidence from multiple views.`,unknown:"I don’t have enough evidence yet. I’ll keep looking.",guide:t=>t},
 hi:{ready:"मैं तैयार हूँ। मैं दृश्य को समझकर अपने आप प्रमाण एकत्र करूँगा।",scan:"मैं अभी दृश्य का विश्लेषण कर रहा हूँ।",done:o=>`मैंने ${o} पहचाना है। मैंने कई दृश्यों के प्रमाण जोड़े हैं।`,unknown:"अभी पर्याप्त प्रमाण नहीं हैं। मैं और जाँच करूँगा।",guide:t=>t},
 te:{ready:"నేను సిద్ధంగా ఉన్నాను. దృశ్యాన్ని అర్థం చేసుకుని ఆధారాలను సేకరిస్తాను.",scan:"నేను ఇప్పుడు దృశ్యాన్ని విశ్లేషిస్తున్నాను.",done:o=>`నేను ${o}ని గుర్తించాను. అనేక దృశ్యాల ఆధారాలను కలిపాను.`,unknown:"ఇంకా సరిపడా ఆధారాలు లేవు. నేను మరింత పరిశీలిస్తాను.",guide:t=>t},
 ta:{ready:"நான் தயாராக இருக்கிறேன். காட்சியைப் புரிந்து ஆதாரங்களைச் சேகரிப்பேன்.",scan:"நான் இப்போது காட்சியை ஆய்வு செய்கிறேன்.",done:o=>`நான் ${o} என்பதை அடையாளம் கண்டேன். பல காட்சிகளின் ஆதாரங்களை இணைத்தேன்.`,unknown:"இன்னும் போதுமான ஆதாரம் இல்லை. தொடர்ந்து ஆய்வு செய்கிறேன்.",guide:t=>t},
 gu:{ready:"હું તૈયાર છું. હું દૃશ્યને સમજીને આપમેળે પુરાવા એકત્ર કરીશ.",scan:"હું હવે દૃશ્યનું વિશ્લેષણ કરી રહ્યો છું.",done:o=>`મેં ${o} ઓળખ્યું છે. મેં ઘણા દૃશ્યોના પુરાવા જોડ્યા છે.`,unknown:"હજુ પૂરતા પ્રમાણ નથી. હું વધુ તપાસ કરીશ.",guide:t=>t}
};
function speak(t){if(!window.speechSynthesis)return;const u=new SpeechSynthesisUtterance(t);u.lang=state.language;u.rate=.94;window.speechSynthesis.cancel();window.speechSynthesis.speak(u)}
function say(k,a){const p=phrases[state.language.slice(0,2)]||phrases.en,t=typeof p[k]==='function'?p[k](a):p[k];$('conversation').textContent=t;if(Date.now()-state.lastSpeak>2200){state.lastSpeak=Date.now();speak(t)}}
function analyseFrame(){
 const v=$('camera'),c=document.createElement('canvas');c.width=160;c.height=100;
 const x=c.getContext('2d');x.drawImage(v,0,0,160,100);const d=x.getImageData(0,0,160,100).data;
 let s=0,dark=0,bright=0;for(let i=0;i<d.length;i+=4){const z=(d[i]+d[i+1]+d[i+2])/3;s+=z;if(z<25)dark++;if(z>245)bright++}
 const n=d.length/4,m=s/n,lighting=m<55||dark/n>.3?'low light':m>220||bright/n>.18?'overexposed':'balanced';
 $('lighting').textContent='LIGHTING — '+lighting;$('lightValue').textContent=lighting;return lighting
}
function featureFromCanvas(canvas){
 const cfg=state.webConfig,n=cfg.image_size,c=document.createElement('canvas');c.width=n;c.height=n;
 c.getContext('2d').drawImage(canvas,0,0,n,n);const ctx=c.getContext('2d'),rgb=ctx.getImageData(0,0,n,n).data;
 const h=new Float32Array(288),gray=new Float32Array(n*n);
 for(let y=0;y<n;y++)for(let x=0;x<n;x++){const i=(y*n+x)*4,r=rgb[i],g=rgb[i+1],b=rgb[i+2],mx=Math.max(r,g,b),mn=Math.min(r,g,b),delta=mx-mn;let hh=0;
   if(delta){if(mx===r)hh=((g-b)/delta)%6;else if(mx===g)hh=(b-r)/delta+2;else hh=(r-g)/delta+4;hh*=30;if(hh<0)hh+=180}
   const ss=mx?delta/mx*255:0;h[Math.min(11,Math.floor(hh/15))*24+Math.min(5,Math.floor(ss/256*6))*4+Math.min(3,Math.floor(mx/256*4))]++;
   gray[y*n+x]=.114*b+.587*g+.299*r}
 let hs=h.reduce((a,b)=>a+b,0);for(let i=0;i<h.length;i++)h[i]/=hs+1e-8;
 const gh=new Float32Array(9),kx=[-1,0,1,-2,0,2,-1,0,1],ky=[-1,-2,-1,0,0,0,1,2,1];
 for(let y=1;y<n-1;y++)for(let x=1;x<n-1;x++){let gx=0,gy=0,k=0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++,k++){const z=gray[(y+dy)*n+x+dx];gx+=z*kx[k];gy+=z*ky[k]}let a=Math.atan2(gy,gx)*180/Math.PI;if(a<0)a+=360;gh[Math.min(8,Math.floor(a/40))]+=Math.hypot(gx,gy)}
 let gs=gh.reduce((a,b)=>a+b,0);for(let i=0;i<9;i++)gh[i]/=gs+1e-8;
 const sm=document.createElement('canvas');sm.width=32;sm.height=32;sm.getContext('2d').drawImage(c,0,0,32,32);
 const sd=sm.getContext('2d').getImageData(0,0,32,32).data,tx=[];
 for(let y=0;y<32;y+=8)for(let x=0;x<32;x+=8){let m=0,m2=0;for(let dy=0;dy<8;dy++)for(let dx=0;dx<8;dx++){const i=((y+dy)*32+x+dx)*4,z=(.114*sd[i+2]+.587*sd[i+1]+.299*sd[i])/255;m+=z;m2+=z*z}m/=64;tx.push(m,Math.sqrt(Math.max(0,m2/64-m*m)))}
 const out=Float32Array.from([...h,...gh,...tx]);if(out.length!==cfg.feature_length)throw Error('feature contract mismatch');return out
}
function feature(){
 const v=$('camera'),vw=v.videoWidth||1280,vh=v.videoHeight||720,c=document.createElement('canvas');c.width=vw;c.height=vh;
 const ctx=c.getContext('2d');ctx.drawImage(v,0,0,vw,vh);
 if(state.objectBox){const b=state.objectBox;const x=Math.max(0,b.x),y=Math.max(0,b.y),w=Math.min(vw-x,b.w),h=Math.min(vh-y,b.h);if(w>10&&h>10){const crop=document.createElement('canvas');crop.width=w;crop.height=h;crop.getContext('2d').drawImage(c,x,y,w,h,0,0,w,h);return featureFromCanvas(crop)}}
 const rw=vw*state.webConfig.roi.width_ratio,rh=vh*state.webConfig.roi.height_ratio;
 const crop=document.createElement('canvas');crop.width=rw;crop.height=rh;crop.getContext('2d').drawImage(c,(vw-rw)/2,(vh-rh)/2,rw,rh,0,0,rw,rh);
 return featureFromCanvas(crop)
}
function predict(f){const m=state.model,z=[];for(let k=0;k<m.labels.length;k++){let s=m.b[k];for(let j=0;j<f.length;j++)s+=(f[j]-m.mean[j])/Math.max(m.std[j],1e-8)*m.W[j][k];z.push(s/Math.max(m.temperature,1e-3))}
 const mx=Math.max(...z),e=z.map(v=>Math.exp(v-mx)),sum=e.reduce((a,b)=>a+b,0),p=e.map(v=>v/sum),o=p.map((v,i)=>[v,i]).sort((a,b)=>b[0]-a[0]);return{label:m.labels[o[0][1]],confidence:o[0][0],margin:o[0][0]-o[1][0]}
}
function colour(){
 const c=document.createElement('canvas');c.width=64;c.height=64;c.getContext('2d').drawImage($('camera'),0,0,64,64);
 const d=c.getContext('2d').getImageData(0,0,64,64).data;let r=0,g=0,b=0,n=0;
 for(let i=0;i<d.length;i+=16){r+=d[i];g+=d[i+1];b+=d[i+2];n++}r/=n;g/=n;b/=n;const mx=Math.max(r,g,b),mn=Math.min(r,g,b);
 return mx-mn<28?(mx<70?'black':mx>190?'white':'silver/grey'):g>r*1.15&&g>b*1.1?'green':b>r*1.2?'blue':r>g*1.25?'red':'neutral'
}
function sceneMask(){
 const v=$('camera'),w=v.videoWidth||1280,h=v.videoHeight||720,c=document.createElement('canvas');c.width=160;c.height=100;
 const x=c.getContext('2d');x.drawImage(v,0,0,160,100);const d=x.getImageData(0,0,160,100).data;
 let minX=160,minY=100,maxX=0,maxY=0,count=0;
 if(state.background){const bd=state.background;for(let i=0;i<d.length;i+=4){const dr=Math.abs(d[i]-bd[i]),dg=Math.abs(d[i+1]-bd[i+1]),db=Math.abs(d[i+2]-bd[i+2]);if((dr+dg+db)>72){const p=i/4,px=p%160,py=Math.floor(p/160);count++;minX=Math.min(minX,px);maxX=Math.max(maxX,px);minY=Math.min(minY,py);maxY=Math.max(maxY,py)}}}
 if(count<80)return null;
 return{x:minX/160*w,y:minY/100*h,w:(maxX-minX+1)/160*w,h:(maxY-minY+1)/100*h,area:count/(160*100),cx:(minX+maxX)/320,cy:(minY+maxY)/200}
}
function guidance(mask){
 if(!mask)return{action:'move_closer',text:'Place one object clearly inside the guide.'};
 if(mask.area<.08)return{action:'move_closer',text:'Move the object a little closer.'};
 if(mask.area>.65)return{action:'move_back',text:'Move a little farther away.'};
 if(mask.cx<.35)return{action:'turn_right',text:'Center the object, then turn it slightly right.'};
 if(mask.cx>.65)return{action:'turn_left',text:'Center the object, then turn it slightly left.'};
 if(mask.cy<.30)return{action:'lower_camera',text:'Lower the camera slightly.'};
 if(mask.cy>.72)return{action:'raise_camera',text:'Raise the camera slightly.'};
 return{action:'capture',text:'Good view. Hold steady while I capture this view.'};
}
function excludePerson(dets,box){
 if(!box)return null;const people=dets.filter(x=>x.class==='person'&&x.score>.55);if(!people.length)return box;
 const overlaps=people.some(p=>{const [x,y,w,h]=p.bbox;const ix=Math.max(0,Math.min(box.x+box.w,x+w)-Math.max(box.x,x));const iy=Math.max(0,Math.min(box.y+box.h,y+h)-Math.max(box.y,y));return ix*iy>box.w*box.h*.25});return overlaps?null:box
}
function progress(p,mask){
 if(state.lastLabel===p.label)state.stable++;else{state.lastLabel=p.label;state.stable=1}
 state.evidence=Math.min(7,state.stable);$('evidenceBar').style.width=(state.evidence/7*100)+'%';$('evidenceText').textContent=state.evidence+' / 7 consistent observations';
 if(mask)$('conditionText').textContent='object view '+(state.captures.length+1)+' / 4'
}
function captureView(p,mask){
 const now=Date.now();if(!mask||now-state.lastCapture<900||state.captures.length>=4)return;
 if(state.captures.length===0&&mask.cx>.42&&mask.cx<.58){state.captures.push({label:p.label,confidence:p.confidence,view:'front'});state.lastCapture=now}
 else if(state.captures.length===1&&mask.cx<.48){state.captures.push({label:p.label,confidence:p.confidence,view:'left'});state.lastCapture=now}
 else if(state.captures.length===2&&mask.cx>.52){state.captures.push({label:p.label,confidence:p.confidence,view:'right'});state.lastCapture=now}
 else if(state.captures.length===3&&mask.cx>.42&&mask.cx<.58){state.captures.push({label:p.label,confidence:p.confidence,view:'final'});state.lastCapture=now}
 if(state.captures.length<4&&state.captures.length>0)$('guidance').textContent=['Turn slightly left for another view.','Turn slightly right for another view.','Return to center for the final view.'][state.captures.length-1]||'Hold steady.';
 if(state.captures.length===4){$('guidance').textContent='Four views captured. Evidence fused.';say('done',p.label.replaceAll('_',' '))}
}
async function loadModel(){
 state.webConfig=await fetch('model_config.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('model config unavailable');return r.json()});
 state.model=await fetch('model.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('model unavailable');return r.json()});
 if(state.model.feature_length!==state.webConfig.feature_length||state.model.labels.join('|')!==state.webConfig.labels.join('|'))throw Error('model/config contract mismatch');
 state.modelReady=true;$('eval').textContent='Browser inference: trained model active'
}
function frameBackground(){
 const c=document.createElement('canvas');c.width=160;c.height=100;c.getContext('2d').drawImage($('camera'),0,0,160,100);state.background=c.getContext('2d').getImageData(0,0,160,100).data
}
async function process(){
 if(!state.running)return;
 const lighting=analyseFrame();let det=[];
 if(state.detectorReady)try{det=await state.detector.detect($('camera'))}catch(e){}
 const person=det.find(x=>x.class==='person'&&x.score>.6);
 const mask=sceneMask();state.objectBox=excludePerson(det,mask);
 $('scene').textContent=state.detectorReady?'SCENE — person filter + motion region':'SCENE — motion region';
 if(person&&!state.objectBox){state.stable=0;state.lastLabel=null;$('systemStatus').textContent='PERSON / OBJECT OCCLUDED';$('guidance').textContent='Move your hand or body away from the object.'}
 else if(state.modelReady){
   try{const p=predict(feature()),threshold=Math.max(state.webConfig.confidence_threshold,state.model.unknown_threshold);
     if(p.confidence>=threshold&&p.margin>=state.webConfig.margin_threshold){progress(p,mask);$('object').textContent=p.label.replaceAll('_',' ');$('confidence').textContent=Math.round(p.confidence*100)+'%';$('colour').textContent=colour();$('systemStatus').textContent=state.captures.length>=4?'VERIFIED':'COLLECTING';const g=guidance(mask);$('guidance').textContent=g.text;captureView(p,mask);if(state.captures.length<4)say('scan')}
     else{state.stable=0;state.lastLabel=null;$('systemStatus').textContent='UNCERTAIN';$('guidance').textContent=guidance(mask).text;say('unknown')}
   }catch(e){$('systemStatus').textContent='INFERENCE ERROR';$('eval').textContent=e.message}
 }else $('systemStatus').textContent='MODEL UNAVAILABLE';
 requestAnimationFrame(process)
}
async function start(){
 if(state.running)return;try{
  state.stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720},frameRate:{ideal:30}},audio:false});
  $('camera').srcObject=state.stream;state.running=true;$('systemStatus').textContent='PERCEIVING';say('scan');await loadModel();await new Promise(r=>setTimeout(r,500));frameBackground();
  try{state.detector=await cocoSsd.load();state.detectorReady=true}catch(e){state.detectorReady=false}
  process()
 }catch(e){$('systemStatus').textContent='CAMERA/MODEL UNAVAILABLE';$('eval').textContent=e.message;say('unknown')}
}
function reset(){state.stable=0;state.lastLabel=null;state.evidence=0;state.captures=[];state.objectBox=null;state.background=null;$('evidenceBar').style.width='0';$('evidenceText').textContent='0 / 7 consistent observations';$('conditionText').textContent='adaptive';['object','colour','confidence'].forEach(id=>$(id).textContent='—');$('systemStatus').textContent=state.running?'PERCEIVING':'READY';$('guidance').textContent='Start perception and place an object in view.';say('ready')}
$('start').onclick=start;$('capture').onclick=()=>{if(state.running)say('scan');else say('ready')};$('reset').onclick=reset;$('language').onchange=e=>{state.language=e.target.value;say('ready')};say('ready');

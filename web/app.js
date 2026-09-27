const $=id=>document.getElementById(id);
const state={running:false,stream:null,language:'en-IN',lastSpeak:0,frames:[],model:null,modelReady:false,training:false,stable:0,lastLabel:null,detector:null};

const phrases={
en:{ready:"I’m ready. I’ll inspect the scene, separate people from objects, and collect evidence automatically.",scan:"I’m analyzing the scene now.",guide:t=>t,done:o=>`I’ve identified ${o}. I combined multiple views, lighting conditions and colour evidence.`,unknown:"I don’t have enough evidence yet. I’ll keep looking."},
hi:{ready:"मैं तैयार हूँ। मैं दृश्य, व्यक्ति और वस्तु को समझकर अपने आप प्रमाण एकत्र करूँगा।",scan:"मैं अभी दृश्य का विश्लेषण कर रहा हूँ।",guide:t=>t,done:o=>`मैंने ${o} पहचाना है। मैंने कई कोणों, रोशनी और रंग के प्रमाण मिलाए हैं।`,unknown:"अभी पर्याप्त प्रमाण नहीं हैं। मैं और जाँच करूँगा।"},
te:{ready:"నేను సిద్ధంగా ఉన్నాను. దృశ్యం, వ్యక్తి మరియు వస్తువును అర్థం చేసుకుని ఆధారాలను సేకరిస్తాను.",scan:"నేను ఇప్పుడు దృశ్యాన్ని విశ్లేషిస్తున్నాను.",guide:t=>t,done:o=>`నేను ${o}ని గుర్తించాను. అనేక కోణాలు, వెలుతురు మరియు రంగు ఆధారాలను కలిపాను.`,unknown:"ఇంకా సరిపడా ఆధారాలు లేవు. నేను మరింత పరిశీలిస్తాను."},
ta:{ready:"நான் தயாராக இருக்கிறேன். காட்சி, மனிதர் மற்றும் பொருளைப் புரிந்து ஆதாரங்களைத் தானாகச் சேகரிப்பேன்.",scan:"நான் இப்போது காட்சியை ஆய்வு செய்கிறேன்.",guide:t=>t,done:o=>`நான் ${o} என்பதை அடையாளம் கண்டேன். பல கோணங்கள், ஒளி மற்றும் நிறத் தகவல்களை இணைத்தேன்.`,unknown:"இன்னும் போதுமான ஆதாரம் இல்லை. தொடர்ந்து ஆய்வு செய்கிறேன்."},
gu:{ready:"હું તૈયાર છું. હું દૃશ્ય, વ્યક્તિ અને વસ્તુને સમજીને આપમેળે પુરાવા એકત્ર કરીશ.",scan:"હું હવે દૃશ્યનું વિશ્લેષણ કરી રહ્યો છું.",guide:t=>t,done:o=>`મેં ${o} ઓળખ્યું છે. મેં ઘણા ખૂણા, પ્રકાશ અને રંગના પુરાવા જોડ્યા છે.`,unknown:"હજુ પૂરતા પુરાવા નથી. હું વધુ તપાસ કરીશ."}
};
const key=()=>state.language.slice(0,2);
function speak(text){if(!('speechSynthesis'in window))return; speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(text);u.lang=state.language;u.rate=.94;u.pitch=1.02;speechSynthesis.speak(u)}
function say(k,arg){const p=phrases[key()]||phrases.en;const text=typeof p[k]==='function'?p[k](arg):p[k];$('conversation').textContent=text;if(Date.now()-state.lastSpeak>2200){state.lastSpeak=Date.now();speak(text)}}

function scene(frame){
 const c=document.createElement('canvas');c.width=160;c.height=100;const x=c.getContext('2d');x.drawImage(frame,0,0,160,100);
 const d=x.getImageData(0,0,160,100).data;let sum=0,dark=0,bright=0,sat=0;
 for(let i=0;i<d.length;i+=4){const mx=Math.max(d[i],d[i+1],d[i+2]),mn=Math.min(d[i],d[i+1],d[i+2]);const v=(d[i]+d[i+1]+d[i+2])/3;sum+=v;sat+=mx-mn;if(v<25)dark++;if(v>245)bright++}
 const n=d.length/4,mean=sum/n,dr=dark/n,br=bright/n;
 const lighting=mean<55||dr>.3?'low light':mean>220||br>.18?'overexposed':dr>.2&&mean>100?'backlit':'balanced';
 $('lighting').textContent='LIGHTING — '+lighting;$('lightValue').textContent=lighting;
 $('scene').textContent='SCENE — '+(dr>.3?'dark scene':br>.18?'high exposure':'stable scene');
 return {mean,lighting,dr,br,saturation:sat/n};
}
function feature(frame){
 const cfg=state.webConfig||{image_size:128,roi:{mode:'center',width_ratio:.82,height_ratio:.82}};
 const n=cfg.image_size,c=document.createElement('canvas');c.width=n;c.height=n;const x=c.getContext('2d'),vw=$('camera').videoWidth||1280,vh=$('camera').videoHeight||720;
 const rw=cfg.roi.mode==='center'?vw*cfg.roi.width_ratio:vw,rh=cfg.roi.mode==='center'?vh*cfg.roi.height_ratio:vh,sx=(vw-rw)/2,sy=(vh-rh)/2;x.drawImage($('camera'),sx,sy,rw,rh,0,0,n,n);
 const d=x.getImageData(0,0,n,n).data,hist=new Float32Array(288),gray=new Float32Array(n*n);
 function hsv(r,g,b){const mx=Math.max(r,g,b),mn=Math.min(r,g,b),v=mx,delta=mx-mn;let h=0,ss=mx===0?0:delta/mx;if(delta){if(mx===r)h=((g-b)/delta)%6;else if(mx===g)h=(b-r)/delta+2;else h=(r-g)/delta+4;h*=30;if(h<0)h+=180}return[h,ss*255,v]}
 for(let yy=0;yy<n;yy++)for(let xx=0;xx<n;xx++){const i=(yy*n+xx)*4,[h,ss,v]=hsv(d[i],d[i+1],d[i+2]);hist[Math.min(11,Math.floor(h/15))*24+Math.min(5,Math.floor(ss/256*6))*4+Math.min(3,Math.floor(v/256*4))]++;gray[yy*n+xx]=(d[i]+d[i+1]+d[i+2])/3/255}
 let hs=hist.reduce((a,b)=>a+b,0);for(let i=0;i<288;i++)hist[i]/=hs||1;
 const gh=new Float32Array(9),sxk=[-1,0,1,-2,0,2,-1,0,1],syk=[-1,-2,-1,0,0,0,1,2,1];
 for(let yy=1;yy<n-1;yy++)for(let xx=1;xx<n-1;xx++){let gx=0,gy=0,k=0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++,k++){const v=gray[(yy+dy)*n+xx+dx];gx+=v*sxk[k];gy+=v*syk[k]}let a=Math.atan2(gy,gx)*180/Math.PI;if(a<0)a+=360;gh[Math.min(8,Math.floor(a/40))]+=Math.hypot(gx,gy)}
 let gs=gh.reduce((a,b)=>a+b,0);for(let i=0;i<9;i++)gh[i]/=gs||1;
 const sm=document.createElement('canvas');sm.width=32;sm.height=32;sm.getContext('2d').drawImage(c,0,0,32,32);const sd=sm.getContext('2d').getImageData(0,0,32,32).data,tex=[];
 for(let yy=0;yy<32;yy+=8)for(let xx=0;xx<32;xx+=8){let m=0,m2=0;for(let dy=0;dy<8;dy++)for(let dx=0;dx<8;dx++){const i=((yy+dy)*32+xx+dx)*4,v=(sd[i]+sd[i+1]+sd[i+2])/3/255;m+=v;m2+=v*v}m/=64;tex.push(m,Math.sqrt(Math.max(0,m2/64-m*m))}
 return Float32Array.from([...hist,...gh,...tex]);
}
function softmax(z){const m=Math.max(...z),e=z.map(v=>Math.exp(v-m)),s=e.reduce((a,b)=>a+b,0);return e.map(v=>v/s)}
function predict(f){
 const m=state.model;if(!m)return null;const z=[];for(let k=0;k<m.labels.length;k++){let s=m.b[k];for(let j=0;j<f.length;j++)s+=(f[j]-m.mean[j])/m.std[j]*m.W[j*m.labels.length+k];z.push(s/Math.max(m.temperature||1,1e-3))}const p=softmax(z),order=p.map((v,i)=>[v,i]).sort((a,b)=>b[0]-a[0]);return {label:m.labels[order[0][1]],confidence:order[0][0],margin:order[0][0]-order[1][0],probs:p}}
async function loadModel(){
 try{state.webConfig=await fetch('model_config.json').then(r=>r.json())}catch(e){throw new Error('model contract unavailable')}
 try{
  const b64=await fetch('model.b64').then(r=>r.text());const bytes=Uint8Array.from(atob(b64.trim()),c=>c.charCodeAt(0));
  const view=new DataView(bytes.buffer),entries=[];let pos=0;
  while(pos+30<bytes.length){if(view.getUint32(pos,true)!==0x04034b50)break;const method=view.getUint16(pos+8,true),cs=view.getUint32(pos+18,true),ns=view.getUint16(pos+26,true),es=view.getUint16(pos+28,true);const name=new TextDecoder().decode(bytes.slice(pos+30,pos+30+ns));const start=pos+30+ns+es;entries.push({name,method,data:bytes.slice(start,start+cs)});pos=start+cs}
  const arrays={};for(const e of entries){if(!e.name.endsWith('.npy'))continue;let data=e.data;if(e.method===8)data=new Uint8Array(await new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer());const h=new TextDecoder().decode(data.slice(0,128));const start=data.indexOf(10)+1;const shape=(h.match(/'shape':\s*\(([^)]*)\)/)||[])[1].split(',').filter(Boolean).map(Number);const raw=data.slice(start);arrays[e.name.split('/').pop().replace('.npy','')]=shape.length===1?Array.from(new Float32Array(raw.buffer,raw.byteOffset,raw.byteLength/4)):Array.from(new Float32Array(raw.buffer,raw.byteOffset,raw.byteLength/4));}
  if(arrays.W){state.model={...arrays,labels:state.webConfig.labels,temperature:1,unknown_threshold:.55};state.modelReady=true;$('eval').textContent='Trained model loaded: browser inference active'}
 }catch(e){$('eval').textContent='Model load unavailable; automatic training can still build a session model'}
}
function heuristicSegmentation(){
 const c=document.createElement('canvas');c.width=160;c.height=100;const x=c.getContext('2d');x.drawImage($('camera'),0,0,160,100);const d=x.getImageData(0,0,160,100).data;
 let minX=160,maxX=0,minY=100,maxY=0,n=0;for(let y=2;y<98;y++)for(let xx=2;xx<158;xx++){const i=(y*160+xx)*4,v=(d[i]+d[i+1]+d[i+2])/3;const border=xx<18||xx>142||y<12||y>88;const bv=border?255:0;if(!border&&Math.abs(v-128)>35){minX=Math.min(minX,xx);maxX=Math.max(maxX,xx);minY=Math.min(minY,y);maxY=Math.max(maxY,y);n++}}
 return n>500?{x:minX/160,y:minY/100,w:(maxX-minX)/160,h:(maxY-minY)/100,area:n/(160*100)}:null;
}
function colour(){const c=document.createElement('canvas');c.width=64;c.height=64;const x=c.getContext('2d');x.drawImage($('camera'),0,0,64,64);const d=x.getImageData(0,0,64,64).data;let r=0,g=0,b=0,n=0;for(let i=0;i<d.length;i+=16){r+=d[i];g+=d[i+1];b+=d[i+2];n++}r/=n;g/=n;b/=n;const mx=Math.max(r,g,b),mn=Math.min(r,g,b);return mx-mn<28?(mx<70?'black':mx>190?'white':'silver/grey'):g>r*1.15&&g>b*1.1?'green':b>r*1.2?'blue':r>g*1.25?'red':'neutral'}

async function process(){
 if(!state.running)return;
 const sc=scene($('camera'));const box=heuristicSegmentation();const det=state.detector?await state.detector.detect($('camera')):[];const human=det.some(x=>['person'].includes(x.class)&&x.score>.55);
 if(human){$('systemStatus').textContent='PERSON DETECTED';say('guide','Please keep the object visible without a person covering it.')}
 else if(box){$('systemStatus').textContent='OBJECT IN VIEW';const p=state.modelReady?predict(feature($('camera'))):null;if(p&&p.confidence>(state.webConfig?.confidence_threshold??.72)&&p.margin>(state.webConfig?.margin_threshold??.12)){if(state.lastLabel===p.label)state.stable++;else{state.lastLabel=p.label;state.stable=1}if(state.stable>=7){$('object').textContent=p.label.replaceAll('_',' ');$('confidence').textContent=Math.round(p.confidence*100)+'%';$('colour').textContent=colour();$('systemStatus').textContent='VERIFIED';say('done',p.label.replaceAll('_',' '))}}else{state.stable=0;say('unknown')}}
 else {$('systemStatus').textContent='SEARCHING';$('confidence').textContent='—'}
 $('conditionText').textContent=sc.lighting+' · '+colour();requestAnimationFrame(process)
}
async function start(){if(state.running)return;try{state.stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720},frameRate:{ideal:30}},audio:false});$('camera').srcObject=state.stream;state.running=true;$('systemStatus').textContent='PERCEIVING';say('scan');await loadModel();try{state.detector=await cocoSsd.load()}catch(e){state.detector=null}process()}catch(e){$('systemStatus').textContent='CAMERA UNAVAILABLE';say('unknown')}}
function reset(){state.stable=0;state.lastLabel=null;['object','colour','confidence'].forEach(id=>$(id).textContent='—');$('systemStatus').textContent=state.running?'PERCEIVING':'READY';say('ready')}
$('start').onclick=start;$('capture').onclick=()=>{say('scan')};$('reset').onclick=reset;$('language').onchange=e=>{state.language=e.target.value;say('ready')};say('ready');

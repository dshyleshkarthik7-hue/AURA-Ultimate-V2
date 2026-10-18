const $=id=>document.getElementById(id);
const state={running:false,stream:null,language:"en-IN",lastSpeak:0,model:null,modelReady:false,detector:null,detectorReady:false,stable:0,lastLabel:null,evidence:0,webConfig:null,background:null,captures:[],lastCapture:0,objectBox:null,viewChanged:false,viewStableSince:0,lastSignature:null,cvReady:false};
const phrases={en:{ready:"I’m ready. I’ll inspect the scene and collect evidence automatically.",scan:"I’m analyzing the scene now.",done:o=>`I’ve identified ${o}. I fused evidence from multiple stabilized views.`,unknown:"I don’t have enough evidence yet. I’ll keep looking."},hi:{ready:"मैं तैयार हूँ। मैं दृश्य को समझकर अपने आप प्रमाण एकत्र करूँगा।",scan:"मैं अभी दृश्य का विश्लेषण कर रहा हूँ।",done:o=>`मैंने ${o} पहचाना है। मैंने कई स्थिर दृश्यों के प्रमाण जोड़े हैं।`,unknown:"अभी पर्याप्त प्रमाण नहीं हैं। मैं और जाँच करूँगा।"},te:{ready:"నేను సిద్ధంగా ఉన్నాను. దృశ్యాన్ని అర్థం చేసుకుని ఆధారాలను సేకరిస్తాను.",scan:"నేను ఇప్పుడు దృశ్యాన్ని విశ్లేషిస్తున్నాను.",done:o=>`నేను ${o}ని గుర్తించాను. అనేక స్థిర దృశ్యాల ఆధారాలను కలిపాను.`,unknown:"ఇంకా సరిపడా ఆధారాలు లేవు. నేను మరింత పరిశీలిస్తాను."},ta:{ready:"நான் தயாராக இருக்கிறேன். காட்சியைப் புரிந்து ஆதாரங்களைச் சேகரிப்பேன்.",scan:"நான் இப்போது காட்சியை ஆய்வு செய்கிறேன்.",done:o=>`நான் ${o} என்பதை அடையாளம் கண்டேன். பல நிலையான காட்சிகளின் ஆதாரங்களை இணைத்தேன்.`,unknown:"இன்னும் போதுமான ஆதாரம் இல்லை. தொடர்ந்து ஆய்வு செய்கிறேன்."},gu:{ready:"હું તૈયાર છું. હું દૃશ્યને સમજીને આપમેળે પુરાવા એકત્ર કરીશ.",scan:"હું હવે દૃશ્યનું વિશ્લેષણ કરી રહ્યો છું.",done:o=>`મેં ${o} ઓળખ્યું છે. મેં ઘણા સ્થિર દૃશ્યોના પુરાવા જોડ્યા છે.`,unknown:"હજુ પૂરતા પ્રમાણ નથી. હું વધુ તપાસ કરીશ."}};
function speak(t){if(!window.speechSynthesis)return;const u=new SpeechSynthesisUtterance(t);u.lang=state.language;u.rate=.94;window.speechSynthesis.cancel();window.speechSynthesis.speak(u)}
function say(k,a){const p=phrases[state.language.slice(0,2)]||phrases.en,t=typeof p[k]==="function"?p[k](a):p[k];$("conversation").textContent=t;if(Date.now()-state.lastSpeak>2200){state.lastSpeak=Date.now();speak(t)}}
function cvReady(){return (state.cvReady||window.__AURA_CV_READY__===true)&&typeof cv!=="undefined"&&!!cv.Mat}
function waitForCv(timeout=15000){return new Promise((resolve,reject)=>{const s=Date.now(),tick=()=>{if(cvReady())return resolve();if(Date.now()-s>timeout)return reject(new Error("OpenCV.js did not initialize"));setTimeout(tick,50)};tick()})}
function analyseFrame(){const v=$("camera"),c=document.createElement("canvas");c.width=160;c.height=100;const x=c.getContext("2d");x.drawImage(v,0,0,160,100);const d=x.getImageData(0,0,160,100).data;let s=0,dark=0,bright=0;for(let i=0;i<d.length;i+=4){const z=(d[i]+d[i+1]+d[i+2])/3;s+=z;if(z<25)dark++;if(z>245)bright++}const n=d.length/4,m=s/n,l=m<55||dark/n>.3?"low light":m>220||bright/n>.18?"overexposed":"balanced";$("lighting").textContent="LIGHTING — "+l;$("lightValue").textContent=l;return l}
function featureFromCanvas(canvas){if(!cvReady())throw new Error("OpenCV.js is not ready");const cfg=state.webConfig||{},size=cfg.image_size||128,roi=cfg.roi||{},src=cv.imread(canvas);let img=new cv.Mat(),roiMat=null,hsv=null,hist=null,channels=null,mask=null,gray=null,gx=null,gy=null,mag=null,ang=null,small=null;try{const w=src.cols,h=src.rows;if((roi.mode||"center")==="center"){const rw=Math.max(1,Math.min(w,Math.floor(w*(roi.width_ratio??1)))),rh=Math.max(1,Math.min(h,Math.floor(h*(roi.height_ratio??1)))),x=Math.floor((w-rw)/2),y=Math.floor((h-rh)/2);roiMat=src.roi(new cv.Rect(x,y,rw,rh));cv.resize(roiMat,img,new cv.Size(size,size),0,0,cv.INTER_AREA)}else cv.resize(src,img,new cv.Size(size,size),0,0,cv.INTER_AREA);hsv=new cv.Mat();cv.cvtColor(img,hsv,cv.COLOR_BGR2HSV);hist=new cv.Mat();channels=new cv.MatVector();channels.push_back(hsv);mask=new cv.Mat();try{hist=cv.calcHist(channels,[0,1,2],mask,[12,6,4],[0,180,0,256,0,256]);}catch(e){const hd=new Float32Array(288);for(let i=0;i<hsv.rows*hsv.cols;i++){const p=i*3,hv=hsv.data[p],sv=hsv.data[p+1],vv=hsv.data[p+2],hb=Math.min(11,Math.floor(hv*12/180)),sb=Math.min(5,Math.floor(sv*6/256)),vb=Math.min(3,Math.floor(vv*4/256));hd[(hb*6+sb)*4+vb]++}hist.delete();hist=null;hist={data32F:hd,delete(){}}}const histData=hist.data32F;let histSum=0;for(const v of histData)histSum+=v;const histVec=Array.from(histData,v=>v/(histSum+1e-8));gray=new cv.Mat();cv.cvtColor(img,gray,cv.COLOR_BGR2GRAY);gx=new cv.Mat();gy=new cv.Mat();cv.Sobel(gray,gx,cv.CV_32F,1,0,3);cv.Sobel(gray,gy,cv.CV_32F,0,1,3);mag=new cv.Mat();ang=new cv.Mat();cv.cartToPolar(gx,gy,mag,ang,true);const gradHist=new Float64Array(9),angData=ang.data32F,magData=mag.data32F;for(let i=0;i<angData.length;i++){const angleDeg=((angData[i]%360)+360)%360;const bin=Math.min(8,Math.floor(angleDeg/40));gradHist[bin]+=magData[i]}let gradSum=0;for(const v of gradHist)gradSum+=v;const gradVec=Array.from(gradHist,v=>v/(gradSum+1e-8));small=new cv.Mat();cv.resize(gray,small,new cv.Size(32,32),0,0,cv.INTER_AREA);const texture=[],smallData=small.data;for(let yy=0;yy<32;yy+=8)for(let xx=0;xx<32;xx+=8){let meanSum=0;for(let y=yy;y<yy+8;y++)for(let x=xx;x<xx+8;x++)meanSum+=smallData[y*32+x]/255;const mean=meanSum/64;let varianceSum=0;for(let y=yy;y<yy+8;y++)for(let x=xx;x<xx+8;x++){const v=smallData[y*32+x]/255;varianceSum+=(v-mean)*(v-mean)}texture.push(mean,Math.sqrt(varianceSum/64))}const out=Float32Array.from([...histVec,...gradVec,...texture]);if(out.length!==329||!Array.from(out).every(Number.isFinite))throw new Error("feature contract mismatch");return out}finally{src.delete();if(roiMat)roiMat.delete();img.delete();if(hsv)hsv.delete();if(hist&&typeof hist.delete==="function")hist.delete();if(channels)channels.delete();if(mask)mask.delete();if(gray)gray.delete();if(gx)gx.delete();if(gy)gy.delete();if(mag)mag.delete();if(ang)ang.delete();if(small)small.delete()}}
function makeFrameCanvas(){const v=$("camera"),c=document.createElement("canvas");c.width=v.videoWidth||1280;c.height=v.videoHeight||720;c.getContext("2d").drawImage(v,0,0,c.width,c.height);return c}
function feature(){const c=makeFrameCanvas(),v=c.width,h=c.height,b=state.objectBox||{x:v*(1-state.webConfig.roi.width_ratio)/2,y:h*(1-state.webConfig.roi.height_ratio)/2,w:v*state.webConfig.roi.width_ratio,h:h*state.webConfig.roi.height_ratio},crop=document.createElement("canvas");crop.width=Math.max(1,Math.round(b.w));crop.height=Math.max(1,Math.round(b.h));crop.getContext("2d").drawImage(c,b.x,b.y,b.w,b.h,0,0,crop.width,crop.height);return featureFromCanvas(crop)}
function predict(f){const m=state.model,z=[];for(let k=0;k<m.labels.length;k++){let s=m.b[k];for(let j=0;j<f.length;j++)s+=(f[j]-m.mean[j])/Math.max(m.std[j],1e-8)*m.W[j][k];z.push(s/Math.max(m.temperature,1e-3))}const mx=Math.max(...z),e=z.map(v=>Math.exp(v-mx)),sum=e.reduce((a,b)=>a+b,0),p=e.map(v=>v/sum),o=p.map((v,i)=>[v,i]).sort((a,b)=>b[0]-a[0]);return{label:m.labels[o[0][1]],confidence:o[0][0],margin:o[0][0]-o[1][0]}}
function colour(){const c=makeFrameCanvas(),b=state.objectBox||{x:0,y:0,w:c.width,h:c.height},t=document.createElement("canvas");t.width=96;t.height=96;t.getContext("2d").drawImage(c,b.x,b.y,b.w,b.h,0,0,96,96);const src=cv.imread(t),hsv=new cv.Mat();try{cv.cvtColor(src,hsv,cv.COLOR_RGBA2HSV);const vals=[];for(let i=0;i<hsv.data.length;i+=4)vals.push([hsv.data[i],hsv.data[i+1],hsv.data[i+2]]);vals.sort((a,b)=>a[0]-b[0]);const m=vals[Math.floor(vals.length/2)],h=m[0],s=m[1],v=m[2];if(v<55)return"black";if(s<35&&v>190)return"white";if(s<55)return"silver/grey";if(s>90&&h>=35&&h<85)return"green";if(s>90&&(h<12||h>=165))return"red";if(s>80&&h>=12&&h<35)return"orange/yellow";if(s>55&&h>=85&&h<135)return"blue";return"neutral"}finally{src.delete();hsv.delete()}}
function frameBackground(){const c=document.createElement("canvas");c.width=160;c.height=100;c.getContext("2d").drawImage($("camera"),0,0,160,100);state.background=c.getContext("2d").getImageData(0,0,160,100).data}
function motionMask(){if(!state.background)return null;const v=$("camera"),w=v.videoWidth||1280,h=v.videoHeight||720,c=document.createElement("canvas");c.width=160;c.height=100;c.getContext("2d").drawImage(v,0,0,160,100);const d=c.getContext("2d").getImageData(0,0,160,100).data;let minX=160,minY=100,maxX=0,maxY=0,count=0;for(let i=0;i<d.length;i+=4){const q=Math.abs(d[i]-state.background[i])+Math.abs(d[i+1]-state.background[i+1])+Math.abs(d[i+2]-state.background[i+2]);if(q>72){const p=i/4,x=p%160,y=Math.floor(p/160);count++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}if(count<80)return null;return{x:minX/160*w,y:minY/100*h,w:(maxX-minX+1)/160*w,h:(maxY-minY+1)/100*h,area:count/16000,cx:(minX+maxX)/320,cy:(minY+maxY)/200}}
function grabCutBox(){const motion=motionMask();if(!cvReady())return motion;const c=document.createElement("canvas");c.width=160;c.height=100;c.getContext("2d").drawImage($("camera"),0,0,160,100);const src=cv.imread(c),mask=new cv.Mat(src.rows,src.cols,cv.CV_8UC1,new cv.Scalar(cv.GC_BGD)),bgd=new cv.Mat(),fgd=new cv.Mat();try{const x=Math.max(1,Math.floor(motion.x/($("camera").videoWidth||1280)*160)),y=Math.max(1,Math.floor(motion.y/($("camera").videoHeight||720)*100)),w=Math.max(2,Math.min(158,Math.floor(motion.w/($("camera").videoWidth||1280)*160))),h=Math.max(2,Math.min(98,Math.floor(motion.h/($("camera").videoHeight||720)*100)));for(let yy=y;yy<y+h;yy++)for(let xx=x;xx<x+w;xx++)mask.ucharPtr(yy,xx)[0]=cv.GC_PR_FGD;cv.grabCut(src,mask,new cv.Rect(x,y,w,h),bgd,fgd,3,cv.GC_INIT_WITH_MASK);let minX=160,minY=100,maxX=0,maxY=0,count=0;for(let yy=0;yy<100;yy++)for(let xx=0;xx<160;xx++){const z=mask.ucharPtr(yy,xx)[0];if(z===cv.GC_FGD||z===cv.GC_PR_FGD){count++;minX=Math.min(minX,xx);maxX=Math.max(maxX,xx);minY=Math.min(minY,yy);maxY=Math.max(maxY,yy)}}if(count<40)return motion;const vw=$("camera").videoWidth||1280,vh=$("camera").videoHeight||720;return{x:minX/160*vw,y:minY/100*vh,w:(maxX-minX+1)/160*vw,h:(maxY-minY+1)/100*vh,area:count/16000,cx:(minX+maxX)/320,cy:(minY+maxY)/200}}catch(e){return motion}finally{src.delete();mask.delete();bgd.delete();fgd.delete()}}
function sceneMask(){const motion=motionMask();return motion||grabCutBox()}
function guidance(mask){if(!mask)return{action:"place",text:"Place one object clearly inside the guide."};if(mask.area<.08)return{action:"closer",text:"Move the object a little closer."};if(mask.area>.65)return{action:"back",text:"Move a little farther away."};if(mask.cx<.35)return{action:"right",text:"Center the object, then turn it slightly right."};if(mask.cx>.65)return{action:"left",text:"Center the object, then turn it slightly left."};if(mask.cy<.30)return{action:"lower",text:"Lower the camera slightly."};if(mask.cy>.72)return{action:"raise",text:"Raise the camera slightly."};return{action:"capture",text:"Good view. Hold steady while I capture this view."}}
function excludePerson(dets,box){if(!box)return null;const people=dets.filter(x=>x.class==="person"&&x.score>.55);if(!people.length)return box;const overlap=people.some(p=>{const [x,y,w,h]=p.bbox,ix=Math.max(0,Math.min(box.x+box.w,x+w)-Math.max(box.x,x)),iy=Math.max(0,Math.min(box.y+box.h,y+h)-Math.max(box.y,y));return ix*iy>box.w*box.h*.25});return overlap?null:box}
function roiSignature(mask){const v=$("camera"),c=document.createElement("canvas");c.width=32;c.height=32;const x=c.getContext("2d");if(mask&&mask.w>8&&mask.h>8)x.drawImage(v,mask.x,mask.y,mask.w,mask.h,0,0,32,32);else x.drawImage(v,0,0,32,32);const d=x.getImageData(0,0,32,32).data;let out=0;for(let i=0;i<d.length-16;i+=16)out+=Math.abs(d[i]-d[i+4])+Math.abs(d[i+1]-d[i+5])+Math.abs(d[i+2]-d[i+6]);return out/(d.length/16*3*255)}
function progress(p){if(state.lastLabel===p.label)state.stable++;else{state.stable=1;state.lastLabel=p.label}state.evidence=Math.min(7,state.stable);$("evidenceBar").style.width=(state.evidence/7*100)+"%";$("evidenceText").textContent=state.evidence+" / 7 consistent observations"}
function viewEvidence(p,mask){const now=Date.now(),sig=roiSignature(mask),delta=state.lastSignature===null?0:Math.abs(sig-state.lastSignature);if(delta>.035){state.viewChanged=true;state.viewStableSince=0}else if(state.viewChanged&&!state.viewStableSince)state.viewStableSince=now;state.lastSignature=sig;const names=["view_1","view_2","view_3","view_4"],next=state.captures.length;if(next===0&&now-state.lastCapture>1400){state.captures.push({view:names[0],label:p.label,confidence:p.confidence});state.lastCapture=now}else if(next<4&&state.viewChanged&&state.viewStableSince&&now-state.viewStableSince>550&&now-state.lastCapture>1100){state.captures.push({view:names[next],label:p.label,confidence:p.confidence,motion_confirmed:true});state.lastCapture=now;state.viewChanged=false;state.viewStableSince=0}$("conditionText").textContent=state.captures.length+" / 4 stabilized views";if(state.captures.length===4)$("guidance").textContent="Four distinct stabilized views captured. Evidence fused."}
function captureView(p,mask){viewEvidence(p,mask)}
function loadNpy(bytes){const u=bytes instanceof Uint8Array?bytes:new Uint8Array(bytes);if(String.fromCharCode(...u.slice(0,6))!=="\x93NUMPY")throw Error("Invalid NPY");const major=u[6],hl=major===1?u[8]|u[9]<<8:u[8]|u[9]<<8|u[10]<<16|u[11]<<24,hs=major===1?10:12,header=new TextDecoder().decode(u.slice(hs,hs+hl)),descr=(header.match(/'descr':\s*'([^']+)'/)||[])[1],shapeRaw=(header.match(/'shape':\s*\(([^)]*)\)/)||[])[1]||"",shape=shapeRaw.split(",").map(s=>parseInt(s.trim(),10)).filter(Number.isFinite),data=u.slice(hs+hl),count=shape.length?shape.reduce((a,b)=>a*b,1):1;if(descr.endsWith("f4"))return{data:new Float32Array(data.buffer,data.byteOffset,count).slice(),shape};if(descr.endsWith("i4"))return{data:new Int32Array(data.buffer,data.byteOffset,count).slice(),shape};if(descr[1]==="U"){const width=parseInt(descr.slice(2),10),out=[];for(let i=0;i<count;i++){let s="";for(let j=0;j<width;j++){const cp=data[(i*width+j)*4]|data[(i*width+j)*4+1]<<8|data[(i*width+j)*4+2]<<16|data[(i*width+j)*4+3]<<24;if(cp)s+=String.fromCodePoint(cp)}out.push(s)}return{data:out,shape}}throw Error("Unsupported NPY dtype "+descr)}
async function loadNpz(b64){if(!window.fflate?.unzipSync)throw Error("fflate is unavailable");const bin=atob(b64.replace(/\s+/g,"")),bytes=Uint8Array.from(bin,c=>c.charCodeAt(0)),files=window.fflate.unzipSync(bytes),get=n=>{if(!files[n])throw Error("Model entry missing: "+n);return loadNpy(files[n]).data},W=get("W.npy"),b=get("b.npy"),mean=get("mean.npy"),std=get("std.npy"),labels=get("labels.npy"),temperature=get("temperature.npy")[0],unknown_threshold=get("unknown_threshold.npy")[0],model_version=get("model_version.npy")[0],shape=W.length/labels.length,nested=[];for(let i=0;i<shape;i++)nested.push(Array.from(W.slice(i*labels.length,(i+1)*labels.length)));return{W:nested,b:Array.from(b),mean:Array.from(mean),std:Array.from(std),labels:Array.from(labels),temperature,unknown_threshold,model_version,feature_length:mean.length}}
async function loadModel(){state.webConfig=await fetch("model_config.json",{cache:"no-store"}).then(r=>r.json());state.model=await fetch("model.b64",{cache:"no-store"}).then(r=>r.text()).then(loadNpz);if(state.model.feature_length!==state.webConfig.feature_length||state.model.labels.join("|")!==state.webConfig.labels.join("|"))throw Error("model/config contract mismatch");state.modelReady=true;$("eval").textContent="Browser inference: trained model active"}
async function process(){if(!state.running)return;try{analyseFrame();let det=[];if(state.detectorReady)try{det=await state.detector.detect($("camera"))}catch(e){}const mask=excludePerson(det,sceneMask());state.objectBox=mask;$("scene").textContent=state.detectorReady?"SCENE — foreground + person filter":"SCENE — foreground segmentation";if(det.some(x=>x.class==="person"&&x.score>.6)&&!mask){$("systemStatus").textContent="PERSON / OBJECT OCCLUDED";$("guidance").textContent="Move your hand or body away from the object."}else if(state.modelReady){const p=predict(feature()),threshold=Math.max(state.webConfig.confidence_threshold,state.model.unknown_threshold);if(p.confidence>=threshold&&p.margin>=state.webConfig.margin_threshold){progress(p);$("object").textContent=p.label.replaceAll("_"," ");$("confidence").textContent=Math.round(p.confidence*100)+"%";$("colour").textContent=colour();$("guidance").textContent=guidance(mask).text;captureView(p,mask);$("systemStatus").textContent=state.captures.length===4&&state.evidence>=7?"VERIFIED":"COLLECTING";}else{state.stable=0;state.evidence=0;state.lastLabel=null;$("systemStatus").textContent="UNCERTAIN";$("evidenceBar").style.width="0";$("evidenceText").textContent="0 / 7 consistent observations";$("guidance").textContent=guidance(mask).text}}else $("systemStatus").textContent="MODEL UNAVAILABLE"}catch(e){$("systemStatus").textContent="INFERENCE ERROR";$("eval").textContent=e.message}requestAnimationFrame(process)}
async function start(){if(state.running)return;try{await waitForCv();state.stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"},width:{ideal:1280},height:{ideal:720},frameRate:{ideal:30}},audio:false});$("camera").srcObject=state.stream;state.running=true;$("systemStatus").textContent="PERCEIVING";say("scan");await loadModel();await new Promise(r=>setTimeout(r,500));frameBackground();try{state.detector=await cocoSsd.load();state.detectorReady=true}catch(e){state.detectorReady=false}process()}catch(e){$("systemStatus").textContent="CAMERA/MODEL UNAVAILABLE";$("eval").textContent=e.message;say("unknown")}}
function reset(){state.stable=0;state.lastLabel=null;state.evidence=0;state.captures=[];state.objectBox=null;state.background=null;state.viewChanged=false;state.viewStableSince=0;state.lastSignature=null;$("evidenceBar").style.width="0";$("evidenceText").textContent="0 / 7 consistent observations";$("conditionText").textContent="adaptive";["object","colour","confidence"].forEach(id=>$(id).textContent="—");$("systemStatus").textContent=state.running?"PERCEIVING":"READY";$("guidance").textContent="Start perception and place an object in view.";say("ready")}
$("start").onclick=start;$("capture").onclick=()=>state.running?say("scan"):say("ready");$("reset").onclick=reset;$("language").onchange=e=>{state.language=e.target.value;say("ready")};window.Module=window.Module||{};if(typeof cv!=="undefined"&&cv.Mat){state.cvReady=true;window.__AURA_CV_READY__=true}else{const previous=window.Module.onRuntimeInitialized;window.Module.onRuntimeInitialized=()=>{if(typeof previous==="function")previous();state.cvReady=true;window.__AURA_CV_READY__=true}}window.__AURA_STATE__=state;window.AURA_TEST={setConfig:c=>state.webConfig=c,featureFromCanvas,loadNpz,loadModel,sceneMask,grabCutBox,roiSignature};say("ready");

/* AURA Context Intelligence: deterministic, inspectable reasoning on the client. */
(function initAuraContext(){
  const byId=id=>document.getElementById(id);
  const on=(id,event,handler)=>{const node=byId(id);if(node&&typeof node.addEventListener==="function")node.addEventListener(event,handler);};
  const catalogue=[
    {sku:"usb-c-hub",name:"USB-C hub",price:"24.00",ports:"USB-C / HDMI / USB-A"},
    {sku:"hdmi-cable",name:"HDMI cable",price:"9.00",ports:"HDMI"},
    {sku:"monitor",name:"Monitor",price:"119.00",ports:"HDMI / DisplayPort"},
    {sku:"desk",name:"Desk",price:"89.00",ports:"Measure available floor space first"},
    {sku:"curtain",name:"Curtain",price:"25.00",ports:"Measure window width and drop first"}
  ];
  const demoPorts={
    laptop:["USB-C","HDMI"], monitor:["HDMI","DisplayPort"],
    "usb-c hub":["USB-C","HDMI","USB-A"], "hdmi cable":["HDMI"]
  };
  const norm=s=>String(s||"").trim().toLowerCase().replace(/[_-]+/g," ").replace(/\s+/g," ");
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  let paypalConfig=null, paypalPromise=null, checkoutTickets=new Map(), reasoningSequence=0;
  function objectList(){
    const entered=byId("contextObjects").value.split(",").map(norm).filter(Boolean);
    const verified=state.lastLabel&&state.lastLabel!=="unknown"&&state.evidence>=7&&state.captures.length>=4;
    const detected=verified?[norm(state.lastLabel)]:[];
    return [...new Set([...detected,...entered])].filter(x=>x!=="unknown").map((label,i)=>({id:"obj-"+(i+1),label,confidence:label===norm(state.lastLabel)&&verified?0.9:0.7,source:label===norm(state.lastLabel)?"aura perception":"user supplied"}));
  }
  async function analyse(){
    const sequence=++reasoningSequence;
    const objects=objectList(), question=byId("contextQuestion").value, q=norm(question);
    const graph={objects:objects.map(x=>({...x})),relations:[]}, notes=[], missing=[], suggestions=[];
    let intent="understand_scene";
    if(!objects.length){
      byId("contextResult").textContent="No object labels yet. Start perception or enter one or more objects (comma-separated), then analyze again.";
      byId("contextGraph").innerHTML=""; return;
    }
    const labels=objects.map(x=>x.label);
    if(/connect|plug|port|monitor|display/.test(q)){
      intent="compatibility";
      const laptop=objects.find(x=>x.label==="laptop"), monitor=objects.find(x=>x.label==="monitor");
      if(laptop&&monitor){
        const shared=demoPorts.laptop.filter(x=>demoPorts.monitor.includes(x));
        notes.push("The illustrative generic-device catalogue lists a shared port: "+shared.join(", ")+".");
        graph.relations.push({subject:laptop.id,predicate:"may_connect_to",object:monitor.id,confidence:.65,evidence:"Illustrative catalogue only; exact models not checked."});
        missing.push("Exact laptop and monitor model numbers and ports");
      }else{
        notes.push("The current object labels do not establish whether these devices connect.");
        missing.push("Add a laptop and monitor label; then check exact model specifications.");
      }
      if(labels.includes("usb c hub")||labels.includes("usb-c hub"))suggestions.push("A USB-C hub may help only if the laptop supports video output over USB-C.");
    }else if(/fit|room|width|measure|curtain|desk|space/.test(q)){
      intent="fit_and_space";
      notes.push("A camera image cannot reliably establish exact physical dimensions.");
      missing.push("Measure the opening or available floor space and compare with verified product dimensions.");
      if(labels.includes("curtain"))suggestions.push("Measure window width and drop; mounting style and desired fullness affect sizing.");
      if(labels.includes("desk"))suggestions.push("Measure width, depth, clearances, and the path into the room.");
    }else if(/buy|purchase|price|order|shop/.test(q)){
      intent="commerce";
      notes.push("Only consider purchase after confirming the item and requirements.");
      missing.push("Verify exact product, budget, and product specifications before checkout.");
      objects.forEach(o=>{const p=catalogue.find(x=>norm(x.name)===o.label);if(p)suggestions.push(p.name+": illustrative demo price $"+p.price+" USD, not a live offer.");});
    }else{
      notes.push("Observed object labels: "+labels.join(", ")+".");
      const low=objects.filter(x=>x.confidence<.65);
      if(low.length)notes.push("Verify uncertain labels: "+low.map(x=>x.label).join(", ")+".");
      missing.push("Tell AURA what relationship or decision you want to check.");
    }
    const mean=objects.reduce((a,x)=>a+x.confidence,0)/objects.length;
    const summary=[...notes,...suggestions,...(missing.length?["Still needed: "+missing.join("; ")+"."]:[])].join(" ");
    byId("contextResult").textContent="Intent: "+intent.replaceAll("_"," ")+" · Evidence confidence: "+Math.round(mean*100)+"%. "+summary;
    byId("contextGraph").innerHTML='<div class="graph-nodes">'+graph.objects.map(o=>'<span class="graph-node">'+esc(o.label)+' <small>'+Math.round(o.confidence*100)+'%</small></span>').join("")+'</div>'+
      (graph.relations.length?graph.relations.map(r=>'<div class="graph-edge">'+esc(objects.find(o=>o.id===r.subject).label)+' <strong>→ '+esc(r.predicate.replaceAll("_"," "))+' →</strong> '+esc(objects.find(o=>o.id===r.object).label)+'<small> '+Math.round(r.confidence*100)+'% · '+esc(r.evidence)+'</small></div>').join(""):'<p class="muted">No relationship is established yet. Add the relevant objects and details.</p>')+
      '<p class="muted">Hypotheses only — not physical measurements, safety certification, or a guarantee of compatibility. Demo catalogue data is illustrative.</p>';
    byId("contextResult").textContent="Analyzing context…";
    const constraints={};
    for(const [field,id] of [["available_width_cm","availableWidth"],["product_width_cm","productWidth"],["available_depth_cm","availableDepth"],["product_depth_cm","productDepth"],["budget_usd","budgetUsd"]]){
      const raw=byId(id)?.value;
      if(raw!==undefined&&raw!==""&&Number.isFinite(Number(raw))&&Number(raw)>=0)constraints[field]=Number(raw);
    }
    if(byId("deviceModel")?.value.trim())constraints.device_model=byId("deviceModel").value.trim().slice(0,120);
    try{
      const response=await fetch("/.netlify/functions/context-reason",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({objects,question,language:state.language||"en-IN",constraints})
      });
      const result=await response.json();
      if(sequence!==reasoningSequence)return;
      if(!response.ok)throw new Error(result.error||"Context service unavailable");
      byId("contextResult").textContent=(result.answer||result.summary)+" "+(result.ai_used?"· AI-assisted answer":"· rule-based answer")+(result.privacy?.text_sent_to_optional_ai?" · text sent to configured AI provider":"");
      const serverGraph=result.graph||graph, serverObjects=serverGraph.objects||[], serverRelations=serverGraph.relations||[];
      byId("contextGraph").innerHTML='<div class="graph-nodes">'+serverObjects.map(o=>'<span class="graph-node">'+esc(o.label)+' <small>'+Math.round(Number(o.confidence||0)*100)+'%</small></span>').join("")+'</div>'+
        (serverRelations.length?serverRelations.map(r=>'<div class="graph-edge">'+esc(serverObjects.find(o=>o.id===r.subject)?.label||r.subject)+' <strong>→ '+esc(String(r.predicate||"related").replaceAll("_"," "))+' →</strong> '+esc(serverObjects.find(o=>o.id===r.object)?.label||r.object)+'<small> '+Math.round(Number(r.confidence||0)*100)+'% · '+esc(r.evidence||"Needs verification")+' · '+esc(r.status||"inferred")+'</small></div>').join(""):'<p class="muted">No relationship can be established from the current evidence.</p>')+
        (Array.isArray(result.recommendations)&&result.recommendations.length?'<div class="context-recommendations"><strong>Possible next steps</strong><ul>'+result.recommendations.map(x=>'<li>'+esc(x.item||"Suggestion")+': '+esc(x.reason||"Check details before acting")+(x.price_is_illustrative?' <small>· illustrative price only</small>':'')+'</li>').join("")+'</ul></div>':'')+
        (Array.isArray(result.missing_information)&&result.missing_information.length?'<p class="muted"><strong>Evidence still needed:</strong> '+result.missing_information.map(esc).join("; ")+'</p>':'')+
        '<p class="muted">'+(Array.isArray(result.limitations)?result.limitations.map(esc).join(" "):"Verify important details independently.")+'</p>';
      if(window.speechSynthesis&&byId("contextSpeak")?.checked) speak(result.answer||result.summary||summary);
    }catch(error){
      if(sequence!==reasoningSequence)return;
      byId("contextResult").textContent="Local result: "+summary+" Server reasoning is unavailable; check that the app is running with Netlify Functions.";
      if(window.speechSynthesis&&byId("contextSpeak")?.checked) speak(summary);
    }
  }
  on("analyzeContext","click",analyse);
  on("useDetection","click",()=>{
    if(state.lastLabel&&state.lastLabel!=="unknown"&&state.evidence>=7&&state.captures.length>=4){
      const current=byId("contextObjects").value.trim();
      byId("contextObjects").value=[current,state.lastLabel.replaceAll("_"," ")].filter(Boolean).join(", ");
      byId("contextQuestion").focus();
    }else byId("contextResult").textContent="AURA has not produced an object label yet. Start perception or enter the label manually.";
  });
  on("voiceQuestion","click",()=>{
    const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!Recognition){byId("contextResult").textContent="Speech recognition is not available in this browser. You can type your question instead.";return;}
    const rec=new Recognition();rec.lang=state.language||"en-IN";rec.interimResults=false;rec.maxAlternatives=1;
    byId("contextResult").textContent="Listening… Your browser may process voice through its speech provider.";
    rec.onresult=e=>{const text=e.results?.[0]?.[0]?.transcript||"";byId("contextQuestion").value=text;analyse();};
    rec.onerror=()=>{byId("contextResult").textContent="Voice input failed or was blocked. Type your question instead.";};
    try{rec.start();}catch(e){byId("contextResult").textContent="Voice input could not start. Type your question instead.";}
  });
  function renderCatalog(){
    const host=byId("commerceCatalog");
    host.innerHTML=catalogue.map(p=>'<article class="commerce-card"><div><strong>'+esc(p.name)+'</strong><p>$'+esc(p.price)+' USD <small>· demo price</small></p><small>'+esc(p.ports)+'</small></div><button type="button" data-checkout="'+esc(p.sku)+'">Set up PayPal</button><div class="paypal-target" id="paypal-'+esc(p.sku)+'"></div></article>').join("");
    if(typeof host.querySelectorAll==="function")host.querySelectorAll("[data-checkout]").forEach(btn=>btn.addEventListener("click",()=>setupButtons(btn.dataset.checkout)));
  }
  async function loadPayPal(){
    if(paypalPromise)return paypalPromise;
    paypalPromise=(async()=>{
      const response=await fetch("/.netlify/functions/paypal-config",{cache:"no-store"});
      if(!response.ok)throw new Error("PayPal configuration endpoint unavailable");
      paypalConfig=await response.json();
      if(!paypalConfig.enabled||!paypalConfig.clientId)throw new Error("PayPal Sandbox is not configured by the site owner");
      if(!window.paypal){
        const url=new URL("https://www.paypal.com/sdk/js");
        url.searchParams.set("client-id",paypalConfig.clientId);url.searchParams.set("currency","USD");url.searchParams.set("intent","capture");
        const script=document.createElement("script");script.src=url.toString();script.async=true;
        document.head.appendChild(script);
        await new Promise((resolve,reject)=>{script.onload=resolve;script.onerror=()=>reject(new Error("PayPal SDK failed to load"));});
      }
      if(!window.paypal?.Buttons)throw new Error("PayPal SDK did not initialize");
      return window.paypal;
    })();
    return paypalPromise;
  }
  async function setupButtons(sku){
    const target=byId("paypal-"+sku);if(!target)return;
    target.textContent="Preparing secure checkout…";
    try{
      const sdk=await loadPayPal();target.textContent="";
      await sdk.Buttons({
        style:{layout:"vertical",shape:"rect",label:"paypal"},
        createOrder:async()=>{
          const response=await fetch("/.netlify/functions/paypal-create-order",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sku})});
          const data=await response.json();if(!response.ok)throw new Error(data.error||"Could not create order");
          checkoutTickets.set(data.id,data.ticket);return data.id;
        },
        onApprove:async data=>{
          target.textContent="Verifying and capturing payment…";
          const ticket=checkoutTickets.get(data.orderID);
          if(!ticket)throw new Error("This checkout session is missing its verification ticket. Start again.");
          const response=await fetch("/.netlify/functions/paypal-capture-order",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({orderId:data.orderID,ticket})});
          const result=await response.json();
          if(!response.ok)throw new Error(result.error||"Payment was not completed");
          target.textContent="Payment completed in PayPal "+(paypalConfig.mode==="live"?"Live":"Sandbox")+". Order "+result.orderId;
          byId("commerceStatus").textContent="PayPal returned a completed capture. Demo products are not fulfilled automatically.";
          checkoutTickets.delete(data.orderID);
        },
        onCancel:()=>{target.textContent="Checkout cancelled. No capture was requested.";},
        onError:err=>{target.textContent="Checkout error: "+(err?.message||"PayPal error");}
      }).render(target);
    }catch(e){target.textContent=e instanceof Error?e.message:"Checkout unavailable";byId("commerceStatus").textContent="PayPal unavailable. The site owner must configure the server environment before checkout can work.";}
  }
  renderCatalog();
  fetch("/.netlify/functions/paypal-config",{cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject()).then(c=>{
    paypalConfig=c;
    byId("commerceStatus").textContent=c.enabled?"PayPal "+(c.mode==="live"?"Live":"Sandbox")+" client ID found. Choose a demo product to load the PayPal button.":"PayPal is not configured yet. Set server-side credentials; no payment can be made until then.";
  }).catch(()=>{byId("commerceStatus").textContent="PayPal checkout requires Netlify Functions. When hosted locally, use Netlify CLI (netlify dev).";});
})();

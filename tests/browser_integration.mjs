import {createServer} from "node:http";
import {readFileSync} from "node:fs";
import {join,extname} from "node:path";
import {cwd} from "node:process";
import {chromium} from "playwright";
const root=cwd(),mime={".html":"text/html",".js":"text/javascript",".json":"application/json",".css":"text/css",".b64":"text/plain"};
const server=createServer((req,res)=>{try{const p=join(root,"web",decodeURIComponent(req.url==="/"?"index.html":req.url));if(!p.startsWith(join(root,"web")))throw Error("bad path");const body=readFileSync(p);res.writeHead(200,{"content-type":mime[extname(p)]||"application/octet-stream"});res.end(body)}catch(e){res.writeHead(404);res.end("not found")}});
server.listen(4173,"127.0.0.1");
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage();
 await page.goto("http://127.0.0.1:4173/",{waitUntil:"domcontentloaded"});
 await page.waitForFunction(()=>window.__AURA_CV_READY__===true,{timeout:30000});
 const r=await page.evaluate(async()=>{
   const c=document.createElement("canvas");c.width=80;c.height=64;
   const ctx=c.getContext("2d"),d=ctx.createImageData(80,64);
   for(let y=0;y<64;y++)for(let x=0;x<80;x++){const i=(y*80+x)*4;d.data[i]=(x*11+y*13)%256;d.data[i+1]=(x*5+y*7)%256;d.data[i+2]=(x*3+y*2)%256;d.data[i+3]=255}
   ctx.putImageData(d,0,0);
   window.AURA_TEST.setConfig({image_size:128,feature_length:329,roi:{mode:"center",width_ratio:.82,height_ratio:.82}});
   const f=window.AURA_TEST.featureFromCanvas(c);
   const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",new Uint8Array(f.buffer,f.byteOffset,f.byteLength)))).map(x=>x.toString(16).padStart(2,"0")).join("");
   return {length:f.length,finite:Array.from(f).every(Number.isFinite),hash};
 });
 if(r.length!==329||!r.finite||r.hash!=="4194e36e9bf2e4d92e798f69ae12e49b8a1fe82ec74fe4942e90c2d098662f5f")throw Error("Python/browser feature parity failed: "+JSON.stringify(r));
 const context=await page.evaluate(()=>{
   document.getElementById("contextObjects").value="laptop, monitor";
   document.getElementById("contextQuestion").value="Can I connect this monitor?";
   document.getElementById("analyzeContext").click();
   return {result:document.getElementById("contextResult").textContent,graph:document.getElementById("contextGraph").textContent};
 });
 if(!context.result.includes("compatibility")||!context.graph.includes("laptop")||!context.graph.includes("monitor"))
   throw Error("AURA context reasoning UI failed: "+JSON.stringify(context));
 console.log("browser OpenCV + 329-value Python golden vector + context reasoning OK");
}finally{await browser.close();server.close()}

const { chromium } = require('playwright'); const fs=require('fs'); const path=require('path');
(async()=>{
 const dir=process.argv[2], pngDir=path.join(dir,'png'); fs.mkdirSync(pngDir,{recursive:true});
 const b=await chromium.launch(); const files=fs.readdirSync(dir).filter(f=>f.endsWith('.svg')).sort();
 for(const f of files){
  const s=fs.readFileSync(path.join(dir,f),'utf8'); const m=s.match(/viewBox="0 0 (\d+) (\d+)"/);
  const w=+m[1],h=+m[2]; const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:4});
  await p.setContent(`<html><body style="margin:0;background:transparent">${s.replace(/<\?xml[^>]*>/,'')}</body></html>`);
  await p.screenshot({path:path.join(pngDir,f.replace('.svg','.png')),omitBackground:true,clip:{x:0,y:0,width:w,height:h}}); await p.close();
 }
 const cells=files.map(f=>`<div style="background:#F6E7A6;border-radius:12px;padding:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;${f.includes('border')?'grid-column:span 3':''}"><img src="file://${path.resolve(dir,f)}" style="max-width:100%;max-height:${f.includes('border')?180:260}px"><div style="font:13px sans-serif;color:#7a4a00;margin-top:8px">${f}</div></div>`).join('');
 const p=await b.newPage({viewport:{width:1300,height:800},deviceScaleFactor:1});
 await p.goto('file://'+path.resolve(dir,'..')); await p.setContent(`<body style="margin:0;padding:20px;background:#fff"><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">${cells}</div></body>`);
 await p.waitForTimeout(300); await p.screenshot({path:path.join(dir,'_contact-sheet.png'),fullPage:true}); await b.close();
})();

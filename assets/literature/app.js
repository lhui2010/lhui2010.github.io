(async () => {
"use strict";
const base = document.currentScript ? document.currentScript.src : location.href;
const data = await fetch(new URL("index.json", base)).then(r => {if(!r.ok) throw Error(r.status); return r.json();});
const el = id => document.getElementById(id);
const add = (parent,tag,text) => {const e=document.createElement(tag);e.textContent=text;parent.appendChild(e);return e;};
for(const m of data.months) {const o=add(el("month"),"option",m);o.value=m;}
{const o=add(el("month"),"option","日期待确认");o.value="unknown";}
for(const j of [...new Set(data.journals)].sort()) {const o=add(el("journal"),"option",j);o.value=j;}
if(data.coverage.month && data.months.includes(data.coverage.month))el("month").value=data.coverage.month;
for(const source of data.coverage.sources||[]) {
 const row=add(el("source-status"),"p",(source.journal||"")+" · "+source.status+" · "+(source.count??"?")+" 条 · "+source.source);
 if(source.error)add(row,"small"," — "+source.error);
}
let sequence=0;
const monthCache=new Map();
async function draw() {
 const seq=++sequence;
 const requested=el("month").value;
 if(!monthCache.has(requested))monthCache.set(requested,
   fetch(new URL("months/"+requested+".json",base)).then(r=>{if(!r.ok)throw Error(r.status);return r.json();}));
 const papers=await monthCache.get(requested);
 if(seq!==sequence)return;
 const query=el("search").value.toLowerCase(), month=el("month").value;
 const rows=papers.filter(p=>(month==="unknown"?!p.months.length:p.months.includes(month)) &&
 (!el("journal").value||p.journal===el("journal").value) &&
 (!el("selected").checked||p.selected) &&
 [p.title,p.abstract,p.authors.join(" "),p.doi].join(" ").toLowerCase().includes(query));
 el("papers").replaceChildren();el("count").textContent=rows.length+" 篇";
 el("coverage").textContent="本地更新："+data.generated_at+"；官方RSS："+data.official_rss.ok+"/"+data.official_rss.endpoints+" 成功；本轮检查期刊："+(data.coverage.journals||[]).join(", ")+"；补充元数据异常："+data.secondary_failures+" 个来源。补充源不代表完整覆盖。";
 for(const p of rows) {
 const box=add(el("papers"),"article","");box.style.marginBottom="1.5em";
 const a=add(box,"a",p.title);if(/^https?:\/\//i.test(p.url)) {a.href=p.url;a.rel="noopener noreferrer";}
 const authors=p.authors.length<=5?p.authors:[...p.authors.slice(0,3),"...",...p.authors.slice(-2)];
 add(box,"p",p.journal+" · "+(p.publication_date||"日期未知")+" · 卷期日期："+(p.issue_date||"未知")+" · "+authors.join(", "));
 if(p.reasons.length) add(box,"p","筛选依据："+p.reasons.join("；"));
 if(p.abstract) {const d=add(box,"details","");add(d,"summary","摘要 / RSS 内容");add(d,"p",p.abstract);}
 if(p.metadata_warnings.length)add(box,"p","元数据待补："+p.metadata_warnings.join("；"));
 add(box,"small","DOI："+(p.doi||"未知")+"；日期依据："+p.date_kind+"；来源："+p.sources.length);
 }
}
for(const id of ["month","journal","selected","search"])el(id).addEventListener("input",()=>draw().catch(e=>{el("coverage").textContent="加载失败："+e.message;}));
await draw();
})().catch(e => {document.getElementById("coverage").textContent="文献索引加载失败："+e.message;});

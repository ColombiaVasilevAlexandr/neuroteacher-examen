// Test the actual locale runtime and dashboard selector without a browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.join(__dirname,'../frontend/public');
const storage=new Map(),calls=[];
const localStorage={getItem:key=>storage.get(key)??null,setItem:(key,value)=>storage.set(key,String(value))};
const document={documentElement:{lang:''}};
const events=[];class CustomEvent{constructor(type,options){this.type=type;this.detail=options.detail;}};
const window={dispatchEvent:event=>events.push(event),location:{href:'http://192.168.1.20:5173/'},COLOMBIA_API_BASE:'http://192.168.1.20:8000/api',
  fetch:async(input,init)=>{calls.push({input,init});return {ok:true};}};
const ctx=vm.createContext({window,document,localStorage,CustomEvent,Request,URL,Math,Date,Intl,Error,encodeURIComponent});
vm.runInContext(fs.readFileSync(path.join(root,'locales.js'),'utf8'),ctx);
vm.runInContext(fs.readFileSync(path.join(root,'aux-locales.js'),'utf8'),ctx);
const locales=window.ColombiaLocales;
assert.deepEqual(Array.from(locales.ids),['es','ru','en','de','fr','zh-Hans']);
const jsx=(type,props)=>({type,props});
ctx.f=locales.wrap({jsx,jsxs:jsx,Fragment:'fragment'});
let hook=0,states=[];
ctx.l={useState(initial){const index=hook++;if(!(index in states))states[index]=typeof initial==='function'?initial():initial;
  return [states[index],value=>{states[index]=typeof value==='function'?value(states[index]):value;}];},useEffect(){},useMemo:fn=>fn()};
ctx.g={};ctx.p=[['home','Hoy'],['book','Aprender'],['target','Entrenamiento'],['exam','Examen'],['chart','Progreso'],['alert','Errores'],['repeat','Repaso'],['ai','Conversación'],['settings','Ajustes']];
ctx.h=()=>null;ctx.re=()=>null;ctx.ee=()=>null;ctx.w=()=>null;ctx.C=()=>null;ctx._=()=>null;
const bundle=fs.readFileSync(path.join(root,'legacy-app.bundle.js'),'utf8');
const start=bundle.indexOf('function ne(){'),end=bundle.indexOf('function re({language:',start);
assert(start>0&&end>start);vm.runInContext(bundle.slice(start,end),ctx);
function nodes(tree){if(!tree||typeof tree!=='object')return [];
 return [tree,...(Array.isArray(tree.props?.children)?tree.props.children:[tree.props?.children]).flatMap(nodes)];}
function text(tree){return Array.isArray(tree)?tree.map(text).join(''):tree&&typeof tree==='object'?text(tree.props?.children):tree==null?'':String(tree);}
const expected=['Hoy','Сегодня','Today','Heute',"Aujourd’hui",'今天'];
for(let index=0;index<locales.ids.length;index++){
 const locale=locales.ids[index];locales.set(locale);const eventCount=events.length;locales.set(locale);assert.equal(events.length,eventCount);states=[];hook=0;
 for(const key of locales.messageKeys){const value=locales.ui(key,{count:12,index:1,total:30,score:5,mode:'TEST',topics:'TEST',topic:'TEST',time:'1:23'});assert(value.length>0);assert(!/\{\w+\}/.test(value));}
 assert.equal(locales.dateLocale,['es-CO','ru-RU','en-GB','de-DE','fr-FR','zh-CN'][index]);
 const tree=ctx.ne();const select=nodes(tree).find(n=>n.type==='select'&&n.props.className==='language');
 assert(select);assert.equal(select.props.value,locale);assert.equal(select.props.children.length,6);
 const first=nodes(tree).find(n=>n.type==='button'&&n.props['data-nav']==='Hoy');
 assert.equal(text(first),expected[index]);assert.equal(document.documentElement.lang,locale);
 select.props.onChange({target:{value:'fr'}});assert.equal(locales.current,'fr');
 assert.equal(localStorage.getItem('neuroteacher-language'),'fr');
 const protectedText=ctx.f.jsx('span',{'data-content':true,children:'Cultura'});
 assert.equal(protectedText.props.children,'Cultura');
 assert.notEqual(locales.fallback(),'');
}
(async()=>{
 locales.set('zh-Hans');await window.fetch('http://127.0.0.1:8000/api/questions?limit=2');
 let url=new URL(calls.at(-1).input);assert.equal(url.hostname,'192.168.1.20');assert.equal(url.searchParams.get('locale'),'zh-Hans');
 await window.fetch('http://127.0.0.1:8000/api/questions?locale=de');
 assert.equal(new URL(calls.at(-1).input).searchParams.get('locale'),'de');
 const request=new Request('http://127.0.0.1:8000/api/exams/start',{method:'POST',headers:{'Content-Type':'application/json'},body:'{"exam_format":"D"}'});
 await window.fetch(request);const forwarded=calls.at(-1).input;
 assert.equal(forwarded.method,'POST');assert.equal(new URL(forwarded.url).searchParams.get('locale'),'zh-Hans');
 assert.equal(await forwarded.text(),'{"exam_format":"D"}');
 assert.equal(locales.escape('<script>&"'), '&lt;script&gt;&amp;&quot;');
 console.log('PASS: six selector locales, navigation labels, content protection, fallback and LAN/request forwarding');
})().catch(error=>{console.error(error);process.exitCode=1;});

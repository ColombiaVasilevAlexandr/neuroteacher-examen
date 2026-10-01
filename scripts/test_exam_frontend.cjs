// Exercise the checked-in exam component with a deterministic hook/HTTP harness.
// This checks handlers and payloads, not browser rendering.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../frontend/public/legacy-app.bundle.js'), 'utf8');
const begin = source.indexOf('function ee({language:e,onExit:t})');
const end = source.indexOf('Object.assign(g,', begin);
assert(begin > 0 && end > begin);
const config = {id:'D',questions:65,passing_score:32,minutes:180};
const questions = [1,2,3].map(id => ({id,question_es:'Question '+id,question_ru:'Вопрос '+id,
  answer_a:'A',answer_b:'B',answer_c:'C',answer_d:'D'}));
let states = [[config],646,0,null,[],0,{},0,null,null,'',false];
let hook = 0, failCompletion = true;
const calls = [];
const jsx = (type,props) => ({type,props});
const context = vm.createContext({Math,Date,Error,encodeURIComponent,te:[],E:{},
  l:{useState(initial){const index=hook++; if(!(index in states)) states[index]=initial;
      return [states[index], value => {states[index]=typeof value==='function'?value(states[index]):value;}];},
     useEffect(){}}, f:{jsx,jsxs:jsx,Fragment:'fragment'},
  fetch: async (url,options) => {
    const body=JSON.parse(options.body); calls.push({url,body});
    if(url.endsWith('/exams/start')) return {ok:true,json:async()=>({session_id:'test-token',questions,minutes:180})};
    assert(url.endsWith('/exams/complete'));
    assert.deepEqual(Object.keys(body).sort(),['answers','session_id']);
    if(failCompletion){failCompletion=false;return {ok:false};}
    return {ok:true,json:async()=>({correct_answers:1,total_questions:3,passing_score:2,passed:false})};
  }});
vm.runInContext(source.slice(begin,end),context);
const render = () => {hook=0;return context.ee({language:'ru',onExit(){}});};
function nodes(tree){if(!tree||typeof tree!=='object')return [];
  return [tree,...(Array.isArray(tree.props?.children)?tree.props.children:[tree.props?.children]).flatMap(nodes)];}
function text(tree){if(Array.isArray(tree))return tree.map(text).join('');
  return tree&&typeof tree==='object'?text(tree.props?.children):(tree==null?'':String(tree));}
function button(tree,predicate){const result=nodes(tree).find(n=>n.type==='button'&&predicate(n));
  assert(result,'Expected button');return result;}
(async()=>{
  await button(render(),n=>text(n).includes('Начать полный')).props.onClick();
  assert.equal(states[9].session_id,'test-token');
  assert.deepEqual(calls[0].body,{exam_format:'D'});
  let tree=render();
  button(tree,n=>n.props.className==='').props.onClick(); // First question, option A.
  button(render(),n=>text(n)==='Далее →').props.onClick();
  button(render(),n=>text(n)==='Далее →').props.onClick(); // Skip the second question.
  await button(render(),n=>text(n)==='Завершить').props.onClick();
  assert.equal(states[8],null); // Failed HTTP completion must not show a result.
  assert(text(render()).includes('Результат не сохранён'));
  await button(render(),n=>text(n)==='Завершить').props.onClick();
  assert.deepEqual(calls[1].body,calls[2].body);
  assert.deepEqual(calls[2].body.answers,[{question_id:1,answer:'A'}]);
  assert.equal(states[8],1); // Show the score returned by the server.
  assert(text(render()).includes('1 / 3'));
  console.log('PASS: exam start, selected-answer payload, failure, retry and server result');
})().catch(error=>{console.error(error);process.exitCode=1;});

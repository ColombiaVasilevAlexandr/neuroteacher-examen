(() => {
  const translations = new Map()
  const normalize = text => text.replace(/^ES:\s*/,'').replace(/\s+/g,' ').trim()
  const apply = () => {
    const card = document.querySelector('main.training .question-card')
    const title = card?.querySelector('h1')
    if (!title || title.dataset.russianQuestion) return
    const spanish = normalize(title.textContent)
    const russian = translations.get(spanish)
    if (!russian) return
    title.dataset.russianQuestion='true'; title.textContent=russian
    if (!card.querySelector('.question-es-original')) {
      const original=document.createElement('p'); original.className='question-es-original'; original.lang='es'; original.textContent=`ES: ${spanish}`
      title.insertAdjacentElement('afterend',original)
    }
  }
  fetch('http://127.0.0.1:8000/api/questions?limit=1000').then(r=>r.ok?r.json():Promise.reject()).then(items=>{
    items.forEach(item=>{if(item.question_es && item.question_ru)translations.set(normalize(item.question_es),item.question_ru)})
    apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
  }).catch(()=>undefined)
})()

(() => {
  const API = 'http://127.0.0.1:8000/api'
  const prompts = [
    {label:'Объясни ошибку', build:async()=>{const errors=await fetch(`${API}/errors`).then(r=>r.json()); const error=errors[0]; return error ? `Я ошибся в вопросе: «${error.question_es}». Объясни правильный ответ простым испанским, затем кратко по-русски и дай один похожий вопрос.` : 'У меня пока нет сохранённых ошибок. Задай мне один вопрос по теме, которую стоит повторить.'}},
    {label:'Диалог на испанском', build:async()=> 'Начни короткий диалог на испанском уровня A2 о гражданстве Колумбии. Говори естественно, исправляй мои ошибки мягко и задавай только один вопрос за раз.'},
    {label:'Вопрос по пособию', build:async()=>{const chapters=await fetch(`${API}/materials/chapters`).then(r=>r.json()); const chapter=chapters[Math.floor(Math.random()*chapters.length)]; return `Задай один вопрос по разделу «${chapter?.title || 'Colombia, nuestra casa'}» (страница ${chapter?.page_number || ''}) официального пособия. После моего ответа коротко объясни его.`}}
  ]
  const setValue = (input, value) => {
    const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set
    setter.call(input,value); input.dispatchEvent(new Event('input',{bubbles:true})); input.dispatchEvent(new Event('change',{bubbles:true}))
  }
  const apply = () => {
    const input = document.querySelector('.ai-input textarea')
    if (!input || document.querySelector('.consultant-shortcuts')) return
    const shortcuts = document.createElement('div'); shortcuts.className='consultant-shortcuts'
    shortcuts.innerHTML = prompts.map(item => `<button type="button">${item.label}</button>`).join('')
    shortcuts.querySelectorAll('button').forEach((button,index) => button.onclick = async () => {
      const original=button.textContent; button.disabled=true; button.textContent='Подготавливаю…'
      try {
        const prompt=await prompts[index].build(); setValue(input,prompt)
        const send=input.parentElement.querySelector('button')
        setTimeout(()=>send?.click(),80)
      } catch { setValue(input,'Давай продолжим практику по экзамену на гражданство Колумбии.') }
      finally { setTimeout(()=>{button.disabled=false;button.textContent=original},500) }
    })
    input.parentElement.insertAdjacentElement('beforebegin', shortcuts)
  }
  apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
})()

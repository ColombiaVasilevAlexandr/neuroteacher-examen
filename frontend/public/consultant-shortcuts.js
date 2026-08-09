(() => {
  const prompts = [
    ['Объясни ошибку', 'Объясни мне последнюю ошибку коротко и дай один похожий вопрос.'],
    ['Диалог на испанском', 'Давай короткий диалог на испанском уровня A2 о гражданстве Колумбии. Один вопрос за раз.'],
    ['Вопрос по пособию', 'Задай мне один вопрос по официальному пособию Colombia, nuestra casa.']
  ]
  const apply = () => {
    const input = document.querySelector('.ai-input textarea')
    if (!input || document.querySelector('.consultant-shortcuts')) return
    const shortcuts = document.createElement('div'); shortcuts.className='consultant-shortcuts'
    shortcuts.innerHTML = prompts.map(([label]) => `<button type="button">${label}</button>`).join('')
    shortcuts.querySelectorAll('button').forEach((button,index) => button.onclick=()=>{input.value=prompts[index][1];input.dispatchEvent(new Event('input',{bubbles:true}));input.focus()})
    input.parentElement.insertAdjacentElement('beforebegin', shortcuts)
  }
  apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
})()

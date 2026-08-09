(() => {
  const add = count => {
    const card = document.querySelector('.today')
    if (!card) return
    const existing = card.querySelector('.review-reminder')
    if (!count) { existing?.remove(); return }
    if (existing) { existing.querySelector('span').textContent=`${count} ${count === 1 ? 'вопрос' : 'вопросов'} по расписанию`; return }
    const reminder = document.createElement('div'); reminder.className='review-reminder'
    reminder.innerHTML=`<div><b>Повторение ждёт</b><span>${count} ${count === 1 ? 'вопрос' : 'вопросов'} по расписанию</span></div><button>Повторить</button>`
    reminder.querySelector('button').onclick=()=>[...document.querySelectorAll('.nav')].find(button=>/Повторение|Repaso/.test(button.textContent))?.click()
    card.querySelector('.start')?.insertAdjacentElement('beforebegin',reminder)
  }
  let latest = 0
  const refresh = () => fetch('http://127.0.0.1:8000/api/dashboard').then(r=>r.ok?r.json():Promise.reject()).then(data=>{ latest=data.due_reviews || 0; add(latest) }).catch(()=>undefined)
  refresh(); new MutationObserver(()=>add(latest)).observe(document.documentElement,{childList:true,subtree:true}); window.addEventListener('reviews:updated',refresh); window.addEventListener('focus',refresh)
})()

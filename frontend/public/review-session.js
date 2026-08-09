(() => {
  const API = 'http://127.0.0.1:8000/api'
  const apply = () => {
    const page = [...document.querySelectorAll('main.training')].find(node => node.textContent.includes('Интервальное повторение'))
    if (!page || page.querySelector('.review-session')) return
    const session = document.createElement('section'); session.className = 'review-session'
    page.querySelector('.repeat-empty-state')?.remove(); page.append(session)
    const render = questions => {
      let index = 0
      const show = () => {
        const q = questions[index]
        if (!q) { session.innerHTML='<div class="review-done"><b>✓</b><h2>Повторение завершено</h2><p>Следующая очередь появится в назначенный день.</p></div>'; return }
        const answers = ['A','B','C','D'].map(key => `<button data-answer="${key}"><b>${key}</b>${q[`answer_${key.toLowerCase()}_ru`] || q[`answer_${key.toLowerCase()}`]}</button>`).join('')
        session.innerHTML = `<small>ПОВТОРЕНИЕ ${index + 1} ИЗ ${questions.length}</small><h1>${q.question_ru || q.question_es}</h1><p class="review-original">ES: ${q.question_es}</p><div class="review-answers">${answers}</div><p class="review-result"></p>`
        session.querySelectorAll('[data-answer]').forEach(button => button.onclick = async () => {
          const response = await fetch(`${API}/questions/${q.id}/answer`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answer:button.dataset.answer})})
          const result = await response.json(); const note = session.querySelector('.review-result')
          session.querySelectorAll('[data-answer]').forEach(item => item.disabled = true)
          note.textContent = result.correct ? `Верно. ${result.explanation_ru || result.explanation_es}` : `Неверно. ${result.explanation_ru || result.explanation_es}`
          note.className = `review-result ${result.correct ? 'right' : 'wrong'}`
          const next = document.createElement('button'); next.className='review-next'; next.textContent='Следующий вопрос →'; next.onclick=()=>{index += 1; show()}; session.append(next)
        })
      }; show()
    }
    session.innerHTML='<p class="review-loading">Загружаю очередь повторения…</p>'
    fetch(`${API}/review/due`).then(r=>r.ok?r.json():Promise.reject()).then(items => {
      if (!items.length) { session.innerHTML='<div class="review-done"><b>✓</b><h2>Сегодня повторений нет</h2><p>Ошибки и отмеченные вопросы появятся здесь автоматически в назначенный день.</p></div>'; return }
      render(items)
    }).catch(()=>session.innerHTML='<p class="review-result wrong">Не удалось загрузить очередь повторения.</p>')
  }
  apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
})()

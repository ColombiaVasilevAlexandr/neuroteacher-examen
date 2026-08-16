(() => {
  const topics = { 'География': 'Geografía', 'История': 'Historia', 'Конституция': 'Constitución', 'Испанский язык': 'Castellano', 'Культура': 'Cultura', 'Натурализация': 'Naturalización' }
  const render = () => document.querySelectorAll('.methodology-course__lesson').forEach(lesson => {
    if (lesson.querySelector('.audio-mini-test')) return
    const start = lesson.querySelector('.methodology-course__start')
    const topic = topics[start?.dataset.topic]
    if (!topic) return
    const button = document.createElement('button')
    button.className = 'audio-mini-test'; button.type = 'button'; button.textContent = 'Мини-тест: 5 вопросов'; button.disabled = false
    button.style.cssText = 'border:1px solid #38e0d0;background:#12344d;border-radius:8px;padding:9px 11px;color:#eef4ff;font-weight:700'
    button.addEventListener('click', async () => {
      button.disabled = true; button.textContent = 'Загрузка…'
      let questions
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/questions?limit=5&topic=${encodeURIComponent(topic)}`)
        if (!response.ok) throw new Error('Не удалось получить вопросы')
        questions = await response.json()
        if (!Array.isArray(questions) || !questions.length) throw new Error('Для этого раздела пока нет вопросов')
      } catch (error) {
        alert(error.message || 'Мини-тест не удалось открыть. Попробуйте ещё раз.')
        button.disabled = false; button.textContent = 'Мини-тест: 5 вопросов'
        return
      }
      button.disabled = false; button.textContent = 'Мини-тест: 5 вопросов'
      const overlay = document.createElement('div'); overlay.style.cssText = 'position:fixed;inset:0;z-index:99;overflow:auto;padding:28px;background:#06101df5;color:#eef4ff'
      let index = 0, correct = 0
      const draw = () => { const q = questions[index]; overlay.innerHTML = `<button id="close">×</button><h2>Мини-тест · ${index + 1} / ${questions.length}</h2><h3>${q.question_ru || q.question_es}</h3>${['A','B','C','D'].map(k => `<button data-a="${k}" style="display:block;width:100%;text-align:left;margin:8px 0;padding:12px">${k}. ${q['answer_' + k.toLowerCase() + '_ru'] || q['answer_' + k.toLowerCase()]}</button>`).join('')}`; overlay.querySelector('#close').onclick=()=>overlay.remove(); overlay.querySelectorAll('[data-a]').forEach(b=>b.onclick=async()=>{ const a=b.dataset.a; const r=await fetch(`http://127.0.0.1:8000/api/questions/${q.id}/answer`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answer:a})}).then(x=>x.json()); if(r.correct)correct++; const right=q['answer_'+r.correct_answer.toLowerCase()+'_ru']||q['answer_'+r.correct_answer.toLowerCase()]; overlay.innerHTML+=`<section style="margin-top:16px;padding:14px;border:1px solid #38e0d0"><b>${r.correct?'✓ Верно':'✕ Неверно'}</b><p>Правильный ответ: ${right}</p><p>${r.explanation_ru||r.explanation_es||''}</p><button id="next">${index+1<questions.length?'Следующий вопрос':'Показать результат'}</button></section>`; overlay.querySelectorAll('[data-a]').forEach(x=>x.disabled=true); overlay.querySelector('#next').onclick=()=>{index++; index<questions.length?draw():overlay.innerHTML=`<h2>Результат: ${correct} / ${questions.length}</h2><button onclick="this.parentElement.remove()">Закрыть</button>`} }) }
      document.body.append(overlay); draw()
    })
    lesson.append(button)
  })
  new MutationObserver(render).observe(document.documentElement,{childList:true,subtree:true}); render()
})()

(() => {
  const topics = { 'География': 'Geografía', 'История': 'Historia', 'Конституция': 'Constitución', 'Испанский язык': 'Castellano', 'Культура': 'Cultura', 'Натурализация': 'Naturalización' }
  const api = 'http://127.0.0.1:8000/api'
  const escapeHtml = value => String(value || '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char])
  const buttonStyle = 'display:block;width:100%;text-align:left;margin:8px 0;padding:12px;background:#12344d;color:#fff;border:1px solid #5d8198;border-radius:8px'

  const render = () => document.querySelectorAll('.methodology-course__lesson').forEach(lesson => {
    if (lesson.querySelector('.audio-mini-test')) return
    const topic = topics[lesson.querySelector('.methodology-course__start')?.dataset.topic]
    if (!topic) return
    const button = document.createElement('button')
    button.className = 'audio-mini-test'; button.type = 'button'; button.textContent = 'Мини-тест: 5 вопросов'
    button.style.cssText = 'border:1px solid #38e0d0;background:#12344d;border-radius:8px;padding:9px 11px;color:#eef4ff;font-weight:700'
    button.addEventListener('click', async () => {
      button.disabled = true; button.textContent = 'Загрузка…'
      let questions
      try {
        const seenKey = `colombia-exam-mini-test-seen-${topic}`
        let seen = JSON.parse(localStorage.getItem(seenKey) || '[]').filter(Number.isInteger)
        const load = () => fetch(`${api}/questions?limit=5&topic=${encodeURIComponent(topic)}&exclude=${seen.join(',')}`)
        let response = await load()
        if (!response.ok) throw new Error('Не удалось получить вопросы')
        questions = await response.json()
        if (!questions.length && seen.length) { seen = []; response = await load(); questions = await response.json() }
        if (!Array.isArray(questions) || !questions.length) throw new Error('Для этого раздела пока нет вопросов')
        localStorage.setItem(seenKey, JSON.stringify([...new Set([...seen, ...questions.map(question => question.id)])]))
      } catch (error) {
        alert(error.message || 'Мини-тест не удалось открыть. Попробуйте ещё раз.')
        button.disabled = false; button.textContent = 'Мини-тест: 5 вопросов'; return
      }
      button.disabled = false; button.textContent = 'Мини-тест: 5 вопросов'
      const overlay = document.createElement('div')
      overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;overflow:auto;padding:28px;background:#06101d !important;color:#eef4ff !important'
      let index = 0, correct = 0
      const mistakes = []
      const speak = async (text, speaker) => {
        speaker.disabled = true; speaker.textContent = 'Озвучивание…'
        try { const response = await fetch(`${api}/consultant/speech`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, locale: 'ru-RU' }) }); new Audio(URL.createObjectURL(await response.blob())).play() }
        catch { alert('Не удалось подготовить аудио.') }
        finally { speaker.disabled = false; speaker.textContent = '🔊 Прослушать правильный ответ' }
      }
      const showReview = () => {
        overlay.innerHTML = `<h2 style="color:#fff">Результат: ${correct} / ${questions.length}</h2><p style="color:#d6e6ef">${mistakes.length ? 'Разберите ошибки: правильный ответ и объяснение доступны по каждому вопросу.' : 'Отлично! Все ответы верные.'}</p>${mistakes.map((item, number) => `<section class="mini-review" style="margin:16px 0;padding:16px;border:1px solid #d56a6a;border-radius:10px;color:#fff"><b>Ошибка ${number + 1}</b><p>${escapeHtml(item.question)}</p><p><strong>Правильный ответ:</strong> ${escapeHtml(item.right)}</p><p>${escapeHtml(item.explanation || 'Объяснение будет добавлено в банк вопросов.')}</p><button data-speak="${number}" style="background:#ffd12a;color:#07111a;border:0;padding:10px 14px;border-radius:8px;font-weight:700">🔊 Прослушать правильный ответ</button></section>`).join('')}<button id="close" style="background:#234158;color:#fff;border:1px solid #5d8198;padding:10px 14px;border-radius:8px">Закрыть</button>`
        overlay.querySelector('#close').onclick = () => overlay.remove()
        overlay.querySelectorAll('[data-speak]').forEach(speaker => { const item = mistakes[Number(speaker.dataset.speak)]; speaker.onclick = () => speak(`Правильный ответ. ${item.right}. ${item.explanation || ''}`, speaker) })
      }
      const draw = () => {
        const q = questions[index]
        overlay.innerHTML = `<button id="close" style="background:#234158;color:#fff;border:1px solid #5d8198;padding:8px 12px">Закрыть ×</button><h2 style="color:#fff">Мини-тест · ${index + 1} / ${questions.length}</h2><h3 style="color:#fff">${escapeHtml(q.question_ru || q.question_es)}</h3>${['A', 'B', 'C', 'D'].map(letter => `<button data-answer="${letter}" style="${buttonStyle}">${letter}. ${escapeHtml(q['answer_' + letter.toLowerCase() + '_ru'] || q['answer_' + letter.toLowerCase()])}</button>`).join('')}`
        overlay.querySelector('#close').onclick = () => overlay.remove()
        overlay.querySelectorAll('[data-answer]').forEach(option => option.onclick = async () => {
          const answer = option.dataset.answer
          const response = await fetch(`${api}/questions/${q.id}/answer`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answer }) })
          const result = await response.json()
          const right = q['answer_' + result.correct_answer.toLowerCase() + '_ru'] || q['answer_' + result.correct_answer.toLowerCase()]
          const explanation = result.explanation_ru || result.explanation_es || ''
          if (result.correct) correct++; else mistakes.push({ question: q.question_ru || q.question_es, right, explanation })
          overlay.querySelectorAll('[data-answer]').forEach(item => item.disabled = true)
          overlay.innerHTML += `<section style="margin-top:16px;padding:14px;border:1px solid #38e0d0;color:#fff"><b>${result.correct ? '✓ Верно' : '✕ Неверно'}</b><p>Правильный ответ: ${escapeHtml(right)}</p><p>${escapeHtml(explanation)}</p><button id="next" style="background:#ffd12a;color:#07111a;border:0;padding:10px 14px;border-radius:8px;font-weight:700">${index + 1 < questions.length ? 'Следующий вопрос' : 'Перейти к разбору'}</button></section>`
          overlay.querySelector('#next').onclick = () => { index++; index < questions.length ? draw() : showReview() }
        })
      }
      document.body.append(overlay); draw()
    })
    lesson.append(button)
  })
  new MutationObserver(render).observe(document.documentElement, { childList: true, subtree: true }); render()
})()

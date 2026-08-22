(() => {
  const API = 'http://127.0.0.1:8000/api'
  const css = document.createElement('style')
  css.textContent = `
    .study-plan-card{border:1px solid #3f5968;background:linear-gradient(135deg,#101b25,#071017);border-radius:18px;margin:0 0 18px;padding:22px;color:#eef7fb;box-shadow:0 12px 30px #0005}
    .study-plan-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}
    .study-plan-head h2{margin:0;font-size:20px;letter-spacing:.03em}
    .study-plan-head p,.study-plan-muted{color:#aebdc8;margin:6px 0 0;font-size:13px;line-height:1.4}
    .study-plan-date{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
    .study-plan-date input{color:#fff;background:#081216;border:1px solid #52777b;border-radius:8px;padding:9px}
    .study-plan-card button{border:0;border-radius:9px;background:#ffd12a;color:#091116;padding:10px 12px;font-weight:800}
    .study-plan-card button.secondary{background:#112631;color:#dff6f6;border:1px solid #395866}
    .study-plan-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0}
    .study-plan-metrics span{background:#07151c;border:1px solid #223845;border-radius:10px;padding:11px;color:#9eb3bf}
    .study-plan-metrics b{display:block;color:#fff;font-size:22px}
    .study-plan-steps{display:grid;gap:9px;margin-top:13px}
    .study-plan-step{display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:center;border:1px solid #263b48;background:#0b1720;border-radius:11px;padding:11px}
    .study-plan-step i{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;font-style:normal;background:#18313d;color:#38e0d0;font-weight:800}
    .study-plan-step strong{display:block;font-size:14px}
    .study-plan-step small{color:#91a8b5}
    .study-plan-modules{display:flex;gap:8px;overflow:auto;padding-bottom:2px;margin-top:12px}
    .study-plan-modules span{white-space:nowrap;border:1px solid #2e4a59;background:#0b1b24;border-radius:999px;padding:8px 10px;color:#cfe4e8;font-size:12px}
    .study-session{position:fixed;z-index:10000;inset:0;background:#061019;color:#eefafa;padding:24px;overflow:auto}
    .study-session article{max-width:780px;margin:auto}
    .study-session h2{line-height:1.35}
    .study-session button{display:block;width:100%;margin:9px 0;padding:13px;text-align:left;background:#102630;color:#fff;border:1px solid #39606a;border-radius:9px}
    .study-session .close{width:auto;background:#23404b}
    .study-session .correct{border-color:#47df93;background:#16452f}
    .study-session .wrong{border-color:#ff8585;background:#4b1c25}
    @media(max-width:650px){.study-plan-head{display:grid}.study-plan-date{justify-content:flex-start}.study-plan-metrics{grid-template-columns:repeat(2,1fr)}.study-plan-step{grid-template-columns:30px 1fr}.study-plan-step em{grid-column:2;font-style:normal}}
  `
  document.head.append(css)

  const ruTopic = (topic) => ({
    Castellano: 'Испанский',
    Historia: 'История',
    Geografía: 'География',
    Cultura: 'Культура',
    Naturalización: 'Натурализация',
    Constitución: 'Конституция',
  }[topic] || topic)

  async function json(path, options) {
    const response = await fetch(`${API}${path}`, options)
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
    return response.json()
  }

  async function answer(questionId, key) {
    return json(`/questions/${questionId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer: key }),
    })
  }

  async function startSession(limit) {
    const data = await json(`/study-plan/questions?limit=${Math.max(5, Math.min(50, limit || 12))}`)
    let index = 0
    let score = 0
    const modal = document.createElement('section')
    modal.className = 'study-session'
    document.body.append(modal)

    const draw = () => {
      const question = data.questions[index]
      if (!question) {
        modal.innerHTML = `<article><h2>Урок дня завершен: ${score} / ${data.questions.length}</h2><p class="study-plan-muted">Ошибки автоматически попадут в повторение.</p><button class="close">Закрыть</button></article>`
        modal.querySelector('.close').onclick = () => modal.remove()
        return
      }
      modal.innerHTML = `<article><button class="close">Закрыть</button><p class="study-plan-muted">Вопрос ${index + 1} из ${data.questions.length} · ${ruTopic(question.topic)}</p><h2>${question.question_ru || question.question_es}</h2>${['A', 'B', 'C', 'D'].map((key) => `<button data-answer="${key}"><b>${key}.</b> ${question[`answer_${key.toLowerCase()}_ru`] || question[`answer_${key.toLowerCase()}`]}</button>`).join('')}</article>`
      modal.querySelector('.close').onclick = () => modal.remove()
      modal.querySelectorAll('[data-answer]').forEach((button) => {
        button.onclick = async () => {
          modal.querySelectorAll('[data-answer]').forEach((item) => { item.disabled = true })
          const result = await answer(question.id, button.dataset.answer)
          score += result.correct ? 1 : 0
          button.className = result.correct ? 'correct' : 'wrong'
          window.setTimeout(() => { index += 1; draw() }, 750)
        }
      })
    }
    draw()
  }

  function render(plan) {
    let card = document.querySelector('.study-plan-card')
    const target = document.querySelector('.content') || document.querySelector('.app-shell') || document.body
    if (!card) {
      card = document.createElement('section')
      card.className = 'study-plan-card'
      target.prepend(card)
    }

    if (plan.mode === 'setup') {
      card.innerHTML = `<div class="study-plan-head"><div><h2>План подготовки</h2><p>Укажите дату экзамена, чтобы приложение разложило 646 вопросов по дням.</p></div><div class="study-plan-date"><input type="date"><button class="save">Сохранить</button></div></div>`
    } else {
      card.innerHTML = `
        <div class="study-plan-head">
          <div><h2>План дня</h2><p>${plan.mode} режим · фокус: ${plan.focus_topics.map((item) => ruTopic(item.topic)).slice(0, 3).join(', ')}</p></div>
          <div class="study-plan-date"><input type="date" value="${plan.exam_date}"><button class="save">Сохранить</button><button class="listen secondary">Слушать модуль дня</button><button class="start">Начать урок</button></div>
        </div>
        <div class="study-plan-metrics">
          <span>До экзамена<b>${plan.days_left}</b>дней</span>
          <span>Новые<b>${plan.daily_new}</b>вопросов</span>
          <span>Повторить<b>${plan.daily_reviews}</b>вопросов</span>
          <span>Время<b>${plan.estimated_minutes}</b>минут</span>
        </div>
        <div class="study-plan-modules">${plan.modules.map((item) => `<span>${item.module}: ${item.unseen} новых</span>`).join('')}</div>
        <div class="study-plan-steps">${plan.lesson.map((item) => `<div class="study-plan-step"><i>${item.step}</i><span><strong>${item.title}</strong><small>${item.description}</small></span><em>${item.count ? `${item.count} шт.` : `${item.minutes} мин.`}</em></div>`).join('')}</div>
      `
      card.querySelector('.listen').onclick = () => {
        if (!plan.audio_lesson) return
        const played = window.ColombiaAudioLibrary?.playLessonByTopic?.(plan.audio_lesson.id)
        if (!played) window.location.href = `/audio/${plan.audio_lesson.file}`
      }
      card.querySelector('.start').onclick = () => startSession(plan.target_questions)
    }

    const input = card.querySelector('input')
    card.querySelector('.save').onclick = async () => {
      if (!input.value) return
      const updated = await json('/study-plan', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam_date: input.value }),
      })
      render(await json(`/study-plan/today?exam_date=${encodeURIComponent(updated.exam_date)}`))
    }
  }

  async function boot() {
    try {
      render(await json('/study-plan/today'))
    } catch (error) {
      console.error('Study plan failed:', error)
    }
  }

  const observer = new MutationObserver(() => {
    if (document.querySelector('.content') && !document.querySelector('.study-plan-card')) boot()
  })
  observer.observe(document.documentElement, { childList: true, subtree: true })
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot)
  else boot()
})()

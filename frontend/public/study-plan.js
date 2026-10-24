(() => {
  const API = window.COLOMBIA_API_BASE || 'http://127.0.0.1:8000/api'
  let currentPlan = null
  const L=window.ColombiaLocales, t=(key,values)=>L.escape(L.ui(key,values)), topic=value=>L.text(ruTopic(value))
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
    .study-plan-metrics button{background:#07151c;border:1px solid #223845;border-radius:10px;padding:11px;color:#9eb3bf;text-align:left;cursor:pointer}
    .study-plan-metrics button:hover,.study-plan-metrics button:focus-visible,.study-plan-modules button:hover,.study-plan-modules button:focus-visible{border-color:#38e0d0;background:#102631;outline:none;box-shadow:0 0 0 2px #38e0d033}
    .study-plan-metrics b{display:block;color:#fff;font-size:22px}
    .study-plan-steps{display:grid;gap:9px;margin-top:13px}
    .study-plan-step{display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:center;border:1px solid #263b48;background:#0b1720;border-radius:11px;padding:11px;text-align:left;color:inherit;width:100%;cursor:pointer}
    .study-plan-step:hover,.study-plan-step:focus-visible{border-color:#38e0d0;background:#102631;outline:none;box-shadow:0 0 0 2px #38e0d033}
    .study-plan-step i{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;font-style:normal;background:#18313d;color:#38e0d0;font-weight:800}
    .study-plan-step strong{display:block;font-size:14px}
    .study-plan-step small{color:#91a8b5}
    .study-plan-modules{display:flex;gap:8px;overflow:auto;padding-bottom:2px;margin-top:12px}
    .study-plan-modules button{white-space:nowrap;border:1px solid #2e4a59;background:#0b1b24;border-radius:999px;padding:8px 10px;color:#cfe4e8;font-size:12px;cursor:pointer}
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

  async function answer(questionId, key, responseTimeSeconds) {
    return json(`/questions/${questionId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer: key, response_time_seconds: responseTimeSeconds }),
    })
  }

  async function startSession(limit) {
    const data = await json(`/study-plan/questions?limit=${Math.max(5, Math.min(50, limit || 12))}`)
    let index = 0
    let score = 0
    const modal = document.createElement('section')
    modal.className = 'study-session'
    document.body.append(modal)
    let questionStartedAt = Date.now()

    const draw = () => {
      const question = data.questions[index]
      if (!question) {
        questionStartedAt = Date.now()
      modal.innerHTML = `<article><h2>${t('lessonDone',{score,total:data.questions.length})}</h2><p class="study-plan-muted">${t('mistakesQueued')}</p><button class="close">${t('close')}</button></article>`
        modal.querySelector('.close').onclick = () => modal.remove()
        return
      }
      modal.innerHTML = `<article><button class="close">${t('close')}</button><p class="study-plan-muted">${t('questionCount',{index:index+1,total:data.questions.length})} · ${L.escape(topic(question.topic))}</p><h2>${window.ColombiaLocales.escape(question.display_question || question.question_es)}</h2>${question.translation_available === false && question.requested_locale !== 'es' ? `<p role="status">${window.ColombiaLocales.escape(window.ColombiaLocales.fallback())}</p>` : ''}${['A', 'B', 'C', 'D'].map((key) => `<button data-answer="${key}"><b>${key}.</b> ${window.ColombiaLocales.escape(question.display_options?.[key] || question[`answer_${key.toLowerCase()}`])}</button>`).join('')}</article>`
      modal.querySelector('.close').onclick = () => modal.remove()
      modal.querySelectorAll('[data-answer]').forEach((button) => {
        button.onclick = async () => {
          modal.querySelectorAll('[data-answer]').forEach((item) => { item.disabled = true })
          try {
            const result = await answer(question.id, button.dataset.answer, Math.max(0, (Date.now() - questionStartedAt) / 1000))
            score += result.correct ? 1 : 0
            button.className = result.correct ? 'correct' : 'wrong'
            window.setTimeout(() => { index += 1; draw() }, 750)
          } catch {
            modal.querySelectorAll('[data-answer]').forEach(item=>{item.disabled=false})
            let error=modal.querySelector('[role=alert]');if(!error){error=document.createElement('p');error.setAttribute('role','alert');modal.querySelector('article').append(error)}
            error.textContent=L.ui('answerError')
          }
        }
      })
    }
    draw()
  }

  function clickNav(pattern) {
    const button = [...document.querySelectorAll('.nav')].find((item) => pattern.test(item.dataset.nav || '') || pattern.test(item.textContent))
    if (button) {
      button.click()
      return true
    }
    return false
  }

  function playAudioLesson(plan) {
    if (!plan.audio_lesson) return
    const played = window.ColombiaAudioLibrary?.playLessonByTopic?.(plan.audio_lesson.id)
    if (!played) window.location.href = `/audio/${plan.audio_lesson.file}`
  }

  function runLessonStep(plan, item) {
    switch(item.kind) {
      case 'theory': playAudioLesson(plan); return
      case 'new': case 'test': startSession(item.count || plan.daily_new || 6); return
      case 'review': if (!clickNav(/^Repaso$/)) startSession(item.count || plan.daily_reviews || 5); return
      case 'errors': if (!clickNav(/^Errores$/)) startSession(item.count || 5); return
      case 'exam': if (!clickNav(/^Examen$/)) startSession(item.count || 30); return
    }
    startSession(item.count || plan.target_questions)
  }

  function runMetricAction(action, plan) {
    if (action === 'date' || action === 'time') {
      document.querySelector('.study-plan-date input')?.focus()
      return
    }
    if (action === 'new') {
      startSession(plan.daily_new || 6)
      return
    }
    if (action === 'review') {
      if (!clickNav(/Повторение|Repaso/)) startSession(plan.daily_reviews || 5)
    }
  }

  function render(plan) {
    currentPlan = plan
    let card = document.querySelector('.study-plan-card')
    const target = document.querySelector('.content') || document.querySelector('.app-shell') || document.body
    if (!card) {
      card = document.createElement('section')
      card.className = 'study-plan-card'
      target.prepend(card)
    }

    if (plan.mode === 'setup') {
      card.innerHTML = `<div class="study-plan-head"><div><h2>${t('planTitle')}</h2><p>${t('setup',{count:plan.total_available})}</p></div><div class="study-plan-date"><input type="date"><button class="save">${t('save')}</button></div></div>`
    } else {
      card.innerHTML = `
        <div class="study-plan-head">
          <div><h2>${t('today')}</h2><p>${t('focus',{mode:L.ui({'спокойный':'calm','нормальный':'normal','интенсивный':'intensive','финальный рывок':'final'}[plan.mode]||'normal'),topics:plan.focus_topics.map(item=>topic(item.topic)).slice(0,3).join(', ')})}</p></div>
          <div class="study-plan-date"><input type="date" value="${L.escape(plan.exam_date)}"><button class="save">${t('save')}</button><button class="listen secondary">${t('listenDay')}</button><button class="start">${t('startLesson')}</button></div>
        </div>
        <div class="study-plan-metrics">
          <button type="button" data-plan-action="date">${t('untilExam')}<b>${plan.days_left}</b>${t('days')}</button>
          <button type="button" data-plan-action="new">${t('newQuestions')}<b>${plan.daily_new}</b>${t('questions')}</button>
          <button type="button" data-plan-action="review">${t('review')}<b>${plan.daily_reviews}</b>${t('questions')}</button>
          <button type="button" data-plan-action="time">${t('time')}<b>${plan.estimated_minutes}</b>${t('minutes')}</button>
        </div>
        <div class="study-plan-modules">${plan.modules.map((item, index) => `<button type="button" data-module-index="${index}">${t('newCount',{topic:topic(item.module),count:item.unseen})}</button>`).join('')}</div>
        <div class="study-plan-steps">${plan.lesson.map((item, index) => `<button class="study-plan-step" type="button" data-step-index="${index}"><i>${item.step}</i><span><strong>${t(item.kind==='review'?'reviewStep':item.kind,{topic:topic(item.title.replace(/^Теория: /,''))})}</strong><small>${t(item.kind+'Description')}</small></span><em>${item.count ? t('itemCount',{count:item.count}) : t('minuteCount',{count:item.minutes})}</em></button>`).join('')}</div>
      `
      card.querySelector('.listen').onclick = () => {
        playAudioLesson(plan)
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

  window.addEventListener('colombia:locale-changed',()=>{if(currentPlan)render(currentPlan)})

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
  document.addEventListener('click', (event) => {
    const button = event.target.closest?.('.study-plan-step')
    if (!button || !currentPlan?.lesson) return
    event.preventDefault()
    const item = currentPlan.lesson[Number(button.dataset.stepIndex)]
    if (item) runLessonStep(currentPlan, item)
  })
  document.addEventListener('click', (event) => {
    const metric = event.target.closest?.('[data-plan-action]')
    if (metric && currentPlan) {
      event.preventDefault()
      runMetricAction(metric.dataset.planAction, currentPlan)
      return
    }
    const module = event.target.closest?.('[data-module-index]')
    if (module && currentPlan?.modules) {
      event.preventDefault()
      const item = currentPlan.modules[Number(module.dataset.moduleIndex)]
      if (item?.module) {
        const target = [...document.querySelectorAll('.plan-item')].find(planItem => planItem.textContent.includes(item.module))
        if (target) target.click()
        else clickNav(/Entrenamiento|Тренировка/)
      }
    }
  })
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return
    const button = event.target.closest?.('.study-plan-step')
    if (!button || !currentPlan?.lesson) return
    event.preventDefault()
    const item = currentPlan.lesson[Number(button.dataset.stepIndex)]
    if (item) runLessonStep(currentPlan, item)
  })
  observer.observe(document.documentElement, { childList: true, subtree: true })
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot)
  else boot()
})()

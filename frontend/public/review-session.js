(() => {
  const API = window.COLOMBIA_API_BASE
  const L=window.ColombiaLocales, t=(key,values)=>L.escape(L.ui(key,values))
  const apply = () => {
    const page = document.querySelector('main.training[data-screen="Repaso"]')
    if (!page || page.querySelector('.review-session')) return
    const session = document.createElement('section'); session.className = 'review-session'
    page.querySelector('.repeat-empty-state')?.remove(); page.append(session)
    const render = questions => {
      let index = 0
      const show = () => {
        const q = questions[index]
        if (!q) { session.innerHTML=`<div class="review-done"><b>✓</b><h2>${t('reviewDone')}</h2><p>${t('reviewNextDate')}</p></div>`; return }
        const answers = ['A','B','C','D'].map(key => `<button data-answer="${key}"><b>${key}</b>${window.ColombiaLocales.escape(q.display_options?.[key] || q[`answer_${key.toLowerCase()}`])}</button>`).join('')
        session.innerHTML = `<small>${t('reviewCount',{index:index+1,total:questions.length})}</small><h1>${window.ColombiaLocales.escape(q.display_question || q.question_es)}</h1>${q.translation_available === false && q.requested_locale !== 'es' ? `<p role="status">${window.ColombiaLocales.escape(window.ColombiaLocales.fallback())}</p>` : ''}${q.content_locale !== 'es' ? `<p class="review-original">ES: ${window.ColombiaLocales.escape(q.question_es)}</p>` : ''}<div class="review-answers">${answers}</div><p class="review-result"></p>`
        session.querySelectorAll('[data-answer]').forEach(button => button.onclick = async () => {
          const response = await fetch(`${API}/questions/${q.id}/answer`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answer:button.dataset.answer})})
          const result = await response.json(); const note = session.querySelector('.review-result')
          window.dispatchEvent(new Event('reviews:updated'))
          session.querySelectorAll('[data-answer]').forEach(item => item.disabled = true)
          note.textContent = `${window.ColombiaLocales.text(result.correct ? 'Верно.' : 'Неверно.')} ${result.display_explanation || result.explanation_es}`
          note.className = `review-result ${result.correct ? 'right' : 'wrong'}`
          const next = document.createElement('button'); next.className='review-next'; next.textContent=window.ColombiaLocales.text('Следующий вопрос →'); next.onclick=()=>{index += 1; show()}; session.append(next)
        })
      }; show()
    }
    session.innerHTML=`<p class="review-loading">${t('reviewLoading')}</p>`
    fetch(`${API}/review/due`).then(r=>r.ok?r.json():Promise.reject()).then(items => {
      if (!items.length) { session.innerHTML=`<div class="review-done"><b>✓</b><h2>${t('reviewEmpty')}</h2><p>${t('reviewEmptyDescription')}</p></div>`; return }
      render(items)
    }).catch(()=>session.innerHTML=`<p class="review-result wrong">${t('reviewError')}</p>`)
  }
  apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
})()

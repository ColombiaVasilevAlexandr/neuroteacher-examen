(() => {
  const API = 'http://127.0.0.1:8000/api'
  const drills = [
    { title: 'Presente: yo', hint: 'Yo ___ en Colombia.', answer: 'vivo', note: 'С yo глагол vivir: vivo.' },
    { title: 'Presente: nosotros', hint: 'Nosotros ___ español.', answer: 'hablamos', note: 'С nosotros окончание -amos.' },
    { title: 'Вежливое обращение', hint: '¿Cómo ___ usted?', answer: 'esta', note: 'Фраза: ¿Cómo está usted?' },
  ]
  const words = [
    ['ciudad', 'город'], ['documento', 'документ'], ['derecho', 'право'],
    ['historia', 'история'], ['pregunta', 'вопрос'], ['respuesta', 'ответ'],
  ]

  const open = () => {
    if (document.querySelector('.spanish-lab')) return
    const modal = document.createElement('section')
    modal.className = 'spanish-lab'
    modal.innerHTML = `<div class="spanish-lab__window">
      <header><div><small>CASTELLANO · A2–B1</small><h1>Практика испанского</h1><p>Грамматика, слова и экзаменационные вопросы.</p></div><button class="spanish-lab__close" aria-label="Закрыть">×</button></header>
      <nav><button class="active" data-tab="grammar">Грамматика</button><button data-tab="words">Словарь</button><button data-tab="test">Тест</button></nav>
      <main class="spanish-lab__content"></main>
    </div>`
    document.body.append(modal)
    const content = modal.querySelector('.spanish-lab__content')
    const showGrammar = () => {
      const drill = drills[Math.floor(Math.random() * drills.length)]
      content.innerHTML = `<article class="spanish-card"><span>Короткое упражнение</span><h2>${drill.title}</h2><p class="spanish-sentence">${drill.hint.replace('___', '<input autocomplete="off" aria-label="Ответ">')}</p><button class="spanish-primary">Проверить</button><p class="spanish-feedback"></p></article><aside class="spanish-tip"><b>Подсказка</b><p>Читайте фразу вслух, затем впишите только недостающее слово.</p></aside>`
      content.querySelector('.spanish-primary').onclick = () => {
        const value = content.querySelector('input').value.trim().toLocaleLowerCase()
        const feedback = content.querySelector('.spanish-feedback')
        const right = value.normalize('NFD').replace(/[\u0300-\u036f]/g, '') === drill.answer
        feedback.textContent = right ? `Верно. ${drill.note}` : `Правильный вариант: ${drill.answer}. ${drill.note}`
        feedback.className = `spanish-feedback ${right ? 'right' : 'wrong'}`
      }
    }
    const showWords = () => {
      content.innerHTML = `<p class="spanish-intro">Нажмите на карточку, чтобы увидеть перевод. Повторяйте слова вслух.</p><div class="spanish-words">${words.map(([es, ru]) => `<button data-ru="${ru}"><b>${es}</b><span>нажмите, чтобы перевести</span></button>`).join('')}</div>`
      content.querySelectorAll('.spanish-words button').forEach(button => button.onclick = () => {
        const open = button.classList.toggle('revealed')
        button.querySelector('span').textContent = open ? button.dataset.ru : 'нажмите, чтобы перевести'
      })
    }
    const showTest = async () => {
      content.innerHTML = '<p class="spanish-loading">Подбираю вопрос по Castellano…</p>'
      try {
        const items = await fetch(`${API}/questions?topic=Castellano&limit=1`).then(r => r.json())
        const q = items[0]
        if (!q) throw new Error()
        const choices = ['A', 'B', 'C', 'D'].map(key => `<button data-answer="${key}"><b>${key}</b>${q[`answer_${key.toLowerCase()}`]}</button>`).join('')
        content.innerHTML = `<article class="spanish-card"><span>Экзаменационный вопрос</span><h2>${q.question_es}</h2><div class="spanish-options">${choices}</div><p class="spanish-feedback"></p></article>`
        content.querySelectorAll('[data-answer]').forEach(button => button.onclick = async () => {
          const result = await fetch(`${API}/questions/${q.id}/answer`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({answer: button.dataset.answer}) }).then(r => r.json())
          content.querySelectorAll('[data-answer]').forEach(item => item.disabled = true)
          const feedback = content.querySelector('.spanish-feedback')
          feedback.textContent = result.correct ? `Верно. ${result.explanation_es}` : `Неверно. ${result.explanation_es}`
          feedback.className = `spanish-feedback ${result.correct ? 'right' : 'wrong'}`
        })
      } catch { content.innerHTML = '<p class="spanish-feedback wrong">Не удалось загрузить вопрос. Проверьте, что API запущен.</p>' }
    }
    const render = tab => ({ grammar: showGrammar, words: showWords, test: showTest }[tab])()
    modal.querySelector('.spanish-lab__close').onclick = () => modal.remove()
    modal.addEventListener('click', event => { if (event.target === modal) modal.remove() })
    modal.querySelectorAll('nav button').forEach(button => button.onclick = () => {
      modal.querySelectorAll('nav button').forEach(item => item.classList.toggle('active', item === button)); render(button.dataset.tab)
    })
    render('grammar')
  }
  const addButton = () => {
    const tools = document.querySelector('.quick > div')
    if (!tools || tools.querySelector('.spanish-lab-launch')) return
    const button = document.createElement('button')
    button.className = 'spanish-lab-launch'
    button.innerHTML = '<i>ES</i><span>Практика<br>испанского</span>'
    button.onclick = open
    tools.append(button)
  }
  addButton()
  new MutationObserver(addButton).observe(document.documentElement, {childList:true, subtree:true})
})()

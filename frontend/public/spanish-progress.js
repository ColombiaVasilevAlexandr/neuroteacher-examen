(() => {
  const API = 'http://127.0.0.1:8000/api'
  const open = async () => {
    if (document.querySelector('.spanish-progress')) return
    const view = document.createElement('section')
    view.className = 'spanish-progress'
    view.innerHTML = '<div class="spanish-progress__window"><header><div><small>CASTELLANO · ПРОГРЕСС</small><h1>Ваш испанский</h1><p>Собираем реальные результаты практики.</p></div><button aria-label="Закрыть">×</button></header><main><p class="spanish-progress__loading">Загружаю результаты…</p></main></div>'
    view.querySelector('header button').onclick = () => view.remove()
    view.onclick = event => { if (event.target === view) view.remove() }
    document.body.append(view)
    try {
      const attempts = await fetch(`${API}/attempts?limit=200`).then(r => r.json())
      const spanish = attempts.filter(item => item.topic === 'Castellano')
      const correct = spanish.filter(item => item.correct).length
      const score = spanish.length ? Math.round(correct / spanish.length * 100) : 0
      const words = JSON.parse(localStorage.getItem('spanishWordsKnown') || '[]').length
      const level = score >= 85 ? 'Уверенный уровень' : score >= 65 ? 'Хорошая основа' : score ? 'Нужна практика' : 'Начните с первого упражнения'
      view.querySelector('main').innerHTML = `<div class="spanish-progress__score"><strong>${score}%</strong><span>${level}</span></div><div class="spanish-progress__metrics"><article><b>${spanish.length}</b><span>тестовых ответов</span></article><article><b>${correct}</b><span>правильных</span></article><article><b>${words}</b><span>слов запомнено</span></article></div><article class="spanish-progress__next"><b>Следующий шаг</b><p>${spanish.length < 5 ? 'Пройдите пять вопросов в разделе «Практика испанского».': score < 80 ? 'Повторите грамматику и пройдите ещё пять вопросов.' : 'Отлично. Продолжайте словарь и диалоги.'}</p></article>`
    } catch { view.querySelector('main').innerHTML = '<p class="spanish-feedback wrong">Не удалось получить статистику. Убедитесь, что программа запущена.</p>' }
  }
  const add = () => {
    const tools = document.querySelector('.quick > div')
    if (!tools || tools.querySelector('.spanish-progress-launch')) return
    const button = document.createElement('button')
    button.className = 'spanish-progress-launch'
    button.innerHTML = '<i>⌁</i><span>Прогресс<br>испанского</span>'
    button.onclick = open; tools.append(button)
  }
  add(); new MutationObserver(add).observe(document.documentElement, {childList:true,subtree:true})
})()

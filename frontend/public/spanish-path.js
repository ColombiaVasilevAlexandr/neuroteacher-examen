(() => {
  const lessons = [
    ['1', 'Алфавит и звуки', 'Буквы, ударение, чтение слов.', 160],
    ['2', 'Слова и род', 'Артикли el / la, единственное и множественное число.', 170],
    ['3', 'Глаголы в настоящем', 'ser, estar, tener, vivir, hablar.', 174],
    ['4', 'Вопросы и диалоги', 'Как представиться и отвечать на вопросы экзамена.', 180],
  ]
  const open = () => {
    if (document.querySelector('.spanish-path')) return
    const view = document.createElement('section')
    view.className = 'spanish-path'
    view.innerHTML = `<div class="spanish-path__window"><header><div><small>CASTELLANO · МАРШРУТ</small><h1>Учебный путь по испанскому</h1><p>Каждый урок связан с пособием «Colombia, nuestra casa».</p></div><button aria-label="Закрыть">×</button></header><main>${lessons.map(([n, title, text, page]) => `<article><i>${n}</i><div><b>${title}</b><p>${text}</p></div><nav><a href="/colombia_nuestra_casa_ru.pdf#page=${page}" target="_blank">RU PDF</a><a href="/colombia_nuestra_casa.pdf#page=${page}" target="_blank">ES PDF</a></nav></article>`).join('')}<footer>Совет: пройдите один урок, затем откройте «Практику испанского» и выполните 3–5 заданий.</footer></main></div>`
    view.querySelector('header button').onclick = () => view.remove()
    view.onclick = event => { if (event.target === view) view.remove() }
    document.body.append(view)
  }
  const add = () => {
    const tools = document.querySelector('.quick > div')
    if (!tools || tools.querySelector('.spanish-path-launch')) return
    const button = document.createElement('button')
    button.className = 'spanish-path-launch'
    button.innerHTML = '<i>↗</i><span>Курс<br>испанского</span>'
    button.onclick = open
    tools.append(button)
  }
  add(); new MutationObserver(add).observe(document.documentElement, {childList:true,subtree:true})
})()

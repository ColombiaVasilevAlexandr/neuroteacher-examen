(() => {
  const add = () => {
    if (document.querySelector('.spanish-access')) return
    const button = document.createElement('button')
    button.className = 'spanish-access'
    button.innerHTML = '<b>ES</b><span>Испанский<br>курс</span>'
    button.title = 'Открыть практику испанского'
    button.onclick = () => {
      const practice = document.querySelector('.spanish-lab-launch')
      if (practice) practice.click()
      else alert('Модуль загружается. Обновите страницу через несколько секунд.')
    }
    document.body.append(button)
  }
  add()
  new MutationObserver(add).observe(document.documentElement, { childList: true, subtree: true })
})()

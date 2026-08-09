(() => {
  const add = () => {
    const content = document.querySelector('.spanish-lab__content')
    if (!content || content.querySelector('.spanish-hub-links')) return
    const links = document.createElement('div')
    links.className = 'spanish-hub-links'
    links.innerHTML = '<button data-action="path">Учебный путь и PDF</button><button data-action="progress">Мой прогресс</button>'
    links.querySelector('[data-action="path"]').onclick = () => document.querySelector('.spanish-path-launch')?.click()
    links.querySelector('[data-action="progress"]').onclick = () => document.querySelector('.spanish-progress-launch')?.click()
    content.append(links)
  }
  add(); new MutationObserver(add).observe(document.documentElement,{childList:true,subtree:true})
})()

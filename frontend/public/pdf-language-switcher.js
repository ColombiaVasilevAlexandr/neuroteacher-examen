(() => {
  const russian = 'colombia_nuestra_casa_ru.pdf'
  const spanish = 'colombia_nuestra_casa.pdf'

  const addSwitch = link => {
    if (link.dataset.pdfLanguageReady) return
    link.dataset.pdfLanguageReady = 'true'
    const page = link.getAttribute('href').match(/#page=\d+/)?.[0] ?? ''
    const switcher = document.createElement('span')
    switcher.className = 'pdf-language-switcher'
    switcher.innerHTML = '<button type="button" data-pdf="ru">RU PDF</button><button type="button" data-pdf="es">ES PDF</button>'
    const setSource = source => {
      link.href = `/${source === 'ru' ? russian : spanish}${page}`
      link.textContent = source === 'ru' ? 'Русский PDF' : 'Español PDF'
      switcher.querySelectorAll('button').forEach(button => button.classList.toggle('selected', button.dataset.pdf === source))
    }
    switcher.addEventListener('click', event => {
      const button = event.target.closest('button[data-pdf]')
      if (button) setSource(button.dataset.pdf)
    })
    link.insertAdjacentElement('afterend', switcher)
    setSource('ru')
  }

  const apply = () => document.querySelectorAll('a.language-mark[href*="colombia_nuestra_casa"]').forEach(addSwitch)
  apply()
  new MutationObserver(apply).observe(document.documentElement, { childList: true, subtree: true })
})()

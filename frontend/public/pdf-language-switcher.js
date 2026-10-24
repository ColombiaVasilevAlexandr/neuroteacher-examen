(() => {
  const L = window.ColombiaLocales
  const paths = {ru: 'colombia_nuestra_casa_ru.pdf', es: 'colombia_nuestra_casa.pdf'}
  const label = source => L.ui(source === 'ru' ? 'pdfRussian' : 'pdfSpanish') + (source === 'ru' ? ' · 2021' : ' · 2024')
  const addSwitch = link => {
    if (link.dataset.pdfLanguageReady) return
    link.dataset.pdfLanguageReady = 'true'
    const original = link.getAttribute('href')
    const page = original.match(/#page=\d+/)?.[0] || ''
    const origin = original.includes('_ru.pdf') ? 'ru' : 'es'
    const switcher = document.createElement('span')
    switcher.className = 'pdf-language-switcher'
    switcher.innerHTML = '<button type="button" data-pdf="es">ES · 2024</button><button type="button" data-pdf="ru">RU · 2021</button>'
    const setSource = source => {
      link.dataset.pdfSource = source
      link.href = `/${paths[source]}${source === origin ? page : '#page=1'}`
      link.textContent = label(source)
      switcher.title = L.current === 'ru' ? 'Разные издания: номера страниц не совпадают.' : 'Ediciones distintas: la numeración de páginas no coincide.'
      switcher.querySelectorAll('button').forEach(button => button.classList.toggle('selected', button.dataset.pdf === source))
    }
    switcher.addEventListener('click', event => {
      const button = event.target.closest('button[data-pdf]')
      if (button) setSource(button.dataset.pdf)
    })
    link.insertAdjacentElement('afterend', switcher)
    setSource(origin)
  }
  const apply = () => document.querySelectorAll('a.language-mark[href*="colombia_nuestra_casa"]').forEach(addSwitch)
  window.addEventListener('colombia:locale-changed', () => {
    document.querySelectorAll('a[data-pdf-source]').forEach(link => {link.textContent = label(link.dataset.pdfSource)})
  })
  apply()
  new MutationObserver(apply).observe(document.documentElement, {childList: true, subtree: true})
})()

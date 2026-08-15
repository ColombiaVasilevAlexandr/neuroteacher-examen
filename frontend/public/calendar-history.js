(() => {
  const style = document.createElement('style')
  style.textContent = `
    .streak .week { gap: 8px; overflow-x: auto; justify-content: flex-start; padding: 6px 2px 10px; scrollbar-width: thin; }
    .streak .week > div { flex: 0 0 36px; }
    .streak .week > div.current { margin-top: 0; }
    .streak .week > div[data-has-activity="true"] i { color: #55e980; border-color: #48d976; }
    .streak .week > div[data-has-activity="false"] i { color: #334357; border-color: #334357; }
  `
  document.head.append(style)

  const render = async () => {
    const week = document.querySelector('.streak .week')
    if (!week || week.dataset.historyLoaded) return
    try {
      const response = await fetch('http://127.0.0.1:8000/api/dashboard')
      const dashboard = await response.json()
      if (!Array.isArray(dashboard.calendar)) return
      week.dataset.historyLoaded = 'true'
      week.replaceChildren(...dashboard.calendar.map(({ date, attempts }) => {
        const item = document.createElement('div')
        const current = date === dashboard.calendar.at(-1)?.date
        if (current) item.className = 'current'
        item.dataset.hasActivity = String(attempts > 0)
        const label = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' }).format(new Date(`${date}T12:00:00`))
        item.innerHTML = `<b>${label}</b><i title="${attempts} занятий">${attempts > 0 ? '✓' : '·'}</i>`
        return item
      }))
    } catch (_) {
      // The original five-day calendar stays visible if the API is unavailable.
    }
  }
  new MutationObserver(render).observe(document.documentElement, { childList: true, subtree: true })
  render()
})()

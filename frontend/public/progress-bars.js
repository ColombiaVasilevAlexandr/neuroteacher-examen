(() => {
  const api = 'http://127.0.0.1:8000/api/dashboard'
  let trend = []

  const draw = () => {
    const chart = document.querySelector('.preparation .chart')
    if (!chart || !trend.length || chart.querySelector('.day-success-bars')) return
    const bars = document.createElement('div')
    bars.className = 'day-success-bars'
    trend.forEach(day => {
      const bar = document.createElement('span')
      const score = day.score ?? 0
      bar.style.setProperty('--score', `${Math.max(4, score)}%`)
      bar.dataset.score = day.score === null ? '—' : `${day.score}%`
      bar.title = `${day.date}: ${day.attempts} попыток, ${day.score === null ? 'нет ответов' : `${day.score}% правильно`}`
      bars.appendChild(bar)
    })
    chart.appendChild(bars)
  }

  fetch(api)
    .then(response => response.ok ? response.json() : Promise.reject())
    .then(data => { trend = data.trend ?? []; draw() })
    .catch(() => undefined)

  new MutationObserver(draw).observe(document.documentElement, { childList: true, subtree: true })
})()

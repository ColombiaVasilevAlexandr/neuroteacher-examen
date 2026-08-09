(() => {
  const api = 'http://127.0.0.1:8000/api/dashboard'

  const dateLabel = value => new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' })
    .format(new Date(`${value}T12:00:00`))

  const draw = trend => {
    const chart = document.querySelector('.preparation .chart')
    if (!chart || chart.querySelector('.daily-score-chart') || !trend.length) return

    const width = 1000
    const left = 62
    const right = 950
    const top = 28
    const bottom = 220
    const x = index => left + (right - left) * index / Math.max(trend.length - 1, 1)
    const y = score => bottom - score * 1.65
    const active = trend.filter(day => day.score !== null)
    const points = active.map(day => `${x(trend.indexOf(day))},${y(day.score)}`).join(' ')

    const root = document.createElement('div')
    root.className = 'daily-score-chart'
    root.innerHTML = `
      <svg viewBox="0 0 ${width} 270" preserveAspectRatio="none" aria-label="Результаты по дням">
        <line class="daily-baseline" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}" />
        <line class="daily-target" x1="${left}" y1="${y(80)}" x2="${right}" y2="${y(80)}" />
        ${points ? `<polyline class="daily-line" points="${points}" />` : ''}
        ${trend.map((day, index) => day.score === null
          ? `<circle class="daily-empty" cx="${x(index)}" cy="${bottom}" r="5" />`
          : `<g class="daily-point"><circle cx="${x(index)}" cy="${y(day.score)}" r="10" /><text x="${x(index)}" y="${y(day.score) - 20}">${day.score}%</text></g>`).join('')}
      </svg>
      <div class="daily-labels">${trend.map(day => `<span>${dateLabel(day.date)}</span>`).join('')}</div>`
    chart.replaceChildren(root)
  }

  fetch(api)
    .then(response => response.ok ? response.json() : Promise.reject())
    .then(data => draw(data.trend ?? []))
    .catch(() => undefined)
})()

(() => {
  const topicLabels = {
    '\u0413\u0435\u043e\u0433\u0440\u0430\u0444\u0438\u044f': '\u0413\u0435\u043e\u0433\u0440\u0430\u0444\u0438\u044f',
    '\u0418\u0441\u0442\u043e\u0440\u0438\u044f': '\u0418\u0441\u0442\u043e\u0440\u0438\u044f',
    '\u041a\u043e\u043d\u0441\u0442\u0438\u0442\u0443\u0446\u0438\u044f': '\u041a\u043e\u043d\u0441\u0442\u0438\u0442\u0443\u0446\u0438\u044f',
    '\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439': '\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439',
    '\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439 \u044f\u0437\u044b\u043a': '\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439',
    '\u041a\u0443\u043b\u044c\u0442\u0443\u0440\u0430': '\u041a\u0443\u043b\u044c\u0442\u0443\u0440\u0430',
    '\u041d\u0430\u0442\u0443\u0440\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f': '\u041d\u0430\u0442\u0443\u0440\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f',
    '\u041c\u0438\u043a\u0440\u043e\u0442\u0435\u043c\u044b': '\u041c\u0438\u043a\u0440\u043e\u0442\u0435\u043c\u044b',
  }

  const norm = value => String(value || '').replace(/\s+/g, ' ').trim()

  const startTraining = topic => {
    const planItems = [...document.querySelectorAll('.plan-item')]
    const target = topic
      ? planItems.find(item => norm(item.textContent).includes(topic))
      : null
    if (target) {
      target.click()
      return
    }
    const training = [...document.querySelectorAll('.nav')].find(item => /Entrenamiento|\u0422\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0430/.test(item.textContent))
    training?.click()
  }

  const enhance = () => {
    const weak = document.querySelector('.weak')
    if (!weak) return

    const all = weak.querySelector('.card-title a')
    if (all && !all.dataset.weakTopicsAction) {
      all.dataset.weakTopicsAction = 'all'
      all.textContent = '\u0412\u0441\u0435 \u0442\u0435\u043c\u044b'
      all.href = '#'
      all.setAttribute('role', 'button')
      all.onclick = event => {
        event.preventDefault()
        startTraining(null)
      }
    }

    weak.querySelectorAll('.weak-row').forEach(row => {
      if (row.dataset.weakTopicsAction) return
      const title = norm(row.querySelector('span')?.childNodes?.[0]?.textContent)
      const topic = topicLabels[title] || topicLabels[Object.keys(topicLabels).find(key => title.includes(key))]
      if (!topic) return
      row.dataset.weakTopicsAction = topic
      row.tabIndex = 0
      row.setAttribute('role', 'button')
      row.title = `\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0443: ${title}`
      row.addEventListener('click', () => startTraining(topic))
      row.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          startTraining(topic)
        }
      })
    })
  }

  const style = document.createElement('style')
  style.textContent = `
    .weak .card-title a{cursor:pointer;text-decoration:none}
    .weak-row[role="button"]{cursor:pointer;border-radius:8px;padding:8px;margin-left:-8px;margin-right:-8px}
    .weak-row[role="button"]:hover,.weak-row[role="button"]:focus-visible{background:#102631;outline:1px solid #38e0d066}
  `
  document.head.append(style)

  enhance()
  new MutationObserver(enhance).observe(document.documentElement, { childList: true, subtree: true })
})()

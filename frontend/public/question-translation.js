(() => {
  const L = window.ColombiaLocales
  let entries = new Map(), revision = 0, activeButton = null
  const normalize = value => String(value || '').replace(/^ES:\s*/, '').replace(/\s+/g, ' ').trim()
  const labels = {es:'Escuchar pregunta',ru:'Прослушать вопрос',en:'Listen to the question',de:'Frage anhören',fr:'Écouter la question','zh-Hans':'朗读题目'}
  const notes = {fr:'Traduction automatique comparée à l’original. Les exemples des exercices restent en espagnol.',de:'Maschinelle Übersetzung mit Abgleich am Original. Spanische Übungsbeispiele bleiben auf Spanisch.',en:'Machine translation checked against the original. Spanish exercise examples stay in Spanish.','zh-Hans':'本译文经自动核对。西班牙语练习中的例句保留原文。'}
  function apply() {
    if (activeButton && !activeButton.isConnected) { window.ColombiaSpeech?.stop(); activeButton = null }
    document.querySelectorAll('main.training .question-card, .study-session article').forEach(card => {
      const title = card.querySelector('h1,h2')
      const item = title && entries.get(normalize(title.textContent))
      if (!item) return
      if (title.textContent !== item.display_question) {
        title.textContent = item.display_question
        if (item.content_locale !== 'es' && !card.querySelector('.question-es-original,[lang="es"]')) {
          const original = document.createElement('p')
          original.className = 'question-es-original'; original.lang = 'es'
          original.textContent = 'ES: ' + item.question_es
          title.after(original)
        }
      }
      if (title.lang !== item.content_locale) title.lang = item.content_locale
      if (item.translation_method && notes[L.current] && !card.querySelector('.translation-origin')) {
        const note = document.createElement('small')
        note.className = 'translation-origin'; note.textContent = notes[L.current]
        title.after(note)
      }
      let button = card.querySelector('.localized-question-speech')
      if (!button) {
        button = document.createElement('button'); button.type = 'button'
        button.className = 'localized-question-speech back'
        title.after(button)
      }
      const label = '🔊 ' + (labels[L.current] || labels.es)
      if (activeButton !== button && button.textContent !== label) button.textContent = label
      button.onclick = async () => {
        if (activeButton === button) { window.ColombiaSpeech.stop(); return }
        activeButton = button; button.textContent = '■'
        try {
          await window.ColombiaSpeech.speak(item.display_question, window.ColombiaSpeech.localeFor(item.content_locale))
        } catch {
          button.textContent = '⚠ ' + label
        } finally {
          if (activeButton === button) {activeButton = null; button.textContent = label}
        }
      }
    })
  }
  async function refresh() {
    const token = ++revision, locale = L.current
    window.ColombiaSpeech?.stop()
    try {
      const response = await fetch(window.COLOMBIA_API_BASE + '/questions?limit=1000&locale=' + encodeURIComponent(locale))
      if (!response.ok) return
      const items = await response.json()
      if (token !== revision) return
      entries = new Map()
      items.forEach(item => {
        entries.set(normalize(item.question_es), item)
        entries.set(normalize(item.display_question), item)
      })
      apply()
    } catch {}
  }
  new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
  window.addEventListener('colombia:locale-changed', refresh)
  refresh()
})()

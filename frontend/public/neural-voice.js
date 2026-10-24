(() => {
  const synthesis = window.speechSynthesis
  if (!synthesis) return
  const nativeCancel = synthesis.cancel.bind(synthesis)
  let generation = 0, controller = null, player = null, release = null, active = null
  const clean = value => String(value).replace(/\*{1,3}|#{1,6}|`|_/g, '').replace(/\[(.*?)\]\([^)]*\)/g, '$1').trim()
  const finish = (utterance, error) => {
    if (active !== utterance) return
    active = null
    if (error) utterance.onerror?.({error: 'synthesis-failed'})
    else utterance.onend?.()
  }
  const cancel = () => {
    generation += 1
    controller?.abort()
    controller = null
    if (player) { player.pause(); player.removeAttribute('src'); player = null }
    release?.()
    release = null
    nativeCancel()
    if (active) finish(active)
  }
  const localeFor = locale => ({es:'es-CO',ru:'ru-RU',en:'en-US',de:'de-DE',fr:'fr-FR',zh:'zh-CN'}[String(locale || window.ColombiaLocales?.current || 'es').split('-')[0]] || 'es-CO')
  const textLocale = (text, locale) => /[\u3400-\u9fff]/u.test(text) ? 'zh-CN'
    : /[А-Яа-яЁё]/u.test(text) ? 'ru-RU'
    : /^ru/i.test(locale || '') ? 'es-CO' : localeFor(locale)
  const segments = (text, locale) => clean(text).replace(/\b(ES|RU):/g, '\n')
    .split(/\n+/).flatMap(part => part.split(/(?<=[.!?])\s+(?=[A-ZА-ЯЁ¿¡])/u))
    .map(clean).filter(Boolean).map(text => ({
      text, locale: textLocale(text, locale)
    }))
  const play = (blob, token) => new Promise((resolve, reject) => {
    if (token !== generation) { resolve(); return }
    const url = URL.createObjectURL(blob), audio = new Audio(url)
    let done = false
    const cleanup = error => {
      if (done) return
      done = true
      URL.revokeObjectURL(url)
      if (player === audio) player = null
      if (release === cleanup) release = null
      if (error) reject(error)
      else resolve()
    }
    player = audio; release = cleanup
    audio.onended = () => cleanup()
    audio.onerror = () => cleanup(Error('audio'))
    audio.play().catch(cleanup)
  })
  synthesis.cancel = cancel
  synthesis.speak = utterance => {
    if (typeof utterance === 'string') utterance = {text: utterance}
    if (!utterance?.text) return
    cancel()
    const token = generation
    active = utterance
    controller = new AbortController()
    const signal = controller.signal
    const rate = Math.max(-50, Math.min(100, Math.round(((utterance.rate || 1) - 1) * 100)))
    utterance.onstart?.()
    ;(async () => {
      for (const part of segments(utterance.text, utterance.lang)) {
        if (token !== generation) return
        const response = await fetch(`${window.COLOMBIA_API_BASE}/consultant/speech`, {
          method: 'POST', signal, headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({...part, rate: `${rate >= 0 ? '+' : ''}${rate}%`})
        })
        if (token !== generation) return
        if (!response.ok) throw Error('voice')
        const blob = await response.blob()
        if (token !== generation) return
        await play(blob, token)
      }
      if (token === generation) finish(utterance)
    })().catch(error => {
      if (token === generation && error.name !== 'AbortError') {
        finish(utterance, error)
        window.dispatchEvent(new Event('colombia:speech-error'))
      }
    })
  }
  window.ColombiaSpeech = {
    stop: cancel,
    localeFor,
    speak: (text, lang = 'es-CO', rate = 1) => new Promise((resolve, reject) => {
      synthesis.speak({text, lang, rate, onend: resolve, onerror: reject})
    })
  }
  window.addEventListener('pagehide', cancel)
})()

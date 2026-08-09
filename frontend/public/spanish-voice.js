(() => {
  const synthesis = window.speechSynthesis
  if (!synthesis) return
  const spanishPattern = /[¿¡áéíóúüñ]|\b(el|la|los|las|de|en|que|colombia|bogotá|español|respuesta|capital|gracias|hola)\b/i
  const isSpanish = text => spanishPattern.test(text) && !/[А-Яа-яЁё]/.test(text)
  const selectVoice = () => {
    const voices = synthesis.getVoices()
    return voices.find(v => /^es-CO/i.test(v.lang)) || voices.find(v => /^es-(MX|US)/i.test(v.lang)) || voices.find(v => /^es/i.test(v.lang))
  }
  const baseSpeak = synthesis.speak.bind(synthesis)
  synthesis.speak = utterance => {
    if (utterance?.text && isSpanish(utterance.text)) {
      utterance.lang = 'es-CO'
      const voice = selectVoice()
      if (voice) utterance.voice = voice
      utterance.rate = Math.min(utterance.rate || 1, 0.96)
    }
    baseSpeak(utterance)
  }
  synthesis.onvoiceschanged = () => selectVoice()
})()

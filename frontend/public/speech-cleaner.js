(() => {
  const synthesis = window.speechSynthesis
  if (!synthesis) return
  const originalSpeak = synthesis.speak.bind(synthesis)
  synthesis.speak = utterance => {
    if (utterance?.text) {
      utterance.text = utterance.text
        .replace(/\*{1,3}|#{1,6}|`|_/g, '')
        .replace(/\[(.*?)\]\([^)]*\)/g, '$1')
        .replace(/\s{2,}/g, ' ')
        .trim()
    }
    originalSpeak(utterance)
  }
})()

(() => {
  const nativeFetch = window.fetch.bind(window)
  window.fetch = async (...args) => {
    const url = String(args[0] instanceof Request ? args[0].url : args[0])
    if (!url.includes('/api/ai/chat')) return nativeFetch(...args)
    let lastResponse
    for (let attempt = 0; attempt < 2; attempt += 1) {
      try {
        const response = await nativeFetch(...args)
        if (response.ok || response.status < 500 || attempt === 1) return response
        lastResponse = response
      } catch (error) {
        if (attempt === 1) throw error
      }
      await new Promise(resolve => setTimeout(resolve, 900))
    }
    return lastResponse
  }

  const synthesis = window.speechSynthesis
  if (!synthesis) return

  let currentAudio = null
  const stop = () => {
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.src = ''
      currentAudio = null
    }
  }

  synthesis.cancel = stop
  synthesis.speak = (utterance) => {
    const text = typeof utterance === 'string' ? utterance : utterance?.text
    if (!text) return
    stop()
    utterance?.onstart?.()
    const rate = `${Math.round(((utterance?.rate ?? 1) - 1) * 100)}%`
    fetch('http://127.0.0.1:8000/api/consultant/speech', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, rate }),
    })
      .then(response => {
        if (!response.ok) throw new Error('Speech synthesis failed')
        return response.blob()
      })
      .then(blob => {
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        currentAudio = audio
        audio.onended = () => {
          URL.revokeObjectURL(url)
          currentAudio = null
          utterance?.onend?.()
        }
        audio.onerror = () => {
          URL.revokeObjectURL(url)
          currentAudio = null
          utterance?.onerror?.()
        }
        return audio.play()
      })
      .catch(() => utterance?.onerror?.())
  }
})()

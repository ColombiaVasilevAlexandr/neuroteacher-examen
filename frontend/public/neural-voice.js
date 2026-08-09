(() => {
  const synthesis = window.speechSynthesis
  if (!synthesis) return
  const nativeCancel = synthesis.cancel.bind(synthesis)
  let audio = null
  const clean = value => value.replace(/\*{1,3}|#{1,6}|`|_/g,'').replace(/\[(.*?)\]\([^)]*\)/g,'$1').replace(/\s{2,}/g,' ').trim()
  const spanishPart = value => {
    const paragraphs = value.split(/\n\s*\n/).map(clean).filter(Boolean)
    return paragraphs.find(part => !/[А-Яа-яЁё]/.test(part) && /[¿¡áéíóúüñ]|\b(colombia|cartagena|bogotá|qué|de|el|la|fue)\b/i.test(part)) || clean(value)
  }
  synthesis.cancel = () => { nativeCancel(); if (audio) { audio.pause(); URL.revokeObjectURL(audio.src); audio=null } }
  synthesis.speak = utterance => {
    const original = typeof utterance === 'string' ? utterance : utterance?.text
    if (!original) return
    synthesis.cancel()
    const hasSpanish = /[¿¡áéíóúüñ]|\b(colombia|cartagena|bogotá|qué|de|el|la|fue)\b/i.test(original)
    const text = hasSpanish ? spanishPart(original) : clean(original)
    utterance?.onstart?.()
    const rate = `${Math.round(((utterance?.rate ?? 1) - 1) * 100)}%`
    fetch('http://127.0.0.1:8000/api/consultant/speech', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,rate,locale:hasSpanish?'es-CO':'ru-RU'})})
      .then(response => { if (!response.ok) throw Error('voice'); return response.blob() })
      .then(blob => { const url=URL.createObjectURL(blob); audio=new Audio(url); audio.onended=()=>{URL.revokeObjectURL(url);audio=null;utterance?.onend?.()}; audio.onerror=()=>{URL.revokeObjectURL(url);audio=null;utterance?.onerror?.()}; return audio.play() })
      .catch(()=>utterance?.onerror?.())
  }
})()

(() => {
  const synthesis = window.speechSynthesis
  if (!synthesis) return
  const nativeCancel = synthesis.cancel.bind(synthesis)
  let audio = null, requestId = 0
  const clean = value => value.replace(/\*{1,3}|#{1,6}|`|_/g,'').replace(/\[(.*?)\]\([^)]*\)/g,'$1').replace(/\s{2,}/g,' ').trim()
  const segments = value => value.split(/\n\s*\n/).map(clean).filter(Boolean).map(text => ({text, locale:/[А-Яа-яЁё]/.test(text)?'ru-RU':'es-CO'}))
  const play = blob => new Promise((resolve,reject) => {
    const url=URL.createObjectURL(blob); audio=new Audio(url)
    audio.onended=()=>{URL.revokeObjectURL(url);audio=null;resolve()}
    audio.onerror=()=>{URL.revokeObjectURL(url);audio=null;reject(Error('audio'))}
    audio.play().catch(reject)
  })
  synthesis.cancel = () => { requestId += 1; nativeCancel(); if (audio) { audio.pause(); URL.revokeObjectURL(audio.src); audio=null } }
  synthesis.speak = utterance => {
    const original = typeof utterance === 'string' ? utterance : utterance?.text
    if (!original) return
    synthesis.cancel(); const current = requestId
    utterance?.onstart?.()
    const rate = `${Math.round(((utterance?.rate ?? 1) - 1) * 100)}%`
    ;(async () => {
      for (const part of segments(original)) {
        if (current !== requestId) return
        const response = await fetch('http://127.0.0.1:8000/api/consultant/speech', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:part.text,rate,locale:part.locale})})
        if (!response.ok) throw Error('voice')
        await play(await response.blob())
      }
      if (current === requestId) utterance?.onend?.()
    })().catch(() => { if (current === requestId) utterance?.onerror?.() })
  }
})()

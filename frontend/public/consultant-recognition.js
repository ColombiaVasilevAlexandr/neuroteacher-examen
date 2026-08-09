(() => {
  const NativeRecognition = window.webkitSpeechRecognition || window.SpeechRecognition
  if (NativeRecognition) {
    const SpanishRecognition = function () {
      const recognition = new NativeRecognition()
      return new Proxy(recognition, {
        get(target, property) { const value=Reflect.get(target,property); return typeof value === 'function' ? value.bind(target) : value },
        set(target, property, value) {
          if (property === 'lang' && document.querySelector('.ai-input textarea')) value='es-CO'
          return Reflect.set(target,property,value)
        }
      })
    }
    window.webkitSpeechRecognition = SpanishRecognition
    if (window.SpeechRecognition) window.SpeechRecognition = SpanishRecognition
  }
  const apply = () => {
    const input = document.querySelector('.ai-input')
    if (!input || input.parentElement.querySelector('.consultant-recognition-note')) return
    const note = document.createElement('small'); note.className='consultant-recognition-note'; note.textContent='Микрофон распознаёт испанскую речь · Español (Colombia)'
    input.insertAdjacentElement('beforebegin',note)
  }
  apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
})()

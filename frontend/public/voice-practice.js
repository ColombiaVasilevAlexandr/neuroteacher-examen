(() => {
  const open = (listen, reply) => {
    if (document.querySelector('.voice-practice-dialog')) return
    const dialog = document.createElement('section')
    dialog.className = 'voice-practice-dialog'
    dialog.innerHTML = '<div><button class="voice-practice-close">×</button><small>ГОЛОСОВАЯ ПРАКТИКА</small><h2>Слушайте и отвечайте</h2><p>Сначала прослушайте вопрос, затем дайте ответ голосом. Так тренируется понимание испанской речи и уверенность в ответе.</p><button class="voice-step listen">1. Прослушать вопрос</button><button class="voice-step reply">2. Ответить голосом</button></div>'
    dialog.querySelector('.voice-practice-close').onclick = () => dialog.remove()
    dialog.querySelector('.listen').onclick = () => { dialog.remove(); listen.click() }
    dialog.querySelector('.reply').onclick = () => { dialog.remove(); reply.click() }
    dialog.onclick = event => { if (event.target === dialog) dialog.remove() }
    document.body.append(dialog)
  }
  const apply = () => {
    const buttons = [...document.querySelectorAll('.quick > div > button')]
    const listen = buttons.find(button => /Прослушать вопрос|Escuchar pregunta/.test(button.textContent))
    const reply = buttons.find(button => /Ответить голосом|Responder por voz/.test(button.textContent))
    if (!listen || !reply || document.querySelector('.voice-practice-launch')) return
    listen.style.display = 'none'; reply.style.display = 'none'
    const combined = document.createElement('button')
    combined.className = 'voice-practice-launch'
    combined.innerHTML = '<i>◉</i><span>Голосовая<br>практика</span>'
    combined.onclick = () => open(listen, reply)
    listen.parentElement.prepend(combined)
  }
  apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
})()

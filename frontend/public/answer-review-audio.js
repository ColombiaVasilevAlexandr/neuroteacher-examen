(() => {
  const addPlayer = () => {
    document.querySelectorAll('.feedback.incorrect').forEach(feedback => {
      if (feedback.querySelector('.review-audio')) return
      const correct = document.querySelector('.answers button.right')
      const explanation = feedback.querySelector('p')
      if (!correct || !explanation) return
      const button = document.createElement('button')
      button.className = 'review-audio'
      button.type = 'button'
      button.textContent = '🔊 Прослушать правильный ответ'
      let playing = false
      button.onclick = async () => {
        if (playing) { window.ColombiaSpeech.stop(); return }
        playing = true
        button.textContent = '■ Остановить'
        try {
          await window.ColombiaSpeech.speak(`${correct.innerText}\n\n${explanation.innerText}`, 'es-CO')
          button.textContent = '🔊 Прослушать ещё раз'
        } catch {
          button.textContent = 'Не удалось озвучить — попробуйте ещё раз'
        } finally {
          playing = false
        }
      }
      feedback.append(button)
    })
  }
  const style = document.createElement('style')
  style.textContent = '.review-audio{color:#e9f4ff;background:#12344d;border:1px solid #4aa8ff;border-radius:8px;margin-top:12px;padding:10px 13px;font-weight:700}'
  document.head.append(style)
  new MutationObserver(addPlayer).observe(document.documentElement, {childList: true, subtree: true})
  addPlayer()
})()

(() => {
  const style = document.createElement('style')
  style.textContent = `.review-audio { color: #e9f4ff; background: #12344d; border: 1px solid #4aa8ff; border-radius: 8px; margin-top: 12px; padding: 10px 13px; font-weight: 700; } .review-audio:disabled { opacity: .6; cursor: wait; }`
  document.head.append(style)

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
      button.addEventListener('click', async () => {
        button.disabled = true
        button.textContent = 'Озвучиваем…'
        try {
          const text = `Правильный ответ. ${correct.innerText}. Объяснение. ${explanation.innerText}`
          const response = await fetch('http://127.0.0.1:8000/api/consultant/speech', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, locale: 'ru-RU' })
          })
          if (!response.ok) throw new Error('speech')
          const url = URL.createObjectURL(await response.blob())
          const audio = new Audio(url)
          audio.addEventListener('ended', () => URL.revokeObjectURL(url), { once: true })
          await audio.play()
          button.textContent = '🔊 Прослушать ещё раз'
        } catch (_) {
          button.textContent = 'Не удалось озвучить — попробуйте ещё раз'
        } finally {
          button.disabled = false
        }
      })
      feedback.append(button)
    })
  }
  new MutationObserver(addPlayer).observe(document.documentElement, { childList: true, subtree: true })
  addPlayer()
})()

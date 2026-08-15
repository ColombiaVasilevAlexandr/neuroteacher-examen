(() => {
  const completedKey = 'colombia-exam-audio-lesson-1-completed'
  const style = document.createElement('style')
  style.textContent = `
    .audio-guide { border: 1px solid #4a5b67; background: linear-gradient(135deg, #142831, #0c151d); border-radius: 20px; margin-top: 18px; padding: 22px; box-shadow: inset 0 1px #9eeaff12, 0 14px 32px #0005; }
    .audio-guide__top { align-items: center; justify-content: space-between; gap: 14px; display: flex; }
    .audio-guide h2 { letter-spacing: .05em; margin: 0; font-size: 17px; }
    .audio-guide h2:first-letter { color: #ffd12a; }
    .audio-guide__status { color: #90a6b7; font-size: 12px; }
    .audio-guide__content { align-items: center; gap: 18px; margin-top: 16px; display: flex; }
    .audio-guide__number { color: #101010; background: #ffd12a; border-radius: 50%; place-items: center; flex: 0 0 42px; width: 42px; height: 42px; font-weight: 700; display: grid; }
    .audio-guide p { color: #d6e0e7; margin: 0 0 5px; font-size: 15px; }
    .audio-guide small { color: #8fa2b0; }
    .audio-guide audio { width: min(360px, 100%); margin-left: auto; }
    .audio-guide__complete { color: #071014; background: #55e980; border: 0; border-radius: 9px; padding: 10px 14px; font-weight: 700; }
    .audio-guide.is-complete { border-color: #48d976; }
    @media (max-width: 650px) { .audio-guide__content { align-items: stretch; flex-wrap: wrap; } .audio-guide audio { width: 100%; margin-left: 0; } }
  `
  document.head.append(style)

  const render = () => {
    const quick = document.querySelector('.quick')
    if (!quick || document.querySelector('.audio-guide')) return
    const completed = localStorage.getItem(completedKey) === 'true'
    const card = document.createElement('section')
    card.className = `audio-guide${completed ? ' is-complete' : ''}`
    card.innerHTML = `
      <div class="audio-guide__top">
        <h2>◉ АУДИОМЕТОДИЧКА</h2>
        <span class="audio-guide__status">Урок 1 из 1 · 10 сек.</span>
      </div>
      <div class="audio-guide__content">
        <span class="audio-guide__number">1</span>
        <div><p>Проверка русской озвучки</p><small>Прослушайте фрагмент. После этого отметьте урок как пройденный.</small></div>
        <audio controls preload="metadata" src="/audio/cosyvoice-ru-test.mp3" aria-label="Русская озвучка методички"></audio>
        <button class="audio-guide__complete" type="button">${completed ? '✓ Прослушано' : 'Отметить'}</button>
      </div>`
    quick.before(card)
    card.querySelector('button').addEventListener('click', () => {
      localStorage.setItem(completedKey, 'true')
      card.classList.add('is-complete')
      card.querySelector('button').textContent = '✓ Прослушано'
    })
  }
  new MutationObserver(render).observe(document.documentElement, { childList: true, subtree: true })
  render()
})()

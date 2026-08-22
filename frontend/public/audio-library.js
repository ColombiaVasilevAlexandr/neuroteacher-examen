(() => {
  const lessons = [
    { id: 'geography', number: '01', title: 'География Колумбии', topic: 'География', file: 'lesson-01-geography-full.mp3' },
    { id: 'history', number: '02', title: 'История Колумбии', topic: 'История', file: 'lesson-02-history-full.mp3' },
    { id: 'constitution', number: '03', title: 'Конституция и государство', topic: 'Конституция', file: 'lesson-03-constitution-full.mp3' },
    { id: 'spanish', number: '04', title: 'Испанский язык', topic: 'Испанский', file: 'lesson-04-spanish-full.mp3' },
    { id: 'culture', number: '05', title: 'Культура Колумбии', topic: 'Культура', file: 'lesson-05-culture-full.mp3' },
    { id: 'naturalization', number: '06', title: 'Натурализация', topic: 'Натурализация', file: 'lesson-06-naturalization-full.mp3' },
  ]

  const stateKey = 'colombia-exam-audio-library'
  const loadState = () => {
    try {
      return JSON.parse(localStorage.getItem(stateKey) || '{}')
    } catch {
      return {}
    }
  }
  const saveState = (state) => localStorage.setItem(stateKey, JSON.stringify(state))
  const formatTime = (seconds) => {
    if (!Number.isFinite(seconds) || seconds < 1) return '0:00'
    const total = Math.floor(seconds)
    const minutes = Math.floor(total / 60)
    const rest = String(total % 60).padStart(2, '0')
    return `${minutes}:${rest}`
  }

  const css = document.createElement('style')
  css.textContent = `
    .audio-library{border:1px solid #3f5968;background:linear-gradient(135deg,#101b25,#071017);border-radius:18px;margin:0 0 18px;padding:22px;color:#eef7fb;box-shadow:0 12px 30px #0005}
    .audio-library-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px}
    .audio-library h2{margin:0;font-size:20px;letter-spacing:.03em}
    .audio-library p{color:#aebdc8;margin:6px 0 0;font-size:13px;line-height:1.4}
    .audio-library-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
    .audio-library button{border:0;border-radius:9px;background:#38e0d0;color:#061214;padding:10px 12px;font-weight:800}
    .audio-library button.secondary{background:#112631;color:#dff6f6;border:1px solid #395866}
    .audio-player{display:grid;grid-template-columns:1fr;gap:10px;background:#07151c;border:1px solid #223845;border-radius:13px;margin:16px 0;padding:14px}
    .audio-player strong{font-size:15px}
    .audio-player small{color:#9db1bd}
    .audio-player audio{width:100%}
    .audio-progress-line{height:6px;background:#102734;border-radius:999px;overflow:hidden}
    .audio-progress-line i{display:block;height:100%;width:0;background:#ffd12a}
    .audio-lessons{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
    .audio-lesson{border:1px solid #263b48;background:#0b1720;border-radius:11px;padding:12px;text-align:left}
    .audio-lesson b{display:block;color:#fff;font-size:14px}
    .audio-lesson span{display:block;color:#8fa4b0;font-size:12px;margin-top:4px}
    .audio-lesson mark{display:inline-block;margin-top:9px;background:#162f3d;color:#38e0d0;border-radius:999px;padding:5px 8px;font-size:11px}
    @media(max-width:760px){.audio-library-head{display:grid}.audio-library-actions{justify-content:flex-start}.audio-lessons{grid-template-columns:1fr}}
  `
  document.head.append(css)

  let currentIndex = 0
  let playAll = false
  let audio

  window.ColombiaAudioLibrary = window.ColombiaAudioLibrary || {}
  window.ColombiaAudioLibrary.playLessonByTopic = (topic) => {
    const index = lessons.findIndex((lesson) => lesson.topic === topic || lesson.id === topic)
    if (index < 0) return false
    currentIndex = index
    playAll = false
    const next = loadState()
    next.currentIndex = currentIndex
    saveState(next)
    render()
    document.querySelector('.audio-library audio')?.play().catch(() => undefined)
    document.querySelector('.audio-library')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    return true
  }

  function render() {
    const target = document.querySelector('.content') || document.querySelector('.app-shell') || document.body
    let card = document.querySelector('.audio-library')
    if (!card) {
      card = document.createElement('section')
      card.className = 'audio-library'
      const plan = document.querySelector('.study-plan-card')
      if (plan && plan.parentElement) plan.after(card)
      else target.prepend(card)
    }

    const state = loadState()
    currentIndex = Number.isInteger(state.currentIndex) ? Math.min(Math.max(state.currentIndex, 0), lessons.length - 1) : currentIndex
    const current = lessons[currentIndex]
    const currentPosition = state.positions?.[current.id] || 0

    card.innerHTML = `
      <div class="audio-library-head">
        <div>
          <h2>Аудиотека методички</h2>
          <p>Слушайте всю методичку подряд или отдельные модули. Позиция сохраняется в этом браузере.</p>
        </div>
        <div class="audio-library-actions">
          <button class="continue">Слушать дальше</button>
          <button class="pause secondary">Пауза</button>
          <button class="stop secondary">Стоп</button>
          <button class="all secondary">Вся методичка</button>
        </div>
      </div>
      <div class="audio-player">
        <strong>${current.number}. ${current.title}</strong>
        <small>${current.topic} · сохранено: ${formatTime(currentPosition)}</small>
        <audio controls preload="metadata" src="/audio/${current.file}"></audio>
        <div class="audio-progress-line"><i></i></div>
      </div>
      <div class="audio-lessons">
        ${lessons.map((lesson, index) => {
          const position = state.positions?.[lesson.id] || 0
          return `<button class="audio-lesson" data-index="${index}"><b>${lesson.number}. ${lesson.title}</b><span>${lesson.topic}</span><mark>${position ? `с ${formatTime(position)}` : 'начать'}</mark></button>`
        }).join('')}
      </div>
    `

    audio = card.querySelector('audio')
    const bar = card.querySelector('.audio-progress-line i')

    function persist() {
      const next = loadState()
      next.currentIndex = currentIndex
      next.positions = next.positions || {}
      if (audio.currentTime > 0) next.positions[current.id] = Math.floor(audio.currentTime)
      saveState(next)
    }

    audio.addEventListener('loadedmetadata', () => {
      if (currentPosition > 0 && currentPosition < audio.duration - 3) audio.currentTime = currentPosition
    })
    audio.addEventListener('timeupdate', () => {
      if (audio.duration) bar.style.width = `${Math.min(100, (audio.currentTime / audio.duration) * 100)}%`
      if (Math.floor(audio.currentTime) % 5 === 0) persist()
    })
    audio.addEventListener('pause', () => {
      playAll = false
      persist()
    })
    audio.addEventListener('ended', () => {
      const next = loadState()
      next.positions = next.positions || {}
      next.positions[current.id] = 0
      saveState(next)
      if (playAll && currentIndex < lessons.length - 1) {
        currentIndex += 1
        render()
        const nextAudio = document.querySelector('.audio-library audio')
        nextAudio?.play().catch(() => undefined)
      }
    })

    card.querySelector('.continue').onclick = () => {
      playAll = false
      audio.play().catch(() => undefined)
    }
    card.querySelector('.pause').onclick = () => {
      playAll = false
      audio.pause()
      persist()
    }
    card.querySelector('.stop').onclick = () => {
      playAll = false
      audio.pause()
      audio.currentTime = 0
      const next = loadState()
      next.currentIndex = currentIndex
      next.positions = next.positions || {}
      next.positions[current.id] = 0
      saveState(next)
      bar.style.width = '0'
    }
    card.querySelector('.all').onclick = () => {
      playAll = true
      audio.play().catch(() => undefined)
    }
    card.querySelectorAll('[data-index]').forEach((button) => {
      button.onclick = () => {
        currentIndex = Number(button.dataset.index)
        playAll = false
        const next = loadState()
        next.currentIndex = currentIndex
        saveState(next)
        render()
        document.querySelector('.audio-library audio')?.play().catch(() => undefined)
      }
    })
  }

  const observer = new MutationObserver(() => {
    if (document.querySelector('.content') && !document.querySelector('.audio-library')) render()
  })
  observer.observe(document.documentElement, { childList: true, subtree: true })
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render)
  else render()
})()

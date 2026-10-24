(() => {
  const L=window.ColombiaLocales, ui=(key,values)=>L.escape(L.ui(key,values))
  const text = new Proxy({}, {get:(_,key)=>L.ui({title:'audioTitle',intro:'audioIntro',continue:'audioContinue',pause:'audioPause',stop:'audioStop',playAll:'audioAll',otherModules:'audioOther',fromStart:'audioFromStart',start:'audioStart',ready:'audioReady',loading:'audioLoading',playing:'audioPlaying',blocked:'audioBlocked'}[key])})

  const lessons = [
    { id: 'geography', number: '01', title: '\u0413\u0435\u043e\u0433\u0440\u0430\u0444\u0438\u044f \u041a\u043e\u043b\u0443\u043c\u0431\u0438\u0438', topic: '\u0413\u0435\u043e\u0433\u0440\u0430\u0444\u0438\u044f', file: 'lesson-01-geography-full.mp3' },
    { id: 'history', number: '02', title: '\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u041a\u043e\u043b\u0443\u043c\u0431\u0438\u0438', topic: '\u0418\u0441\u0442\u043e\u0440\u0438\u044f', file: 'lesson-02-history-full.mp3' },
    { id: 'constitution', number: '03', title: '\u041a\u043e\u043d\u0441\u0442\u0438\u0442\u0443\u0446\u0438\u044f \u0438 \u0433\u043e\u0441\u0443\u0434\u0430\u0440\u0441\u0442\u0432\u043e', topic: '\u041a\u043e\u043d\u0441\u0442\u0438\u0442\u0443\u0446\u0438\u044f', file: 'lesson-03-constitution-full.mp3' },
    { id: 'spanish', number: '04', title: '\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439 \u044f\u0437\u044b\u043a', topic: '\u0418\u0441\u043f\u0430\u043d\u0441\u043a\u0438\u0439', file: 'lesson-04-spanish-full.mp3' },
    { id: 'culture', number: '05', title: '\u041a\u0443\u043b\u044c\u0442\u0443\u0440\u0430 \u041a\u043e\u043b\u0443\u043c\u0431\u0438\u0438', topic: '\u041a\u0443\u043b\u044c\u0442\u0443\u0440\u0430', file: 'lesson-05-culture-full.mp3' },
    { id: 'naturalization', number: '06', title: '\u041d\u0430\u0442\u0443\u0440\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f', topic: '\u041d\u0430\u0442\u0443\u0440\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f', file: 'lesson-06-naturalization-full.mp3' },
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
    .audio-player audio{width:100%}
    .audio-current-meta{display:flex;gap:8px;flex-wrap:wrap;color:#9db1bd;font-size:12px}
    .audio-current-meta span{border:1px solid #223845;background:#0b1b24;border-radius:999px;padding:5px 8px}
    .audio-status{min-height:18px;color:#9db1bd;font-size:12px}
    .audio-status.warn{color:#ffd12a}
    .audio-progress-line{height:6px;background:#102734;border-radius:999px;overflow:hidden}
    .audio-progress-line i{display:block;height:100%;width:0;background:#ffd12a}
    .audio-lessons-title{margin:16px 0 8px;color:#cfe4e8;font-size:13px;font-weight:800}
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
    document.querySelector('.audio-library .continue')?.click()
    document.querySelector('.audio-library')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    return true
  }

  function render(autoplay = false) {
    const continuous = playAll
    if (audio) audio.pause()
    playAll = continuous
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
    const lessonButtons = lessons
      .map((lesson, index) => {
        if (index === currentIndex) return ''
        const position = state.positions?.[lesson.id] || 0
        const label = position ? ui('audioListenFrom',{time:formatTime(position)}) : text.start
        return `<button class="audio-lesson" data-index="${index}"><b>${lesson.number}. ${ui(lesson.id+'Title')}</b><span>${L.escape(L.text(lesson.topic))}</span><mark>${label}</mark></button>`
      })
      .join('')

    card.innerHTML = `
      <div class="audio-library-head">
        <div>
          <h2>${text.title}</h2>
          <p>${text.intro}</p>
        </div>
        <div class="audio-library-actions">
          <button class="continue">${text.continue}</button>
          <button class="pause secondary">${text.pause}</button>
          <button class="stop secondary">${text.stop}</button>
          <button class="all secondary">${text.playAll}</button>
        </div>
      </div>
      <div class="audio-player">
        <strong>${current.number}. ${ui(current.id+'Title')}</strong>
        <div class="audio-current-meta">
          <span>${L.escape(L.text(current.topic))}</span>
          <span>${currentPosition ? ui('audioSaved',{time:formatTime(currentPosition)}) : text.fromStart}</span>
        </div>
        <audio controls preload="metadata" src="/audio/${current.file}" data-current-id="${current.id}"></audio>
        <div class="audio-status" data-ui-status="ready">${text.ready}</div>
        <div class="audio-progress-line"><i></i></div>
      </div>
      <div class="audio-lessons-title">${text.otherModules}</div>
      <div class="audio-lessons">${lessonButtons}</div>
    `

    const player = card.querySelector('audio')
    audio = player
    const bar = card.querySelector('.audio-progress-line i')
    const status = card.querySelector('.audio-status')

    function setStatus(key, warning = false) {
      status.dataset.uiStatus=key
      status.textContent = text[key]
      status.classList.toggle('warn', warning)
    }

    async function playCurrent() {
      setStatus('loading')
      try {
        await player.play()
        setStatus('playing')
      } catch {
        setStatus('blocked', true)
      }
    }

    function persist() {
      const next = loadState()
      next.positions = next.positions || {}
      if (player.currentTime > 0) next.positions[current.id] = Math.floor(player.currentTime)
      saveState(next)
    }

    player.addEventListener('loadedmetadata', () => {
      if (currentPosition > 0 && currentPosition < player.duration - 3) player.currentTime = currentPosition
      setStatus('ready')
    })
    player.addEventListener('timeupdate', () => {
      if (player.duration) bar.style.width = `${Math.min(100, (player.currentTime / player.duration) * 100)}%`
      if (Math.floor(player.currentTime) % 5 === 0) persist()
    })
    player.addEventListener('pause', () => {
      if (!player.ended) playAll = false
      persist()
    })
    player.addEventListener('ended', () => {
      const next = loadState()
      next.positions = next.positions || {}
      next.positions[current.id] = 0
      saveState(next)
      if (playAll && currentIndex < lessons.length - 1) {
        currentIndex += 1
        next.currentIndex = currentIndex
        saveState(next)
        render(true)
      }
    })

    card.querySelector('.continue').onclick = () => {
      playAll = false
      playCurrent()
    }
    card.querySelector('.pause').onclick = () => {
      playAll = false
      player.pause()
      persist()
    }
    card.querySelector('.stop').onclick = () => {
      playAll = false
      player.pause()
      player.currentTime = 0
      const next = loadState()
      next.currentIndex = currentIndex
      next.positions = next.positions || {}
      next.positions[current.id] = 0
      saveState(next)
      bar.style.width = '0'
    }
    card.querySelector('.all').onclick = () => {
      playAll = true
      playCurrent()
    }
    card.querySelectorAll('[data-index]').forEach((button) => {
      button.onclick = () => {
        currentIndex = Number(button.dataset.index)
        playAll = false
        const next = loadState()
        next.currentIndex = currentIndex
        saveState(next)
        render()
        const nextCard = document.querySelector('.audio-library')
        nextCard?.querySelector('.continue')?.click()
      }
    })
    if (autoplay) playCurrent()
  }

  window.addEventListener('colombia:locale-changed', () => {
    const card=document.querySelector('.audio-library'); if(!card)return
    const state=loadState(), current=lessons[currentIndex], position=state.positions?.[current.id]||0
    const labels={'.audio-library-head h2':text.title,'.audio-library-head p':text.intro,'.continue':text.continue,'.pause':text.pause,'.stop':text.stop,'.all':text.playAll,'.audio-lessons-title':text.otherModules,'.audio-player strong':current.number+'. '+L.ui(current.id+'Title')}
    Object.entries(labels).forEach(([selector,value])=>{card.querySelector(selector).textContent=value})
    const meta=card.querySelectorAll('.audio-current-meta span');meta[0].textContent=L.text(current.topic);meta[1].textContent=position?L.ui('audioSaved',{time:formatTime(position)}):text.fromStart
    const status=card.querySelector('.audio-status');status.textContent=text[status.dataset.uiStatus||'ready']
    card.querySelectorAll('[data-index]').forEach(button=>{const lesson=lessons[Number(button.dataset.index)],pos=state.positions?.[lesson.id]||0;button.querySelector('b').textContent=lesson.number+'. '+L.ui(lesson.id+'Title');button.querySelector('span').textContent=L.text(lesson.topic);button.querySelector('mark').textContent=pos?L.ui('audioListenFrom',{time:formatTime(pos)}):text.start})
  })

  window.addEventListener('pagehide', () => audio?.pause())

  const observer = new MutationObserver(() => {
    if (document.querySelector('.content') && !document.querySelector('.audio-library')) render()
  })
  observer.observe(document.documentElement, { childList: true, subtree: true })
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => render())
  else render()
})()

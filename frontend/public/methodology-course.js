(() => {
  const style = document.createElement('style')
  style.textContent = `
    .methodology-course { border: 1px solid #4a5b67; background: linear-gradient(135deg, #121f29, #0b1117); border-radius: 20px; margin-top: 18px; padding: 22px; }
    .methodology-course h2 { letter-spacing: .05em; margin: 0; font-size: 17px; }
    .methodology-course > p { color: #aebdc8; margin: 8px 0 17px; font-size: 13px; }
    .methodology-course__list { gap: 10px; display: grid; }
    .methodology-course__lesson { border: 1px solid #31414d; background: #0b151d; border-radius: 12px; align-items: center; gap: 14px; padding: 13px; display: flex; }
    .methodology-course__lesson b { color: #ffd12a; min-width: 28px; }
    .methodology-course__lesson div { flex: 1; }
    .methodology-course__lesson div strong, .methodology-course__lesson div small { display: block; }
    .methodology-course__lesson small { color: #8fa2b0; margin-top: 3px; }
    .methodology-course__lesson audio { width: min(300px, 100%); }
    .methodology-course__start { color: #091116; background: #ffd12a; border: 0; border-radius: 8px; padding: 9px 11px; white-space: nowrap; font-size: 12px; font-weight: 700; }
    .methodology-course__start:disabled { cursor: not-allowed; opacity: .45; }
    @media (max-width: 650px) { .methodology-course__lesson { align-items: stretch; flex-wrap: wrap; } .methodology-course__lesson audio { width: 100%; } }
  `
  document.head.append(style)

  const render = () => {
    const guide = document.querySelector('.audio-guide')
    if (!guide || document.querySelector('.methodology-course')) return
    const course = document.createElement('section')
    course.className = 'methodology-course'
    course.innerHTML = `
      <h2>КУРС ПО ОФИЦИАЛЬНОЙ МЕТОДИЧКЕ</h2>
      <p>Источник: «Colombia, nuestra casa». Уроки строятся по разделам методички и ведут к тренировке.</p>
      <div class="methodology-course__list">
        <article class="methodology-course__lesson"><b>01</b><div><strong>География Колумбии</strong><small>Территория, население, регионы и природа · 18 сек.</small></div><audio controls preload="metadata" src="/audio/lesson-01-geography.mp3" aria-label="Урок География Колумбии"></audio><button class="methodology-course__start" data-topic="География">Тренировка</button></article>
        <article class="methodology-course__lesson"><b>02</b><div><strong>История Колумбии</strong><small>Хронология от первых поселений до современности</small></div><audio controls preload="metadata" src="/audio/lesson-02-history.mp3" aria-label="Урок История Колумбии"></audio><button class="methodology-course__start" data-topic="История">Тренировка</button></article>
        <article class="methodology-course__lesson"><b>03</b><div><strong>Конституция и государство</strong><small>Устройство страны и основы гражданства</small></div><audio controls preload="metadata" src="/audio/lesson-03-constitution.mp3" aria-label="Урок Конституция и государство"></audio><button class="methodology-course__start" data-topic="Конституция">Тренировка</button></article>
        <article class="methodology-course__lesson"><b>04</b><div><strong>Испанский язык</strong><small>Алфавит, словарь и базовая грамматика</small></div><audio controls preload="metadata" src="/audio/lesson-04-spanish.mp3" aria-label="Урок Испанский язык"></audio><button class="methodology-course__start" data-topic="Испанский язык">Тренировка</button></article>
        <article class="methodology-course__lesson"><b>05</b><div><strong>Культура Колумбии</strong><small>Символы страны, традиции и ключевые культурные факты</small></div><audio controls preload="metadata" src="/audio/lesson-05-culture.mp3" aria-label="Урок Культура Колумбии"></audio><button class="methodology-course__start" data-topic="Культура">Тренировка</button></article>
        <article class="methodology-course__lesson"><b>06</b><div><strong>Натурализация</strong><small>Документы, сроки и порядок подачи</small></div><audio controls preload="metadata" src="/audio/lesson-06-naturalization.mp3" aria-label="Урок Натурализация"></audio><button class="methodology-course__start" data-topic="Натурализация">Тренировка</button></article>
      </div>`
    guide.after(course)
    course.querySelectorAll('.methodology-course__lesson').forEach((lesson, index) => {
      const audio = lesson.querySelector('audio')
      const button = lesson.querySelector('.methodology-course__start')
      const key = `colombia-exam-methodology-lesson-${index + 1}`
      const unlock = () => {
        localStorage.setItem(key, 'complete')
        button.disabled = false
        button.textContent = 'К тренировке'
      }
      if (localStorage.getItem(key) === 'complete') unlock()
      else {
        button.disabled = true
        button.textContent = 'Прослушайте блок'
        audio.addEventListener('ended', unlock, { once: true })
      }
    })
    course.querySelectorAll('.methodology-course__start').forEach(button => button.addEventListener('click', () => {
      const topic = button.dataset.topic
      const topicButton = [...document.querySelectorAll('.plan-item')].find(item => item.textContent.includes(topic))
      if (topicButton) topicButton.click()
      else [...document.querySelectorAll('nav button')].find(item => item.textContent.includes('Тренировка'))?.click()
    }))
  }
  new MutationObserver(render).observe(document.documentElement, { childList: true, subtree: true })
  render()
})()

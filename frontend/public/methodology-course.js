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
    .methodology-course__lesson.is-locked { opacity: .58; }
    .methodology-course__lesson em { color: #91a4b2; font-size: 12px; font-style: normal; }
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
        <article class="methodology-course__lesson"><b>01</b><div><strong>География Колумбии</strong><small>Территория, население, регионы и природа · 18 сек.</small></div><audio controls preload="metadata" src="/audio/lesson-01-geography.mp3" aria-label="Урок География Колумбии"></audio></article>
        <article class="methodology-course__lesson is-locked"><b>02</b><div><strong>История Колумбии</strong><small>Хронология от первых поселений до современности</small></div><em>Готовится</em></article>
        <article class="methodology-course__lesson is-locked"><b>03</b><div><strong>Конституция и государство</strong><small>Устройство страны и основы гражданства</small></div><em>Готовится</em></article>
        <article class="methodology-course__lesson is-locked"><b>04</b><div><strong>Испанский язык</strong><small>Алфавит, словарь и базовая грамматика</small></div><em>Готовится</em></article>
      </div>`
    guide.after(course)
  }
  new MutationObserver(render).observe(document.documentElement, { childList: true, subtree: true })
  render()
})()

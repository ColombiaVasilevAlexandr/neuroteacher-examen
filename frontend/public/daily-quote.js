(() => {
  const quotes = [
    ['Образование — самое мощное оружие, которым можно изменить мир.', 'Нельсон Мандела'],
    ['Тот, кто знает языки, может чувствовать себя дома везде.', 'Иоганн Вольфганг Гёте'],
    ['Маленький ежедневный прогресс со временем даёт большие результаты.', 'Неизвестный автор'],
    ['Учиться — значит открывать для себя, что ты уже знаешь.', 'Ричард Бах'],
    ['Успех — это сумма небольших усилий, повторяемых изо дня в день.', 'Роберт Кольер'],
    ['Не бойтесь делать ошибки: они помогают говорить лучше.', 'Учебный принцип'],
    ['Знание открывает двери, которые прежде казались закрытыми.', 'Народная мудрость'],
  ]
  const apply = () => {
    const card = document.querySelector('.quote')
    if (!card || card.dataset.dailyQuote) return
    const today = new Date(); const index = Math.floor(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()) / 86400000) % quotes.length
    const [text, author] = quotes[index]
    card.dataset.dailyQuote = 'true'
    card.innerHTML = `<b>ФРАЗА ДНЯ</b><p>${text}</p><small>— ${author}</small><i>“</i>`
  }
  apply(); new MutationObserver(apply).observe(document.documentElement, {childList:true,subtree:true})
})()

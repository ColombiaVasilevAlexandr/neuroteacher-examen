(() => {
  const apply = () => {
    const page = [...document.querySelectorAll('main.training')].find(item => item.textContent.includes('Интервальное повторение'))
    if (!page || page.querySelector('.repeat-empty-state')) return
    const heading = [...page.querySelectorAll('h1')].find(item => item.textContent.includes('Интервальное повторение'))
    if (!heading || page.querySelector('.question-card')) return
    const card = document.createElement('section')
    card.className = 'repeat-empty-state'
    card.innerHTML = '<div class="repeat-empty-state__mark">✓</div><h2>Сегодня повторений нет</h2><p>Вы уже разобрали все вопросы, назначенные на сегодня. Новые ошибки и отмеченные вопросы появятся здесь автоматически.</p><button>Начать тренировку</button>'
    card.querySelector('button').onclick = () => {
      const training = [...document.querySelectorAll('button')].find(button => button.textContent.includes('Тренировка'))
      if (training) training.click()
    }
    heading.parentElement.insertAdjacentElement('afterend', card)
  }
  apply(); new MutationObserver(apply).observe(document.documentElement, {childList:true,subtree:true})
})()

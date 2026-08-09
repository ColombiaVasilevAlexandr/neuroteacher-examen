(() => {
  const apply = () => {
    const footer = document.querySelector('.app-shell footer')
    if (footer && !footer.querySelector('.official-source-note')) {
      const note = document.createElement('small'); note.className='official-source-note'
      note.textContent='Материалы: Colombia, nuestra casa · официальный учебный источник Cancillería de Colombia.'
      footer.append(note)
    }
    document.querySelectorAll('.feedback').forEach(feedback => {
      if (feedback.querySelector('.review-rule-note')) return
      const note = document.createElement('small'); note.className='review-rule-note'
      note.textContent='Этот вопрос автоматически будет назначен на повторение по интервальному расписанию.'
      feedback.append(note)
    })
  }
  apply(); new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true})
})()

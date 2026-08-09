(() => {
  const apply = count => {
    const button = [...document.querySelectorAll('.nav')].find(item => /Повторение|Repaso/.test(item.textContent))
    if (!button || button.querySelector('.review-badge') || !count) return
    const badge = document.createElement('em'); badge.className='review-badge'; badge.textContent=count > 9 ? '9+' : count
    button.append(badge)
  }
  fetch('http://127.0.0.1:8000/api/dashboard').then(r=>r.ok?r.json():Promise.reject()).then(data=>{
    apply(data.due_reviews || 0); new MutationObserver(()=>apply(data.due_reviews || 0)).observe(document.documentElement,{childList:true,subtree:true})
  }).catch(()=>undefined)
})()

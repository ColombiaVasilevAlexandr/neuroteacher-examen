(() => {
  const apply = count => {
    const button = [...document.querySelectorAll('.nav')].find(item => /Повторение|Repaso/.test(item.textContent))
    if (!button) return
    const existing = button.querySelector('.review-badge')
    if (!count) { existing?.remove(); return }
    const label = count > 9 ? '9+' : String(count)
    if (existing) {
      if (existing.textContent !== label) existing.textContent = label
      return
    }
    const badge = document.createElement('em'); badge.className='review-badge'; badge.textContent=label
    button.append(badge)
  }
  let latest = 0
  const refresh = () => fetch('http://127.0.0.1:8000/api/dashboard').then(r=>r.ok?r.json():Promise.reject()).then(data=>{ latest=data.due_reviews || 0; apply(latest) }).catch(()=>undefined)
  refresh(); new MutationObserver(()=>apply(latest)).observe(document.documentElement,{childList:true,subtree:true}); window.addEventListener('reviews:updated',refresh); window.addEventListener('focus',refresh)
})()

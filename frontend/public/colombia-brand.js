(() => {
  const apply = () => {
    const brand = document.querySelector('.sidebar .brand')
    if (!brand || brand.dataset.colombiaBrand) return
    brand.dataset.colombiaBrand = 'true'
    brand.innerHTML = '<span class="colombia-flag" aria-label="Флаг Колумбии"><i></i><i></i><i></i></span><b>EXAMEN<br>DE COLOMBIA</b>'
  }
  apply(); new MutationObserver(apply).observe(document.documentElement, {childList:true,subtree:true})
})()

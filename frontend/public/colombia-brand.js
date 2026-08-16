(() => {
  const apply = () => {
    const brand = document.querySelector('.sidebar .brand')
    if (!brand || brand.dataset.colombiaBrand) return
    brand.dataset.colombiaBrand = 'true'
    brand.innerHTML = '<span class="colombia-flag" aria-label="Флаг Колумбии"><i></i><i></i><i></i></span><b>КОЛУМБИЯ<br>ЭКЗАМЕН</b>'
  }
  apply()
  const label = document.querySelector('.sidebar .brand b')
  if (label) label.innerHTML = '\u041a\u041e\u041b\u0423\u041c\u0411\u0418\u042f<br>\u042d\u041a\u0417\u0410\u041c\u0415\u041d'
  new MutationObserver(apply).observe(document.documentElement, { childList: true, subtree: true })
})()

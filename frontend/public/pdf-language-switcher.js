(() => {
  const L=window.ColombiaLocales;
  const paths={ru:'colombia_nuestra_casa_ru.pdf',es:'colombia_nuestra_casa.pdf'};
  const label=source=>L.ui(source==='ru'?'pdfRussian':'pdfSpanish');
  const addSwitch=link=>{
    if(link.dataset.pdfLanguageReady)return;
    link.dataset.pdfLanguageReady='true';
    const page=link.getAttribute('href').match(/#page=\d+/)?.[0]??'';
    const switcher=document.createElement('span');switcher.className='pdf-language-switcher';
    switcher.innerHTML='<button type="button" data-pdf="ru">RU PDF</button><button type="button" data-pdf="es">ES PDF</button>';
    const setSource=source=>{
      link.dataset.pdfSource=source;link.href=`/${paths[source]}${page}`;link.textContent=label(source);
      switcher.title=L.ui('pdfLanguages');
      switcher.querySelectorAll('button').forEach(button=>button.classList.toggle('selected',button.dataset.pdf===source));
    };
    switcher.addEventListener('click',event=>{const button=event.target.closest('button[data-pdf]');if(button)setSource(button.dataset.pdf);});
    link.insertAdjacentElement('afterend',switcher);setSource(L.current==='ru'?'ru':'es');
  };
  const apply=()=>document.querySelectorAll('a.language-mark[href*="colombia_nuestra_casa"]').forEach(addSwitch);
  window.addEventListener('colombia:locale-changed',()=>{
    document.querySelectorAll('a[data-pdf-source]').forEach(link=>{link.textContent=label(link.dataset.pdfSource);link.nextElementSibling.title=L.ui('pdfLanguages');});
  });
  apply();new MutationObserver(apply).observe(document.documentElement,{childList:true,subtree:true});
})();

(() => {
  const L=window.ColombiaLocales;
  const style=document.createElement('style');
  style.textContent=`.streak.has-calendar-history>.week{display:none}.calendar-history{display:flex;gap:8px;overflow-x:auto;padding:6px 2px 10px;scrollbar-width:thin}.calendar-history>div{flex:0 0 60px;text-align:center}.calendar-history b{display:block;font-size:11px}.calendar-history i{display:block;font-style:normal;color:#334357}.calendar-history [data-has-activity=true] i{color:#55e980}.calendar-history .current{border-bottom:2px solid #38e0d0}`;
  document.head.append(style);
  let cached=null,busy=false;
  const render=async()=>{
    const parent=document.querySelector('.streak');if(!parent||busy)return;
    let history=parent.querySelector('.calendar-history');
    if(history?.dataset.historyLoaded===L.current)return;
    busy=true;
    try{
      if(!cached){const response=await fetch(window.COLOMBIA_API_BASE+'/dashboard');if(!response.ok)throw new Error('Dashboard unavailable');cached=await response.json();}
      if(!Array.isArray(cached.calendar))return;
      if(!parent.isConnected)return;
      if(!history){history=document.createElement('div');history.className='calendar-history';parent.append(history);}
      history.dataset.historyLoaded=L.current;
      history.replaceChildren(...cached.calendar.map(({date,attempts},index)=>{
        const item=document.createElement('div');if(index===cached.calendar.length-1)item.className='current';
        item.dataset.hasActivity=String(attempts>0);
        const label=document.createElement('b');label.textContent=new Intl.DateTimeFormat(L.dateLocale,{day:'numeric',month:'short'}).format(new Date(date+'T12:00:00'));
        const mark=document.createElement('i');mark.title=L.ui('sessions',{count:attempts});mark.textContent=attempts>0?'✓':'·';
        item.append(label,mark);return item;
      }));
      parent.classList.add('has-calendar-history');
    }catch{ /* Keep the original five-day view if the API is unavailable. */ }
    finally{busy=false;}
  };
  window.addEventListener('colombia:locale-changed',render);
  window.addEventListener('reviews:updated',()=>{cached=null;const history=document.querySelector('.calendar-history');if(history)delete history.dataset.historyLoaded;render();});
  new MutationObserver(render).observe(document.documentElement,{childList:true,subtree:true});render();
})();

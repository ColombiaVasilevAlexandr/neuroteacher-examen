(() => {
  const originalFetch=window.fetch.bind(window)
  const ready=originalFetch(window.COLOMBIA_API_BASE+'/session',{credentials:'same-origin'}).then(response=>{
    if(!response.ok)throw new Error('Could not initialize private study progress')
  })
  window.fetch=(input,init)=>ready.then(()=>originalFetch(input,init))
})()

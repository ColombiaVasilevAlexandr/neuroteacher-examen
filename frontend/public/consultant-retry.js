(() => {
  const originalFetch = window.fetch.bind(window)
  window.fetch = async (...args) => {
    const url = String(args[0] instanceof Request ? args[0].url : args[0])
    if (!url.includes('/api/ai/chat')) return originalFetch(...args)
    let lastError
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        const response = await originalFetch(...args)
        if (response.ok || response.status < 500) return response
        lastError = response
      } catch (error) {
        lastError = error
      }
      await new Promise(resolve => setTimeout(resolve, 700 * (attempt + 1)))
    }
    if (lastError instanceof Response) return lastError
    throw lastError
  }
})()

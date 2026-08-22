(() => {
  const explicitBase = window.COLOMBIA_API_BASE
  const localHosts = new Set(['127.0.0.1', 'localhost', '[::1]', '::1'])
  const normalized = (value) => String(value || '').replace(/\/$/, '')
  const defaultBase = () => {
    if (explicitBase) return normalized(explicitBase)
    if (localHosts.has(window.location.hostname)) return 'http://127.0.0.1:8000/api'
    if (window.location.port === '5173') return `${window.location.protocol}//${window.location.hostname}:8000/api`
    return `${window.location.origin}/api`
  }
  const apiBase = defaultBase()
  const apiPattern = /^https?:\/\/(?:127\.0\.0\.1|localhost):8000\/api/

  window.COLOMBIA_API_BASE = apiBase
  window.ColombiaRuntime = Object.assign(window.ColombiaRuntime || {}, { apiBase })

  const rewriteUrl = (url) => {
    const value = String(url)
    return apiPattern.test(value) ? value.replace(apiPattern, apiBase) : value
  }

  const originalFetch = window.fetch ? window.fetch.bind(window) : null
  if (originalFetch) {
    window.fetch = (input, init) => {
      if (typeof input === 'string' || input instanceof URL) {
        return originalFetch(rewriteUrl(input), init)
      }
      if (typeof Request !== 'undefined' && input instanceof Request) {
        const nextUrl = rewriteUrl(input.url)
        return originalFetch(nextUrl === input.url ? input : new Request(nextUrl, input), init)
      }
      return originalFetch(input, init)
    }
  }

  const originalOpen = window.XMLHttpRequest && window.XMLHttpRequest.prototype.open
  if (originalOpen) {
    window.XMLHttpRequest.prototype.open = function open(method, url, ...rest) {
      return originalOpen.call(this, method, rewriteUrl(url), ...rest)
    }
  }
})()

(() => {
  const staleSelectors = [
    '.spanish-access',
    '.methodology-course',
    '.audio-guide',
    '.audio-mini-test',
    '.spanish-lab',
    '.spanish-path',
    '.spanish-progress',
    '.spanish-lab-launch',
    '.spanish-path-launch',
    '.spanish-progress-launch',
    '.spanish-hub-links',
  ]

  const cleanup = () => {
    staleSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(element => element.remove())
    })
  }

  cleanup()
  window.addEventListener('pageshow', cleanup)
  setTimeout(cleanup, 250)
  setTimeout(cleanup, 1000)
})()

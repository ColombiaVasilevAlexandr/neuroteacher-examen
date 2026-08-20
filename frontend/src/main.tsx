const root = document.getElementById('root')
let startupErrorShown = false

function describeError(error: unknown): string {
  if (error instanceof Error) {
    return `${error.name}: ${error.message}\n${error.stack ?? ''}`.trim()
  }
  return String(error ?? 'Unknown startup error')
}

function showStartupError(error: unknown) {
  if (startupErrorShown) return
  startupErrorShown = true

  const details = describeError(error)
  console.error('Colombia Exam frontend failed to start:', error)

  if (!root) return
  root.replaceChildren()

  const panel = document.createElement('main')
  panel.setAttribute('role', 'alert')
  panel.style.cssText = [
    'min-height:100vh',
    'display:grid',
    'place-items:center',
    'padding:24px',
    'background:#06101d',
    'color:#eef4ff',
    'font-family:Arial,sans-serif',
  ].join(';')

  const card = document.createElement('section')
  card.style.cssText = [
    'width:min(760px,100%)',
    'background:#0b1a2b',
    'border:1px solid #ff5360',
    'border-radius:14px',
    'padding:24px',
    'box-shadow:0 18px 50px #0008',
  ].join(';')

  const title = document.createElement('h1')
  title.textContent = 'Не удалось запустить COLOMBIA EXAM'
  title.style.margin = '0 0 12px'

  const message = document.createElement('p')
  message.textContent = 'Интерфейс упал при загрузке. Чёрного экрана больше не будет: ниже показана реальная ошибка.'
  message.style.cssText = 'color:#c8d6e5;line-height:1.5'

  const pre = document.createElement('pre')
  pre.textContent = details
  pre.style.cssText = [
    'white-space:pre-wrap',
    'word-break:break-word',
    'background:#07131f',
    'border:1px solid #284057',
    'border-radius:10px',
    'padding:14px',
    'color:#ffd2d6',
    'max-height:45vh',
    'overflow:auto',
  ].join(';')

  const retry = document.createElement('button')
  retry.type = 'button'
  retry.textContent = 'Перезапустить страницу'
  retry.style.cssText = [
    'margin-top:14px',
    'border:0',
    'border-radius:8px',
    'padding:12px 16px',
    'background:linear-gradient(90deg,#7435e1,#1797f1)',
    'color:white',
    'font-weight:700',
    'cursor:pointer',
  ].join(';')
  retry.addEventListener('click', () => location.reload())

  card.append(title, message, pre, retry)
  panel.append(card)
  root.append(panel)
}

window.addEventListener('error', (event) => {
  window.setTimeout(() => {
    if (root?.childElementCount === 0) {
      showStartupError(event.error ?? event.message)
    }
  }, 0)
})

window.addEventListener('unhandledrejection', (event) => {
  window.setTimeout(() => {
    if (root?.childElementCount === 0) {
      showStartupError(event.reason)
    }
  }, 0)
})

void import('./legacy-app.bundle.js')
  .then(() => {
    window.setTimeout(() => {
      if (!root || root.childElementCount === 0) {
        showStartupError(new Error('Frontend module loaded, but React did not mount anything into #root.'))
      }
    }, 1500)
  })
  .catch(showStartupError)

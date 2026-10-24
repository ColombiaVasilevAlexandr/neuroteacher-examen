const assert = require('node:assert/strict')
const vm = require('node:vm')
const fs = require('node:fs')
const path = require('node:path')
const source = fs.readFileSync(path.join(__dirname, '../frontend/public/neural-voice.js'), 'utf8')
const tick = () => new Promise(resolve => setTimeout(resolve, 5))
function harness(fetch) {
  const state = {plays: 0, urls: 0, errors: 0}
  const synthesis = {cancel() {},getVoices() {return []}}
  const scope = {
    window: {speechSynthesis: synthesis, COLOMBIA_API_BASE: 'http://test/api', addEventListener() {}, dispatchEvent() {}},
    fetch, AbortController, Event,
    URL: {createObjectURL() {state.urls++; return 'blob:test'}, revokeObjectURL() {state.urls--}},
    Audio: class {
      play() {state.plays++; setTimeout(() => this.onended?.(), 0); return Promise.resolve()}
      pause() {}
      removeAttribute() {}
    }
  }
  vm.runInNewContext(source, scope)
  for (const name of ['speech-cleaner.js','spanish-voice.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../frontend/public',name),'utf8'), scope)
  return {state, synthesis}
}
;(async () => {
  let resolveFetch
  let h = harness(() => new Promise(resolve => {resolveFetch = resolve}))
  h.synthesis.speak({text: 'Hola'})
  h.synthesis.cancel()
  resolveFetch({ok: true, blob: async () => ({})})
  await tick()
  assert.equal(h.state.plays, 0, 'cancel during fetch must prevent late playback')
  let resolveBlob
  h = harness(async () => ({ok: true, blob: () => new Promise(resolve => {resolveBlob = resolve})}))
  h.synthesis.speak({text: 'Hola'})
  await tick()
  h.synthesis.cancel()
  resolveBlob({})
  await tick()
  assert.equal(h.state.plays, 0, 'cancel during blob decoding must prevent late playback')
  const calls = []
  h = harness(async (url, options) => {calls.push([url, JSON.parse(options.body)]); return {ok: true, blob: async () => ({})}})
  let ended = 0
  h.synthesis.speak({text: 'Hola.\n\nПривет.', lang: 'es-CO', rate: 1, onend: () => ended++})
  await new Promise(resolve => setTimeout(resolve, 30))
  assert.equal(calls.length, 2)
  assert.equal(calls[0][1].locale, 'es-CO')
  assert.equal(calls[1][1].locale, 'ru-RU')
  assert.equal(calls[0][1].rate, '+0%')
  assert.equal(ended, 1)
  assert.equal(h.state.urls, 0, 'audio URLs must be released')
  assert.ok(calls.every(([url]) => url === 'http://test/api/consultant/speech'))
  calls.length = 0
  h = harness(async (url, options) => {calls.push(JSON.parse(options.body)); return {ok:true,blob:async()=>({})}})
  h.synthesis.speak({text:'Welcome to Colombia.',lang:'en-US'})
  await new Promise(resolve => setTimeout(resolve, 30))
  assert.equal(calls[0].locale,'en-US')
  h.synthesis.speak({text:'欢迎来到哥伦比亚。',lang:'es-CO'})
  await new Promise(resolve => setTimeout(resolve, 30))
  assert.equal(calls[1].locale,'zh-CN')
  h = harness(async () => ({ok: false}))
  let errors = 0
  h.synthesis.speak({text: 'Hola', onerror: () => errors++})
  await tick()
  assert.equal(errors, 1)
  console.log('PASS: late fetch/blob cancellation, mixed languages, rate, API base, URL cleanup and service failure')
})().catch(error => {console.error(error); process.exitCode = 1})

# Frontend Runtime

This project currently runs a static frontend from `frontend/public`.

## Entrypoint

The only supported browser entrypoint is:

```text
frontend/public/index.html
```

It is served by `scripts/start-neuroteacher.ps1` through:

```text
python -m http.server 5173 --bind <bindHost>
```

The page loads assets in this order:

1. `app.bundle.css`
2. inline mount-failure fallback
3. `runtime-config.js`
4. `legacy-app.bundle.js`
5. deferred runtime extensions such as `study-plan.js`, `audio-library.js`, and `daily-quote.js`

## Runtime Contract

`runtime-config.js` owns API base resolution for localhost, LAN, and reverse-proxy deployments.

`legacy-app.bundle.js` is the primary UI artifact. It is a checked-in runtime bundle, not a maintained source tree.

`study-plan.js`, `audio-library.js`, and the other small files in `frontend/public` are runtime extensions layered on top of the primary bundle. They may be edited directly when the change is narrow and static-only.

## Edit Policy

Safe direct edits:

- `frontend/public/index.html`
- `frontend/public/runtime-config.js`
- small runtime extension files in `frontend/public`
- CSS files paired with those extensions

Checkpoint required:

- rebuilding or replacing `legacy-app.bundle.js`
- replacing `app.bundle.css`
- reintroducing React/Vite source files
- changing the frontend boot order in `index.html`

## Migration Note

If the project returns to a source-based frontend, do it as a separate phase:

1. create a real source tree;
2. document the build command;
3. document the generated output files;
4. keep the static runtime working during the migration;
5. update `scripts/smoke_test.py` only after the runtime contract changes.

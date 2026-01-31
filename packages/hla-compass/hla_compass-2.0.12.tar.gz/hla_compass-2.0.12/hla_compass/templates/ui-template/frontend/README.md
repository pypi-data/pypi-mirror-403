# Module UI Template

Lean scaffold for module-specific inputs and results, built with Vite + React + Ant Design.

## Quick start

1. Start the backend preview (from the module root):

```bash
hla-compass serve --port 8080
```

2. Start the frontend dev server (from `frontend/`):

```bash
npm install
npm run dev
```

3. Open `http://localhost:3000` — the dev server proxies `/api/*` to `http://localhost:8080`.

## Customize the UI

- Update the form fields in `index.tsx` to match `manifest.json` inputs.
- Align the `params` object in `handleSubmit` with your backend inputs.
- Tailor the results section to match your module output shape.

## Build output

```bash
npm run build:all
```

Produces two UMD bundles in `dist/`:

| File | Purpose |
|---|---|
| `bundle.js` | Platform-embedded bundle (externalises React, ReactDOM, antd) |
| `bundle.standalone.js` | Self-contained bundle for `hla-compass serve` (includes all deps) |

Both expose `window.ModuleUI` as a UMD global.

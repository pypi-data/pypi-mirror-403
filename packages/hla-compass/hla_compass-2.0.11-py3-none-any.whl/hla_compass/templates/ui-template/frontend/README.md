# Module UI Template

Lean scaffold for module-specific inputs and results. It includes:
- A minimal form wired to `onExecute` or `devPost('/execute', ...)`
- Result rendering (table or JSON)
- Platform-aligned theming via design system tokens

## Quick start

1) Generate your module from this template (see SDK docs)
2) Start the backend preview (from the module root):

```bash
hla-compass serve --port 8080
```

3) Start the frontend dev server (from `frontend/`):

```bash
npm run dev
```

4) Open the UI and run the form.

The dev server proxies `/api/*` to `http://localhost:8080` by default.

## Customize the UI

- Update the form fields in `index.tsx` to match `manifest.json` inputs.
- Align the `params` object in `handleSubmit` with your backend inputs.
- Tailor the results section to match your module output shape.

## Local execution

The template calls the local backend for execution when `onExecute` is not provided:

```ts
import { devPost } from './api';

const result = await devPost('/execute', { input: params });
```

## Theming

- When embedded in the platform, the template inherits the host theme.
- When running standalone, it applies a safe set of Ant Design CSS variables.

## Build output

```bash
npm run build
```

The webpack output emits a UMD global named `ModuleUI`. The platform expects
`window.ModuleUI` when mounting your bundle.

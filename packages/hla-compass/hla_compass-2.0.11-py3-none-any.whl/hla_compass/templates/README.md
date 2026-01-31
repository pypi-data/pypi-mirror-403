# HLA-Compass Module Templates

This directory contains two main templates for developing HLA-Compass modules:

## 📱 UI Template (`ui-template/`)
For modules that need a user interface. Includes:
- **Backend**: Python module with UI-friendly response formatting
- **Frontend**: React/TypeScript UI with a lean input form and results view
- **Styling**: Tailwind CSS + scientific design system matching the platform
- Input validation and error handling
- Results display with summary statistics
- Consistent visual design with HLA-Compass platform

### When to use:
- Interactive data exploration
- User-driven analysis
- Visual results presentation
- Parameter configuration interfaces

### Key files:
- `backend/main.py` - Module logic with UI formatting
- `frontend/index.tsx` - React component with platform-matching design
- `frontend/styles.css` - Scientific styling system
- `frontend/tailwind.config.js` - Design system configuration

### Bundle size notes:
- The UI template is intentionally lean; keep dependencies minimal to reduce bundle size.
- If you add charting or visualization libraries, consider lazy-loading them to avoid large initial bundles.

## 🔧 No-UI Template (`no-ui-template/`)
For `no-ui` (backend-only) modules without user interface. Includes:
- Batch processing capabilities
- API response formatting
- Data source flexibility (files, S3, direct input)
- Progress tracking
- Comprehensive error handling

### When to use:
- Automated workflows
- Batch data processing
- API integrations
- Scheduled jobs
- Pipeline components

### Key files:
- `backend/main.py` - Backend processing logic

## Quick Start

### 1. Choose your template:
```bash
# Recommended: scaffold with the CLI
hla-compass init my-module --template ui
# or
hla-compass init my-module --template no-ui
```

### 2. Update the module:
- Update manifest metadata (name, version, author) and class names.
- Implement `execute()` to call module logic and return `self.success(...)`.
- Define `Input` fields or `validate_inputs()` to match the manifest schema.
- Configure data sources and permissions in `manifest.json`.
- For UI modules, align `frontend/index.tsx` form fields with the input schema.

### 3. For UI modules - Setup frontend:
```bash
cd my-module/frontend/
npm install
npm run dev  # Development server
npm run build  # Production build
```

> The generated webpack configuration emits a UMD global named `ModuleUI`. Keep that export intact—HLA-Compass looks for `window.ModuleUI` when mounting your bundle.

To execute the backend while iterating on the UI:
```bash
# Terminal A (from module root)
hla-compass serve --port 8080

# Terminal B (from frontend/)
npm run dev
```

#### Available styling features:
- **Tailwind CSS**: Utility-first CSS framework
- **Scientific design system**: Colors and spacing optimized for data
- **Platform consistency**: Matches HLA-Compass main interface
- **Responsive design**: Mobile-friendly layouts
- **Accessibility**: Screen reader and keyboard navigation support

### 4. Key methods to implement:

#### `execute()` - Main processing function
```python
def execute(self, input_data, context):
    results = self._process_data(input_data)
    return self.success(results=results)
```

#### `Input` / `validate_inputs()` - Input validation
```python
from pydantic import BaseModel

class Input(BaseModel):
    sample_id: str
    min_score: float = 0.0

class MyModule(Module):
    Input = Input
    # Optional: override validate_inputs(...) for custom validation logic
```

#### `_process_data()` - Core processing logic
```python
def _process_data(self, data):
    return [
        {
            "id": data.get("sample_id", "unknown"),
            "score": float(data.get("min_score", 0.0)),
            "processed": True,
        }
    ]
```

## Available SDK Features

Both templates have access to:

### Data Access
- `self.peptides.search()` - Search peptide database
- `self.storage.save_json()` / `save_file()` - Persist results to object storage
- `self.storage.save_csv()` / `save_excel()` - Export tabular data when needed
- `self.storage.create_download_url()` - Generate presigned links for saved artefacts

### Logging
- `self.logger.info()` - Information logs
- `self.logger.error()` - Error logs
- `self.logger.warning()` - Warning logs

### Response Helpers
- `self.success()` - Return success response
- `self.error()` - Raise a ModuleError (run() catches and formats the error response)

## Testing Your Module

```bash
# Local test via container (recommended)
hla-compass test --input examples/sample_input.json
```

## Runtime & Deployment

Modules built from these templates run inside Docker containers. The platform's
`module-runner` entrypoint instantiates your `Module` subclass directly, so no
extra handler function is required.

Typical workflow:

```bash
# Build container image + manifest descriptor
hla-compass build

# Publish to an environment (dev/staging/prod)
hla-compass publish --env dev
```

During execution the platform mounts payload/context artefacts into the
container and invokes `Module.execute`. Any files you write via
`self.storage.save_*` become part of the job results.

For local UI preview, run:
```bash
hla-compass serve --port 8080
```

## Best Practices

1. **Always validate input** - Check types, ranges, and required fields
2. **Use batch processing** - Process large datasets in chunks
3. **Log important events** - Help with debugging and monitoring
4. **Handle errors gracefully** - Return meaningful error messages
5. **Document your code** - Update docstrings and comments
6. **Test thoroughly** - Include unit tests in your module

## Need Help?

- Check the existing templates for examples
- Review the SDK documentation
- Contact the platform team for support

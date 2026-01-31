# HLA-Compass Python SDK

[![PyPI version](https://badge.fury.io/py/hla-compass.svg)](https://badge.fury.io/py/hla-compass)
[![Python Versions](https://img.shields.io/pypi/pyversions/hla-compass.svg)](https://pypi.org/project/hla-compass/)

The official Python SDK for developing modules on the HLA-Compass platform.

## 🚀 Quick Start

```bash
# 1. Install
pip install hla-compass

# 2. Setup
hla-compass auth login --env dev

# 3. Create
hla-compass init my-module --template no-ui
cd my-module

# 4. Test
hla-compass test

# 5. Ship
hla-compass build && hla-compass publish --env dev --generate-keys
```

📚 **New to HLA-Compass?** Try the **[Ten-Minute Tutorial](../../internal-docs/guides/module-developer/tutorial.md)**.

---

## 🛠️ CLI Entry Points

| Command | Description |
|:--------|:------------|
| `init` | Scaffold a new module from templates |
| `validate` | Validate module structure and manifest |
| `test` | Run module execution (local or remote context) |
| `build` | Build Docker image |
| `publish` | Sign and register module with the platform |
| `auth` | Manage platform login and keys |

---

## 🔧 Local SDK Development

When iterating on the SDK itself, build images against your local checkout:

```bash
hla-compass build --sdk-path ../sdk/python
# or set HLA_COMPASS_SDK_PATH=../sdk/python for dev/test/serve/build
```

To target a specific architecture:

```bash
hla-compass build --platform linux/amd64
```

Multi-arch builds require `--platform linux/amd64,linux/arm64 --push`.

---

## 💎 Key Features

- **Module-first CLI**: Scaffold, build, test, and publish with a single toolchain.
- **Signed publishing**: Keys + manifest signing baked into `publish`.
- **Data helpers**: Storage + data access helpers for module runtimes.
- **Local dev loop**: Containerized `dev`/`serve`/`test` flow that matches production.

---

## 📖 Advanced Documentation

- **[Installation Guide](../../DEVELOPER_GUIDE.md)** – Detailed setup for various roles.
- **[Module Developer Handbook](../../internal-docs/guides/module-developer/index.md)** – Best practices and deep dives.
- **[API Reference](https://developer.alithea.bio/sdk)** – Full Pydoc catalog of classes and methods.

---

## 🤝 Support & Issues

- **Bugs**: [GitHub Issues](https://github.com/AlitheaBio/HLA-Compass-platform/issues)
- **Discussion**: #hla-compass-dev Slack channel

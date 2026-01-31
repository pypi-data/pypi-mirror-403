"""
Module lifecycle commands (init, build, publish, validate).
"""

import os
import sys
import json
import shutil
import subprocess
import time
import click
import importlib
from pathlib import Path
from typing import Optional, Dict, Any

from rich.prompt import Confirm
from rich.table import Table
from rich.live import Live

from ..auth import Auth
from ..config import Config
from ..client import APIClient, APIError
from ..env import get_publish_defaults, PublishConfigError
from ..signing import ModuleSigner
from ..validation import ModuleValidator
from .utils import console, verbose_option, ensure_docker_available, _ensure_verbose

def load_sdk_config():
    try:
        config_path = Config.get_config_path()
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
    except Exception:
        pass
    return None

@click.command()
@verbose_option
@click.argument("name", required=False)
@click.option("--template", type=click.Choice(["ui", "no-ui"]), default="no-ui", help="Module template")
@click.option("--yes", is_flag=True, help="Non-interactive mode")
@click.pass_context
def init(ctx, name, template, yes):
    """Create a new HLA-Compass module"""
    _ensure_verbose(ctx)
    if not name:
        console.print("[red]Module name required[/red]")
        return

    # Validate name
    import re
    name_pattern = r"^[a-z0-9]([a-z0-9-]{1,48}[a-z0-9])?$"
    if not re.match(name_pattern, name):
        console.print(f"[red]Invalid module name '{name}'[/red]")
        console.print(f"Name must match regex: {name_pattern}")
        console.print("(Lowercase alphanumeric, hyphens, 2-50 chars, start/end with alphanumeric)")
        return

    module_type = "with-ui" if template == "ui" else "no-ui"
    template_dir_name = f"{template}-template"
    
    # Locate template relative to hla_compass package (parent of this cli package)
    # hla_compass/cli/module.py -> hla_compass/templates
    # We need to go up two levels to sdk/python/hla_compass
    # Or better, use importlib.resources (Python 3.9+) or __file__ relative
    base_path = Path(__file__).parent.parent
    pkg_templates_dir = base_path / "templates" / template_dir_name
    
    if not pkg_templates_dir.exists():
        console.print(f"[red]Template not found at {pkg_templates_dir}[/red]")
        return

    module_dir = Path(name)
    if module_dir.exists() and not yes:
        if not Confirm.ask(f"Directory '{name}' exists. Continue?"): return

    shutil.copytree(pkg_templates_dir, module_dir, dirs_exist_ok=True)
    
    # Update manifest
    manifest_path = module_dir / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    manifest["name"] = name
    manifest["type"] = module_type
    sdk_config = load_sdk_config()
    author_info = sdk_config.get("author", {}) if sdk_config else {}
    
    # Try to get author info from git if not in config
    author_name = author_info.get("name")
    author_email = author_info.get("email")
    
    if not author_name:
        try:
            author_name = subprocess.check_output(["git", "config", "user.name"], text=True).strip()
        except Exception:
            author_name = os.getenv("USER", "Unknown")
            
    if not author_email:
        try:
            author_email = subprocess.check_output(["git", "config", "user.email"], text=True).strip()
        except Exception:
            author_email = "developer@example.com"

    manifest["author"]["name"] = author_name
    manifest["author"]["email"] = author_email
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    if module_type == "no-ui":
        shutil.rmtree(module_dir / "frontend", ignore_errors=True)

    # Pin the runtime SDK dependency inside the generated module to match the CLI SDK version.
    # This keeps `hla-compass init` outputs compatible with the CLI used to create them.
    requirements_path = module_dir / "backend" / "requirements.txt"
    if requirements_path.exists():
        try:
            from .._version import __version__ as sdk_version

            lines = requirements_path.read_text(encoding="utf-8").splitlines()
            rewritten: list[str] = []
            replaced = False
            for line in lines:
                stripped = line.strip()
                if stripped in {"hla-compass", "hla_compass"} or stripped.startswith("hla-compass==") or stripped.startswith("hla-compass>="):
                    rewritten.append(f"hla-compass=={sdk_version}")
                    replaced = True
                else:
                    rewritten.append(line)

            if not replaced:
                rewritten.insert(0, f"hla-compass=={sdk_version}")

            requirements_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning: failed to pin hla-compass dependency in requirements.txt: {e}[/yellow]")

    console.print(f"[green]✓ Module '{name}' created![/green]")


SUPPORTED_COMPUTE_TYPES = {"docker", "fargate", "batch", "lambda", "sagemaker"}


def _require_supported_compute(manifest: Dict[str, Any]) -> None:
    ctype = manifest.get("computeType") or "docker"
    if ctype not in SUPPORTED_COMPUTE_TYPES:
        console.print(f"[red]Compute type '{ctype}' is not supported by the CLI yet.[/red]")
        console.print(f"Supported: {', '.join(sorted(SUPPORTED_COMPUTE_TYPES))}")
        sys.exit(1)


def _normalize_compute_for_api(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map CLI-friendly compute values to backend-accepted values.

    The platform currently expects fargate for container modules; if the manifest
    uses docker we map it to fargate before submission.
    """
    mapped = dict(manifest)
    if mapped.get("computeType") == "docker":
        mapped["computeType"] = "fargate"
        console.print("[dim]Mapped computeType 'docker' -> 'fargate' for platform compatibility.[/dim]")
    return mapped

@click.command()
@verbose_option
@click.option("--tag", help="Docker image tag")
@click.option("--registry", help="Registry prefix")
@click.option(
    "--platform",
    default="linux/amd64",
    show_default=True,
    help="Docker build platform(s), e.g. linux/amd64 or linux/amd64,linux/arm64",
)
@click.option(
    "--sdk-path",
    type=click.Path(path_type=Path),
    envvar="HLA_COMPASS_SDK_PATH",
    help="Install the SDK from a local path inside the image (for development)",
)
@click.option("--push", is_flag=True, help="Push image")
@click.pass_context
def build(ctx, tag, registry, platform, sdk_path, push):
    """Build module container"""
    _ensure_verbose(ctx)
    ensure_docker_available()
    
    manifest_path = Path("manifest.json")
    if not manifest_path.exists():
        console.print("[red]manifest.json not found[/red]")
        sys.exit(1)
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require_supported_compute(manifest)
    module_name = manifest.get("name", "module")
    version = manifest.get("version", "0.0.0")
    
    # Default tag logic
    def _sanitize(v): return "".join(c if c.isalnum() or c in "-_." else "-" for c in v.lower()).strip("-.")
    default_tag = f"{_sanitize(module_name)}:{_sanitize(version)}"
    image_tag = tag or default_tag
    
    local_tag = image_tag
    registry_tag = None
    if registry:
        registry = registry.rstrip("/")
        # Check if the registry string already contains the repository name (common in this platform)
        # If so, we should use tags to distinguish modules instead of sub-repositories
        if "/" not in image_tag.split(":")[0]:
            # Convert "module:version" to "module-version" for the tag
            # This ensures we push to the single 'registry' repo with a unique tag
            # Ensure the tag is sanitized to prevent confusion with registry separators
            safe_tag = image_tag.replace("/", "-") 
            tag_suffix = safe_tag.replace(":", "-")
            registry_tag = f"{registry}:{tag_suffix}"
        else:
            # If image_tag already has a slash, assume user knows what they are doing (custom full path)
            registry_tag = image_tag
            local_tag = image_tag # Use full reference locally too if provided

    # NOTE: The suffix replacement logic above (replacing ':' with '-') is crucial for 
    # maintaining a clean repository structure where all module versions are stored 
    # as tags within a single repository per module, rather than creating separate 
    # repositories for each version. This simplifies ECR management and access control.

    dist_dir = Path("dist")
    dist_dir.mkdir(parents=True, exist_ok=True)

    sdk_source = _prepare_sdk_source(sdk_path, dist_dir)
    _prepare_backend_requirements(dist_dir, sdk_source)
    
    # Helper to write container scripts
    _write_container_serve_script(dist_dir)
    _write_container_runner_script(dist_dir)

    dockerfile_path = dist_dir / "Dockerfile.hla"
    dockerfile_path.write_text(_generate_dockerfile_content(manifest, sdk_source), encoding="utf-8")

    published_tag = registry_tag or local_tag

    multi_platform = bool(platform and "," in platform)
    if multi_platform and not push:
        console.print("[red]Multi-arch builds require --push (or specify a single --platform).[/red]")
        sys.exit(1)

    console.print(f"[cyan]Building {local_tag}...[/cyan]")
    if multi_platform:
        build_cmd = [
            "docker",
            "buildx",
            "build",
            "--platform",
            platform,
            "-f",
            str(dockerfile_path),
            "-t",
            published_tag,
            ".",
            "--push",
        ]
        subprocess.run(build_cmd, check=True)
    else:
        build_cmd = ["docker", "build"]
        if platform:
            build_cmd.extend(["--platform", platform])
        build_cmd.extend(["-f", str(dockerfile_path), "-t", local_tag, "."])
        subprocess.run(build_cmd, check=True)

    if registry_tag and not multi_platform:
        subprocess.run(["docker", "tag", local_tag, registry_tag], check=True)

    if push and not multi_platform:
        console.print(f"[cyan]Pushing {published_tag}...[/cyan]")
        try:
            subprocess.run(["docker", "push", published_tag], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to push image: {e}[/red]")
            if "denied" in str(e) or "unauthorized" in str(e) or "forbidden" in str(e).lower():
                console.print("[yellow]Tip: Check your permissions. You might need to run:[/yellow]")
                console.print(f"  docker login {published_tag.split('/')[0]}")
            raise e
        
    # Report
    report = {
        "image_tag": published_tag if multi_platform else local_tag,
        "published_tag": published_tag,
        "pushed": push,
        "platform": platform,
        "sdk_source": sdk_source,
    }
    (dist_dir / "build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    
    return report

# Helper functions for build
def _write_container_serve_script(dist_dir: Path):
    script = r'''#!/usr/bin/env python3
import json
import importlib
import logging
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

MODULE_ENTRY = os.getenv("HLA_COMPASS_MODULE", None)
MANIFEST_PATH = Path("/app/manifest.json")
INDEX_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HLA-Compass Module</title>
  <link rel="stylesheet" href="https://unpkg.com/antd@5.22.7/dist/reset.css" crossorigin="anonymous">
</head>
<body>
  <div id='root'></div>
  <script crossorigin="anonymous" src="https://unpkg.com/react@19.1.0/umd/react.production.min.js"></script>
  <script crossorigin="anonymous" src="https://unpkg.com/react-dom@19.1.0/umd/react-dom.production.min.js"></script>
  <script crossorigin="anonymous" src="https://unpkg.com/dayjs@1.11.13/dayjs.min.js"></script>
  <script crossorigin="anonymous" src="https://unpkg.com/antd@5.22.7/dist/antd.min.js"></script>
  <script src='/bundle.js'></script>
</body>
</html>"""

def _configure_logging():
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    level_name = os.getenv("LOG_LEVEL") or os.getenv("HLA_COMPASS_LOG_LEVEL") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )

def _resolve_module(entry: str):
    if ":" not in entry: return None
    mod, cls = entry.split(":", 1)
    m = importlib.import_module(mod)
    return getattr(m, cls)()

def _load_manifest():
    try: return json.loads(MANIFEST_PATH.read_text())
    except: return {}

def _locate_ui_dist():
    candidates = [Path("/app/ui/dist"), Path("/app/frontend/dist")]
    for p in candidates:
        if p.exists(): return p
    return None

class _Handler(BaseHTTPRequestHandler):
    server_version = "hla-compass-serve/1.0"

    def log_message(self, fmt, *args):
        logging.getLogger("container-serve").info("%s - %s", self.address_string(), fmt % args)

    def _send(self, body: bytes, status: int, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self._send(body, status, "application/json")

    def _send_text(self, text: str, status: int = 200, content_type: str = "text/html"):
        self._send(text.encode("utf-8"), status, content_type)

    def _serve_index(self, root: Path | None):
        if root:
            index_path = root / "index.html"
            if index_path.is_file():
                return self._serve_file(index_path)
        return self._send_text(INDEX_HTML)

    def _serve_file(self, path: Path):
        content_type, _ = mimetypes.guess_type(str(path))
        content_type = content_type or "application/octet-stream"
        self._send(path.read_bytes(), 200, content_type)

    def do_POST(self):
        if self.path != "/api/execute":
            return self._send_text("Not found", 404, "text/plain")
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}
        input_data = payload.get("input", {})
        offline_env = str(os.getenv("HLA_COMPASS_OFFLINE", "")).lower() in {"1", "true", "yes"}
        has_credentials = bool(os.getenv("HLA_API_KEY") or os.getenv("HLA_ACCESS_TOKEN"))
        context = {
            "mode": "interactive",
            "run_id": "serve-dev",
            "offline": offline_env or not has_credentials,
        }
        try:
            module = self.server.module
            if module is None:
                return self._send_json({"status": "error", "message": "Module entrypoint not found"}, 500)
            result = module.run(input_data, context)
            return self._send_json(result)
        except Exception as exc:
            return self._send_json({"status": "error", "message": str(exc)}, 500)

    def do_GET(self):
        path = urlparse(self.path).path or "/"
        if path.startswith("/api/"):
            return self._send_text("Not found", 404, "text/plain")
        root = self.server.ui_root
        if path == "/":
            return self._serve_index(root)
        if not root:
            return self._send_text("No UI")
        file_path = (root / path.lstrip("/")).resolve()
        try:
            file_path.relative_to(root)
        except Exception:
            return self._send_text("Not found", 404, "text/plain")
        if file_path.is_file():
            return self._serve_file(file_path)
        return self._serve_index(root)

class _Server(ThreadingHTTPServer):
    allow_reuse_address = True

def main():
    _configure_logging()
    manifest = _load_manifest()
    entry = MODULE_ENTRY or manifest.get("execution", {}).get("entrypoint") or "backend.main:Module"
    module = _resolve_module(entry)
    ui_root = _locate_ui_dist()
    port = int(os.getenv("PORT", 8080))
    server = _Server(("0.0.0.0", port), _Handler)
    server.module = module
    server.ui_root = ui_root
    server.serve_forever()

if __name__ == "__main__":
    main()
'''
    (dist_dir / "container-serve.py").write_text(script, encoding="utf-8")

def _write_container_runner_script(dist_dir: Path):
    script = r'''#!/usr/bin/env python3
import logging
import os
import sys

def _configure_logging():
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    level_name = os.getenv("LOG_LEVEL") or os.getenv("HLA_COMPASS_LOG_LEVEL") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )

def main():
    _configure_logging()
    from hla_compass.runtime.runner import main as runner_main
    runner_main()

if __name__ == "__main__":
    main()
'''
    (dist_dir / "container-runner.py").write_text(script, encoding="utf-8")

def _prepare_sdk_source(sdk_path: Optional[Path], dist_dir: Path) -> Optional[str]:
    if not sdk_path:
        existing = dist_dir / "sdk-src"
        if existing.exists():
            shutil.rmtree(existing)
        return None

    resolved = sdk_path.expanduser().resolve()
    if not resolved.exists():
        console.print(f"[red]SDK path not found: {resolved}[/red]")
        sys.exit(1)
    if not resolved.is_dir():
        console.print(f"[red]SDK path must be a directory: {resolved}[/red]")
        sys.exit(1)

    target = dist_dir / "sdk-src"
    if target.exists():
        shutil.rmtree(target)

    def _ignore_sdk(_path: str, names: list[str]) -> set[str]:
        ignore = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            "dist",
            "build",
            ".idea",
            ".vscode",
        }
        return {name for name in names if name in ignore}

    shutil.copytree(resolved, target, symlinks=True, ignore=_ignore_sdk)
    return target.as_posix()

def _is_hla_compass_requirement(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    lowered = stripped.lower()
    if lowered.startswith(("hla-compass", "hla_compass")):
        return True
    if "hla-compass" in lowered or "hla_compass" in lowered:
        if lowered.startswith(("-e", "--editable")):
            return True
    return False


def _prepare_backend_requirements(dist_dir: Path, sdk_source: Optional[str]) -> None:
    override_lock = dist_dir / "requirements.sdk.lock.txt"
    override_plain = dist_dir / "requirements.sdk.txt"
    for candidate in (override_lock, override_plain):
        if candidate.exists():
            candidate.unlink()

    if not sdk_source:
        return

    lock_path = Path("backend/requirements.lock.txt")
    req_path = Path("backend/requirements.txt")
    source_path = lock_path if lock_path.exists() else req_path
    if not source_path.exists():
        return

    lines = source_path.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if not _is_hla_compass_requirement(line)]
    target = override_lock if lock_path.exists() else override_plain
    target.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def _generate_dockerfile_content(manifest, sdk_source: Optional[str] = None):
    entry = manifest.get("execution", {}).get("entrypoint") or "backend.main:Module"
    
    lines = ["# syntax=docker/dockerfile:1"]
    
    has_frontend = Path("frontend/package.json").exists()
    if has_frontend:
        lines.extend([
            "FROM node:20.19.6-alpine AS ui",
            "WORKDIR /ui",
            "COPY frontend/package*.json ./",
            "RUN npm install --legacy-peer-deps",
            "COPY frontend/ ./",
            "RUN npm run build"
        ])
        
    lines.extend([
        "FROM python:3.11.13-slim-bullseye",
        "RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && rm -rf /var/lib/apt/lists/*",
        "WORKDIR /app",
        "RUN pip install --no-cache-dir --upgrade pip setuptools==78.1.1",
    ])

    if sdk_source:
        lines.append(f"COPY {sdk_source} /tmp/hla-compass-sdk")
        lines.append("RUN pip install --no-cache-dir /tmp/hla-compass-sdk")
    else:
        from .._version import __version__ as sdk_version
        lines.append(f"RUN pip install --no-cache-dir hla-compass=={sdk_version}")

    lines.append("COPY manifest.json /app/manifest.json")
    
    override_lock = Path("dist/requirements.sdk.lock.txt")
    override_plain = Path("dist/requirements.sdk.txt")
    if override_lock.exists():
        lines.append("COPY dist/requirements.sdk.lock.txt /tmp/reqs.lock.txt")
        lines.append("RUN pip install --require-hashes -r /tmp/reqs.lock.txt")
    elif override_plain.exists():
        lines.append("COPY dist/requirements.sdk.txt /tmp/reqs.txt")
        lines.append("RUN pip install -r /tmp/reqs.txt")
    elif Path("backend/requirements.txt").exists():
        lock_path = Path("backend/requirements.lock.txt")
        if lock_path.exists():
            lines.append("COPY backend/requirements.lock.txt /tmp/reqs.lock.txt")
            lines.append("RUN pip install --require-hashes -r /tmp/reqs.lock.txt")
        else:
            lines.append("COPY backend/requirements.txt /tmp/reqs.txt")
            lines.append("RUN pip install -r /tmp/reqs.txt")
        
    lines.append("COPY backend/ /app/backend/")
    
    if has_frontend:
        lines.extend([
            "RUN mkdir -p /app/ui",
            "COPY --from=ui /ui/dist /app/ui/dist"
        ])
        
    lines.extend([
        "ENV PYTHONPATH=/app",
        f"ENV HLA_COMPASS_MODULE={entry}",
        "COPY dist/container-serve.py /app/container-serve.py",
        "COPY dist/container-runner.py /app/container-runner.py",
        "EXPOSE 8080",
        'ENTRYPOINT ["python", "/app/container-runner.py"]'
    ])
    
    return "\n".join(lines)

@click.command()
@verbose_option
@click.option("--env", required=True, type=click.Choice(["dev", "staging", "prod"]))
@click.option("--image-ref", help="Image reference")
@click.option("--registry", help="Registry override")
@click.option(
    "--platform",
    default="linux/amd64",
    show_default=True,
    help="Docker build platform(s), e.g. linux/amd64 or linux/amd64,linux/arm64",
)
@click.option(
    "--sdk-path",
    type=click.Path(path_type=Path),
    envvar="HLA_COMPASS_SDK_PATH",
    help="Install the SDK from a local path inside the image (for development)",
)
@click.option(
    "--scope",
    type=click.Choice(["org", "public"]),
    default="org",
    help="Module scope: 'org' (auto-approved, org-only) or 'public' (needs approval)"
)
@click.option("--visibility", hidden=True, help="Deprecated alias for --scope")
@click.option("--generate-keys", is_flag=True, help="Auto-generate signing keys if missing")
@click.option("--dry-run", is_flag=True, help="Validate and show what would be published without making changes")
@click.pass_context
def publish(ctx, env, image_ref, registry, platform, sdk_path, scope, visibility, generate_keys, dry_run):
    """Publish module to the HLA-Compass platform.
    
    Scope determines approval workflow:
    - org: Auto-approved, only your organization can use it
    - public: Requires superuser approval before others can use it
    """
    _ensure_verbose(ctx)
    Config.set_environment(env)
    
    # Handle deprecated visibility flag
    if visibility:
        console.print("[yellow]⚠️ The '--visibility' option is deprecated; please use '--scope' instead.[/yellow]")
        # If scope is default ("org") but visibility is set, map visibility to scope
        # We check if scope was explicitly provided to avoid overwriting it
        if ctx.get_parameter_source("scope").name == "DEFAULT":
            if visibility.lower() in ("private", "org"):
                scope = "org"
            elif visibility.lower() == "public":
                scope = "public"
    
    auth = Auth()
    if not auth.is_authenticated():
        console.print("[red]Not authenticated[/red]")
        sys.exit(1)
    
    # Fetch registry from API if not provided
    if not registry:
        try:
            publish_config = get_publish_defaults(env)
            registry = publish_config.get("registry")
            if registry:
                console.print(f"[dim]Using registry: {registry}[/dim]")
        except PublishConfigError as e:
            console.print(f"[yellow]Warning: Could not fetch publish config: {e}[/yellow]")
        
    client = APIClient()
    
    manifest = json.loads(Path("manifest.json").read_text())
    _require_supported_compute(manifest)

    # Map computeType for backend compatibility (docker -> fargate)
    # Sign the exact payload we submit to avoid signature mismatch.
    manifest_for_api = _normalize_compute_for_api(manifest)

    # Dry-run mode: validate and show what would happen
    if dry_run:
        console.print("[cyan]═══ DRY RUN MODE ═══[/cyan]")
        console.print()
        
        # Validate manifest
        validator = ModuleValidator(manifest_path="manifest.json")
        res = validator.run()
        if res.valid:
            console.print("[green]✓ Manifest validation passed[/green]")
        else:
            console.print("[red]✗ Manifest validation failed[/red]")
            for issue in res.issues:
                console.print(f"  {issue.code}: {issue.message}")
            sys.exit(1)
        
        # Show computed values
        module_name = manifest.get("name", "unknown")
        version = manifest.get("version", "0.0.0")
        compute_type = manifest_for_api.get("computeType", "fargate")
        
        table = Table(title="Publish Summary (Dry Run)", show_lines=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Module", module_name)
        table.add_row("Version", version)
        table.add_row("Scope", scope)
        table.add_row("Environment", env)
        table.add_row("Compute Type", compute_type)
        table.add_row("Registry", registry or "(default)")
        
        if image_ref:
            table.add_row("Image Ref", image_ref)
        else:
            # Compute what image tag would be
            safe_name = "".join(c if c.isalnum() or c in "-_." else "-" for c in module_name.lower()).strip("-.")
            safe_version = "".join(c if c.isalnum() or c in "-_." else "-" for c in version.lower()).strip("-.")
            computed_tag = f"{safe_name}:{safe_version}"
            if registry:
                computed_tag = f"{registry}:{safe_name}-{safe_version}"
            table.add_row("Computed Tag", computed_tag)
        
        # Check signing keys
        signer = ModuleSigner()
        try:
            signer.get_public_key_string()
            table.add_row("Signing", f"✓ Keys found ({signer.get_key_fingerprint()[:16]}...)")
        except FileNotFoundError:
            if generate_keys:
                table.add_row("Signing", "Keys will be auto-generated")
            else:
                table.add_row("Signing", "[red]✗ Keys not found[/red]")
        
        console.print(table)
        console.print()
        console.print("[dim]No changes were made (--dry-run mode)[/dim]")
        return

    if not image_ref:
        # Build first
        report = ctx.invoke(build, push=True, registry=registry, platform=platform, sdk_path=sdk_path)
        image_ref = report.get("published_tag")
    
    # Map computeType for backend compatibility (docker -> fargate)
    # Sign the exact payload we submit to avoid signature mismatch.
    manifest_for_api = _normalize_compute_for_api(manifest)

    signer = ModuleSigner()
    try:
        manifest_for_api["signature"] = signer.sign_manifest(manifest_for_api)
        manifest_for_api["publicKey"] = signer.get_public_key_string()
        manifest_for_api["keyFingerprint"] = signer.get_key_fingerprint()
        manifest_for_api["signatureAlgorithm"] = signer.ALGORITHM
        manifest_for_api["hashAlgorithm"] = signer.HASH_ALGORITHM
    except FileNotFoundError:
        if generate_keys:
            console.print("[yellow]Signing keys not found. Generating new keys...[/yellow]")
            signer.generate_keys()
            manifest_for_api["signature"] = signer.sign_manifest(manifest_for_api)
            manifest_for_api["publicKey"] = signer.get_public_key_string()
            manifest_for_api["keyFingerprint"] = signer.get_key_fingerprint()
            manifest_for_api["signatureAlgorithm"] = signer.ALGORITHM
            manifest_for_api["hashAlgorithm"] = signer.HASH_ALGORITHM
        else:
            console.print("[red]Signing keys not found.[/red]")
            console.print("Run `hla-compass keys init` or re-run publish with --generate-keys.")
            sys.exit(1)
        
    payload = {
        "imageRef": image_ref,
        "manifest": manifest_for_api,
        "scope": scope
    }
    
    try:
        result = client.register_container_module(payload)
    except APIError as e:
        status = f"{e.status_code}" if getattr(e, "status_code", None) else "unknown"
        console.print(f"[red]Publish failed ({status}): {e}[/red]")
        if getattr(e, "status_code", None) == 401:
            console.print("[dim]Hint: Run `hla-compass auth login --env {env}` and retry.[/dim]".format(env=env))
        elif getattr(e, "status_code", None) == 403:
            console.print("[dim]Hint: Ensure your account/org has permission to publish modules in this environment.[/dim]")
        sys.exit(1)

    publish_id = result.get("publishId") if isinstance(result, dict) else None
    if publish_id:
        console.print(f"[dim]Publish job: {publish_id}[/dim]")
    
    # Display result based on module state
    state = result.get("state") if isinstance(result, dict) else None
    if state == "SUBMITTED":
        console.print(f"[yellow]✓ Module submitted for approval (scope: public)[/yellow]")
        console.print("[dim]A superuser must approve before it's publicly available[/dim]")
    elif state == "APPROVED":
        console.print(f"[green]✓ Module published and approved (scope: {scope})[/green]")
    else:
        console.print(f"[green]✓ Module published to {env}[/green]")

@click.command(name="publish-status")
@verbose_option
@click.option("--env", type=click.Choice(["dev", "staging", "prod"]), help="Target environment")
@click.option("--watch", is_flag=True, help="Poll until the publish job completes")
@click.option("--timeout", type=int, default=900, show_default=True, help="Max seconds to wait when --watch is set")
@click.option("--interval", type=int, default=10, show_default=True, help="Poll interval seconds when --watch is set")
@click.argument("publish_id")
def publish_status(env: Optional[str], watch: bool, timeout: int, interval: int, publish_id: str):
    """Show (and optionally watch) module publish intake status."""
    if env:
        Config.set_environment(env)

    client = APIClient()
    deadline = time.time() + max(timeout, 30)

    def _render(status_payload: Dict[str, Any]) -> Table:
        table = Table(title="Publish Status", show_lines=False)
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        for key in (
            "publishId",
            "status",
            "buildStatus",
            "currentPhase",
            "failureReason",
            "startTime",
            "endTime",
            "message",
            "logsUrl",
        ):
            if key in status_payload and status_payload.get(key) is not None:
                table.add_row(key, str(status_payload.get(key)))
        return table

    last_payload: Optional[Dict[str, Any]] = None

    def _fetch() -> Dict[str, Any]:
        return client.get_module_publish_status(publish_id)

    try:
        if not watch:
            payload = _fetch()
            console.print(_render(payload))
            return

        with Live(console=console, refresh_per_second=4) as live:
            while True:
                payload = _fetch()
                last_payload = payload
                live.update(_render(payload))

                normalized = (payload.get("status") or "").lower()
                if normalized in {"completed", "failed", "cancelled"}:
                    break
                if time.time() >= deadline:
                    raise click.ClickException(f"Timed out waiting for publish job {publish_id}")
                time.sleep(max(interval, 1))

        normalized = ((last_payload or {}).get("status") or "").lower()
        if normalized == "failed":
            reason = (last_payload or {}).get("failureReason") or (last_payload or {}).get("message")
            if reason:
                raise click.ClickException(f"Publish job failed: {publish_id} ({reason})")
            raise click.ClickException(f"Publish job failed: {publish_id}")
    except APIError as e:
        raise click.ClickException(str(e))

@click.command()
@verbose_option
@click.option("--manifest", default="manifest.json")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--strict", is_flag=True, help="Fail on warnings")
def validate(manifest, format, strict):
    """Validate manifest"""
    validator = ModuleValidator(manifest_path=manifest)
    res = validator.run(strict=strict)
    
    if format == "json":
        output = {
            "valid": res.valid,
            "issues": [{"code": i.code, "message": i.message} for i in res.issues]
        }
        click.echo(json.dumps(output))
    else:
        if res.valid:
            console.print("[green]✓ Valid[/green]")
        else:
            console.print("[red]✗ Invalid[/red]")
            for issue in res.issues:
                console.print(f"{issue.code}: {issue.message}")
    
    if not res.valid:
        sys.exit(1)
        
    if strict and res.issues:
        sys.exit(1)

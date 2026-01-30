import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml


class DetectionResult:
    """Standardized result for service detection."""
    def __init__(
        self, 
        name: str, 
        path: str, 
        tier: str, # "backend", "frontend", "agent"
        framework: str, 
        entrypoint: Optional[str] = None,
        port: int = 8000,
        package_manager: str = "pip",
        dependency_file: str = "requirements.txt",
        missing_deps: List[str] = None
    ):
        self.name = name
        self.path = path
        self.tier = tier
        self.framework = framework
        self.entrypoint = entrypoint
        self.port = port
        self.package_manager = package_manager
        self.dependency_file = dependency_file
        self.missing_deps = missing_deps or []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "tier": self.tier,
            "framework": self.framework,
            "entrypoint": self.entrypoint,
            "port": self.port,
            "package_manager": self.package_manager,
            "dependency_file": self.dependency_file,
            "missing_deps": self.missing_deps,
        }


class BaseProbe(ABC):
    """Base class for language-specific detection probes."""
    
    @abstractmethod
    def detect(self, service_dir: Path, name: str) -> Optional[DetectionResult]:
        pass


class PythonProbe(BaseProbe):
    """Probe for Python-based backends and agents."""
    
    def detect(self, service_dir: Path, name: str) -> Optional[DetectionResult]:
        has_pyproject = (service_dir / "pyproject.toml").exists()
        has_requirements = (service_dir / "requirements.txt").exists()
        
        if not has_pyproject and not has_requirements:
            return None
            
        content = ""
        if has_pyproject:
            content = (service_dir / "pyproject.toml").read_text(errors="ignore").lower()
        elif has_requirements:
            content = (service_dir / "requirements.txt").read_text(errors="ignore").lower()

        # Determine Tier & Framework
        tier = "backend"
        framework = "fastapi" # Default
        
        # Check for Agents
        if any(lib in content for lib in ["mcp", "langgraph", "crewai", "langchain"]):
            tier = "agent"
            framework = "mcp" if "mcp" in content else "langgraph"
        elif "django" in content or "djangorestframework" in content:
            framework = "django"
        elif "flask" in content:
            framework = "flask"

        entrypoint = _detect_python_entrypoint(service_dir, name)
        
        # Proactive Dependency Scanning (Zen Mode Auto-Healing)
        missing_deps = _scan_proactive_dependencies(service_dir)

        return DetectionResult(
            name=name,
            path=str(service_dir),
            tier=tier,
            framework=framework,
            entrypoint=entrypoint,
            package_manager="uv" if has_pyproject else "pip",
            dependency_file="pyproject.toml" if has_pyproject else "requirements.txt",
            missing_deps=missing_deps
        )


class NodeProbe(BaseProbe):
    """Probe for Node.js based frontends and backends."""
    
    def detect(self, service_dir: Path, name: str) -> Optional[DetectionResult]:
        package_json = service_dir / "package.json"
        if not package_json.exists():
            return None
            
        try:
            with open(package_json, "r") as f:
                config = json.load(f)
        except Exception:
            return None
            
        deps = {**config.get("dependencies", {}), **config.get("devDependencies", {})}
        
        # Determine Tier
        tier = "backend"
        framework = "node"
        
        if any(lib in deps for lib in ["next", "react", "vue", "svelte", "nuxt", "angular"]):
            tier = "frontend"
            framework = "nextjs" if "next" in deps else ("react" if "react" in deps else "frontend")
        elif any(lib in deps for lib in ["express", "fastify", "nest", "hono"]):
            tier = "backend"
            framework = "express" if "express" in deps else "node-backend"
        elif "@modelcontextprotocol/sdk" in deps:
            tier = "agent"
            framework = "mcp"

        return DetectionResult(
            name=name,
            path=str(service_dir),
            tier=tier,
            framework=framework,
            package_manager="npm",
            dependency_file="package.json",
            port=3000 if tier == "frontend" else 8000
        )


class GoProbe(BaseProbe):
    """Probe for Go backends."""
    
    def detect(self, service_dir: Path, name: str) -> Optional[DetectionResult]:
        go_mod = service_dir / "go.mod"
        if not go_mod.exists():
            return None
            
        content = go_mod.read_text(errors="ignore").lower()
        framework = "go-std"
        if "gin-gonic" in content:
            framework = "gin"
        elif "labstack/echo" in content:
            framework = "echo"
            
        return DetectionResult(
            name=name,
            path=str(service_dir),
            tier="backend",
            framework=framework,
            package_manager="go",
            dependency_file="go.mod"
        )


class DetectionRegistry:
    """Registry of probes for multi-language detection."""
    
    def __init__(self):
        self.probes: List[BaseProbe] = [
            PythonProbe(),
            NodeProbe(),
            GoProbe()
        ]
        
    def detect_all(self, service_dir: Path, name: str) -> Optional[DetectionResult]:
        for probe in self.probes:
            result = probe.detect(service_dir, name)
            if result:
                return result
        return None


# --- Singleton for discovery ---
_registry = DetectionRegistry()


def detect_docker_compose_services(project_path: str = ".") -> Optional[List[dict]]:
    """Parse docker-compose.yml to detect services."""
    compose_path = Path(project_path) / "docker-compose.yml"
    if not compose_path.exists():
        compose_path = Path(project_path) / "docker-compose.yaml"
    
    if not compose_path.exists():
        return None
    
    try:
        with open(compose_path, "r", encoding="utf-8") as f:
            compose = yaml.safe_load(f)
    except yaml.YAMLError:
        return None
    
    if not compose or "services" not in compose:
        return None
    
    services = []
    base_port = 8000
    
    for name, config in compose.get("services", {}).items():
        if _is_infrastructure_service(name, config):
            continue
            
        build_config = config.get("build", ".")
        build_path = build_config.get("context", ".") if isinstance(build_config, dict) else str(build_config)
        
        src_path = (Path(project_path) / build_path).resolve()
        
        # Use our new registry for deep detection
        result = _registry.detect_all(src_path, name)
        
        if result:
            svc_dict = result.to_dict()
            svc_dict["path"] = build_path # Use relative path from compose
            # Override port if explicitly set in compose
            svc_dict["port"] = _extract_port(config.get("ports", []), svc_dict["port"])
            services.append(svc_dict)
        else:
            # Fallback for unrecognized languages
            services.append({
                "name": name,
                "path": build_path,
                "port": _extract_port(config.get("ports", []), base_port + len(services)),
                "framework": "other",
                "tier": "backend"
            })
    
    return services if services else None


def detect_pyproject_services(project_path: str = ".") -> Optional[List[dict]]:
    """Scan for multiple services/* directories with language indicators."""
    services = []
    project_root = Path(project_path).resolve()
    
    services_dir = project_root / "services"
    if not services_dir.exists():
        return None
    
    for service_dir in sorted(services_dir.iterdir()):
        if not service_dir.is_dir():
            continue
        
        result = _registry.detect_all(service_dir, service_dir.name)
        if result:
            svc_dict = result.to_dict()
            svc_dict["path"] = f"./services/{service_dir.name}"
            services.append(svc_dict)
            
    return services if len(services) > 1 else None


def auto_detect_services(project_path: str = ".") -> Optional[List[dict]]:
    """Try all detection methods in priority order."""
    services = detect_docker_compose_services(project_path)
    if services:
        return services
    
    services = detect_pyproject_services(project_path)
    if services:
        return services
    
    return None


# --- Helper Functions (Internal) ---

def _is_infrastructure_service(name: str, config: dict) -> bool:
    infra_names = {"db", "database", "postgres", "mysql", "redis", "mongo", "mongodb", 
                   "elasticsearch", "rabbitmq", "kafka", "zookeeper", "memcached", "nginx"}
    if name.lower() in infra_names: return True
    image = config.get("image", "")
    return any(infra in image.lower() for infra in infra_names)


def _extract_port(ports: list, default: int) -> int:
    if not ports: return default
    port_str = str(ports[0])
    if isinstance(ports[0], dict): return int(ports[0].get("published", default))
    match = re.match(r"(\d+):", port_str)
    return int(match.group(1)) if match else (int(port_str) if port_str.isdigit() else default)


def _detect_python_entrypoint(service_dir: Path, service_name: str = None) -> Optional[str]:
    """Internal helper for PythonProbe."""
    candidates = [
        ("main.py", "main:app"),
        ("app.py", "app:app"),
        ("api.py", "api:app"),
        ("wsgi.py", "wsgi:application"),
        ("asgi.py", "asgi:application"),
    ]
    
    for filename, entrypoint in candidates:
        if (service_dir / filename).exists(): return entrypoint
    
    for container_name in ["src", "app", "services"]:
        container_dir = service_dir / container_name
        if container_dir.exists() and container_dir.is_dir():
            if service_name:
                svc_subdir = container_dir / service_name
                if svc_subdir.exists():
                    for f, s in candidates:
                        if (svc_subdir / f).exists(): return f"{container_name}.{service_name}.{s}"

            for subdir in container_dir.iterdir():
                if subdir.is_dir() and not subdir.name.startswith((".", "__")):
                    for f, s in candidates:
                        if (subdir / f).exists(): return f"{container_name}.{subdir.name}.{s}"
    
    for subdir in service_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith((".", "__", "src", "app", "services", "venv", ".venv")):
            for f, s in candidates:
                if (subdir / f).exists(): return f"{subdir.name}.{s}"

    return _discover_entrypoint_by_content(service_dir)


def _scan_proactive_dependencies(service_dir: Path) -> List[str]:
    """
    Scan source code for framework-specific requirements that are often missed.
    Example: FastAPI Form/File/OAuth2 requirements.
    """
    missing = []
    patterns = [
        (r"\b(?:Form|File|OAuth2PasswordRequestForm)\b", "python-multipart"),
    ]
    
    excludes = {".venv", "venv", "tests", "__pycache__", "node_modules", ".git"}
    
    # Speed check: Read main files first
    for py_file in service_dir.rglob("*.py"):
        if any(ex in py_file.parts for ex in excludes):
            continue
            
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, dep in patterns:
                if dep not in missing and re.search(pattern, content):
                    # Check if it's already in the project's dependency files
                    if not _is_dep_already_present(service_dir, dep):
                        missing.append(dep)
        except Exception:
            continue
            
    return missing


def _is_dep_already_present(service_dir: Path, dep: str) -> bool:
    """Check if a dependency is already listed in pyproject.toml or requirements.txt."""
    for filename in ["pyproject.toml", "requirements.txt"]:
        fpath = service_dir / filename
        if fpath.exists():
            try:
                if dep.lower() in fpath.read_text().lower():
                    return True
            except Exception:
                pass
    return False


def _discover_entrypoint_by_content(service_dir: Path) -> Optional[str]:
    patterns = [
        (r"(\w+)\s*=\s*(?:fastapi\.)?FastAPI\(", "{module}:{var}"),
        (r"(\w+)\s*=\s*(?:flask\.)?Flask\(", "{module}:{var}"),
        (r"application\s*=\s*get_wsgi_application\(", "{module}:application"),
        (r"application\s*=\s*get_asgi_application\(", "{module}:application"),
    ]
    excludes = {".venv", "venv", "tests", "__pycache__", "node_modules", ".git", ".xenfra"}
    
    for py_file in service_dir.rglob("*.py"):
        if any(ex in py_file.parts for ex in excludes): continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, template in patterns:
                match = re.search(pattern, content)
                if match:
                    try:
                        rel_path = py_file.relative_to(service_dir)
                        module_path = ".".join(rel_path.with_suffix("").parts)
                        var_name = match.group(1) if match.groups() else "application"
                        return template.format(module=module_path, var=var_name)
                    except ValueError: continue
        except Exception: continue
    return None

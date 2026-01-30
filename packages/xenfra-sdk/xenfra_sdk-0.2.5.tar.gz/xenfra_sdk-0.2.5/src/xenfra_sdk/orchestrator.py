"""
Xenfra Service Orchestrator - Multi-service deployment orchestration.

This module handles the deployment of multiple services on single or multiple droplets,
coordinating the generation of docker-compose.yml, Caddyfile, and health checks.
"""

import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

import yaml

from .manifest import ServiceDefinition, load_services_from_xenfra_yaml
from . import dockerizer


class ServiceOrchestrator:
    """
    Orchestrates multi-service deployments on DigitalOcean.
    
    Supports two deployment modes:
    - single-droplet: All services on one machine with Caddy routing
    - multi-droplet: Each service on separate droplets with private networking
    """
    
    def __init__(self, engine, services: List[ServiceDefinition], project_name: str, mode: str = "single-droplet", file_manifest: List[dict] = None):
        """
        Initialize the orchestrator.
        
        Args:
            engine: InfraEngine instance
            services: List of ServiceDefinition instances
            project_name: Name of the project
            mode: Deployment mode (single-droplet or multi-droplet)
            file_manifest: List of files to be uploaded (delta upload)
        """
        self.engine = engine
        self.services = services
        self.project_name = project_name
        self.mode = mode
        self.file_manifest = file_manifest or []
        self.token = engine.token
        self.manager = engine.manager
    
    def deploy(self, logger: Callable = print, **kwargs) -> Dict:
        """
        Deploy services using the configured mode.
        
        Automatically selects between single-droplet and multi-droplet
        based on self.mode.
        """
        if self.mode == "multi-droplet":
            return self.deploy_multi_droplet(logger=logger, **kwargs)
        else:
            return self.deploy_single_droplet(logger=logger, **kwargs)
    
    def deploy_single_droplet(
        self,
        logger: Callable = print,
        **kwargs
    ) -> Dict:
        """
        Deploy all services on a single droplet with Caddy routing.
        
        This is the cost-effective option for development and small projects.
        All services run on one machine, communicating via localhost.
        
        Args:
            logger: Logging function (Rich-compatible)
            **kwargs: Additional parameters passed to InfraEngine
        
        Returns:
            Dict with deployment result:
            {
                "droplet": Droplet object,
                "services": {"svc1": True, "svc2": False, ...},
                "status": "SUCCESS" | "PARTIAL" | "FAILED",
                "url": "http://ip-address"
            }
        """
        logger(f"[bold blue]🚀 Deploying {len(self.services)} services (single-droplet mode)[/bold blue]")
        
        for svc in self.services:
            logger(f"   - {svc.name} (port {svc.port})")
        
        # Step 1: Calculate droplet size based on service count
        size = self._calculate_droplet_size()
        logger(f"\n[dim]Recommended droplet size: {size}[/dim]")
        
        # Step 2: Generate multi-service docker-compose.yml
        compose_content = self._generate_docker_compose()
        logger(f"[dim]Generated docker-compose.yml ({len(compose_content)} bytes)[/dim]")
        
        # Step 3: Generate Caddyfile for path-based routing
        caddy_content = self._generate_caddyfile()
        logger(f"[dim]Generated Caddyfile ({len(caddy_content)} bytes)[/dim]")
        
        # Step 4: Deploy using InfraEngine (with modifications for multi-service)
        # We'll use the first service's config as the base
        primary_service = self.services[0]
        
        result = {
            "droplet": None,
            "services": {},
            "status": "FAILED",
            "url": None,
            "compose_content": compose_content,
            "caddy_content": caddy_content,
        }
        
        try:
            # Use InfraEngine's deploy_server but with our multi-service assets
            
            # Helper to sanitize kwargs preventing "multiple values" TypeError
            safe_kwargs = kwargs.copy()
            explicit_args = [
                "name", "size", "framework", "port", "is_dockerized", 
                "entrypoint", "multi_service_compose", "multi_service_caddy", 
                "services", "logger", "extra_assets"
            ]
            for arg in explicit_args:
                safe_kwargs.pop(arg, None)
                
            # Generate Dockerfiles for each service
            extra_assets = {}
            for svc in self.services:
                dockerfile_name = f"Dockerfile.{svc.name}"
                
                # Check if user already provided this file (or standard Dockerfile if in subfolder)
                has_existing = False
                if self.file_manifest:
                    # Check for explicit Dockerfile.svcname
                    if any(f.get("path") in [dockerfile_name, f"./{dockerfile_name}"] for f in self.file_manifest):
                        has_existing = True
                        logger(f"   [dim]Using existing {dockerfile_name}[/dim]")
                    
                    # Check for standard Dockerfile if service has its own directory
                    elif svc.path and svc.path != ".":
                        std_path = f"{svc.path}/Dockerfile"
                        if any(f.get("path") in [std_path, f"./{std_path}"] for f in self.file_manifest):
                            # If standard Dockerfile exists in subfolder, we don't need to generate one
                            # BUT we must ensure docker-compose points to it.
                            # _generate_docker_compose forces "Dockerfile.svcname".
                            # This is a potential conflict.
                            # For now, we only skip if the EXACT filename matches what we expect.
                            pass

                if has_existing and not svc.missing_deps:
                    continue

                if has_existing and svc.missing_deps:
                    # Injection logic for existing Dockerfile
                    logger(f"   - [Zen Mode] Injecting {len(svc.missing_deps)} missing deps into existing {dockerfile_name}")
                    
                    # Find the file in manifest and get its content
                    existing_finfo = next(f for f in self.file_manifest if f.get("path") in [dockerfile_name, f"./{dockerfile_name}", f"{svc.path}/Dockerfile" if (svc.path and svc.path != ".") else "Dockerfile"])
                    from .engine import DeploymentError
                    if not self.engine.get_file_content:
                        raise DeploymentError("Cannot inject deps into existing Dockerfile: get_file_content not available", stage="Asset Generation")
                    
                    content_bytes = self.engine.get_file_content(existing_finfo["sha"])
                    content = content_bytes.decode("utf-8", errors="ignore")
                    
                    # Append injection block
                    deps_str = " ".join(svc.missing_deps)
                    injection_block = f"\n\n# --- Xenfra Zen Mode: Auto-heal missing dependencies ---\nRUN pip install --no-cache-dir {deps_str}\n"
                    
                    # If it's a multi-stage build or has entrypoint/cmd, try to insert before it
                    # otherwise just append
                    if "ENTRYPOINT" in content:
                        parts = content.split("ENTRYPOINT", 1)
                        content = parts[0] + injection_block + "ENTRYPOINT" + parts[1]
                    elif "CMD" in content:
                        parts = content.split("CMD", 1)
                        content = parts[0] + injection_block + "CMD" + parts[1]
                    else:
                        content += injection_block
                        
                    extra_assets[dockerfile_name] = content
                    continue

                # Determine command (same logic as _generate_docker_compose)
                command = svc.command
                if not command and svc.entrypoint:
                    if svc.framework == "fastapi":
                        command = f"uvicorn {svc.entrypoint} --host 0.0.0.0 --port {svc.port}"
                    elif svc.framework == "flask":
                        command = f"gunicorn {svc.entrypoint} -b 0.0.0.0:{svc.port}"
                    elif svc.framework == "django":
                        command = f"gunicorn {svc.entrypoint} --bind 0.0.0.0:{svc.port}"
                
                # Render assets using dockerizer
                ctx = {
                    "framework": svc.framework,
                    "port": svc.port,
                    "command": command,
                    "missing_deps": svc.missing_deps,
                    # Pass through other potential context
                    "database": None, 
                }
                assets = dockerizer.render_deployment_assets(ctx)
                if "Dockerfile" in assets:
                    extra_assets[dockerfile_name] = assets["Dockerfile"]
            
            if extra_assets:
                logger(f"[dim]Generated {len(extra_assets)} service Dockerfiles[/dim]")

            deployment_result = self.engine.deploy_server(
                name=self.project_name,
                size=size,
                framework=primary_service.framework,
                port=80,  # Caddy listens on 80
                is_dockerized=True,
                entrypoint=None,  # We'll use docker-compose
                # Pass multi-service config
                multi_service_compose=compose_content,
                multi_service_caddy=caddy_content,
                extra_assets=extra_assets,  # Pass generated Dockerfiles
                services=self.services,
                logger=logger,
                **safe_kwargs
            )
            
            result["droplet"] = deployment_result.get("droplet")
            result["url"] = f"http://{deployment_result.get('ip_address')}"
            
            # Step 5: Health check all services
            if result["droplet"]:
                result["services"] = self._health_check_all_services(
                    result["droplet"].ip_address,
                    logger=logger
                )
                
                # Determine overall status
                healthy_count = sum(1 for v in result["services"].values() if v)
                total_count = len(result["services"])
                
                if healthy_count == total_count:
                    result["status"] = "SUCCESS"
                    logger(f"\n[bold green]✨ All {total_count} services healthy![/bold green]")
                elif healthy_count > 0:
                    result["status"] = "PARTIAL"
                    logger(f"\n[yellow]⚠ {healthy_count}/{total_count} services healthy[/yellow]")
                else:
                    result["status"] = "FAILED"
                    logger(f"\n[bold red]❌ All services failed health check[/bold red]")
                    
        except Exception as e:
            logger(f"[bold red]Deployment failed: {e}[/bold red]")
            result["error"] = str(e)
        
        return result
    
    def _calculate_droplet_size(self) -> str:
        """
        Recommend droplet size based on number of services.
        
        Guidelines:
        - 1-2 services: s-1vcpu-2gb ($12/month)
        - 3-5 services: s-2vcpu-4gb ($24/month)
        - 6+ services: s-4vcpu-8gb ($48/month)
        """
        service_count = len(self.services)
        
        if service_count <= 2:
            return "s-1vcpu-2gb"
        elif service_count <= 5:
            return "s-2vcpu-4gb"
        else:
            return "s-4vcpu-8gb"
    
    def _generate_docker_compose(self) -> str:
        """
        Generate docker-compose.yml for all services.
        
        Each service gets:
        - Its own container
        - Port mapping
        - Environment variables
        - Restart policy
        """
        services_config = {}
        
        for svc in self.services:
            # Build command based on framework and entrypoint
            command = svc.command
            if not command and svc.entrypoint:
                if svc.framework == "fastapi":
                    command = f"uvicorn {svc.entrypoint} --host 0.0.0.0 --port {svc.port}"
                elif svc.framework == "flask":
                    command = f"gunicorn {svc.entrypoint} -b 0.0.0.0:{svc.port}"
                elif svc.framework == "django":
                    command = f"gunicorn {svc.entrypoint} --bind 0.0.0.0:{svc.port}"
            
            service_entry = {
                "build": {
                    "context": svc.path or ".",
                    "dockerfile": f"Dockerfile.{svc.name}"
                },
                "ports": [f"{svc.port}:{svc.port}"],
                "restart": "unless-stopped",
            }
            
            if command:
                service_entry["command"] = command
            
            if svc.env:
                service_entry["environment"] = svc.env
            
            services_config[svc.name] = service_entry
        
        compose = {
            "services": services_config
        }
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def _generate_caddyfile(self) -> str:
        """
        Generate Caddyfile for path-based routing.
        
        Routes:
        - /<service-name>/* → localhost:<service-port> (Strip prefix)
        - / → Gateway info page (Exact match only)
        """
        routes = []
        
        for svc in self.services:
            # handle_path strips the prefix automatically
            route = f"""    handle_path /{svc.name}* {{
        reverse_proxy localhost:{svc.port}
    }}"""
            routes.append(route)
        
        caddyfile = f""":80 {{
{chr(10).join(routes)}

    handle / {{
        respond "Xenfra Gateway - {self.project_name}" 200
    }}

    handle {{
        respond "Not Found" 404
    }}
}}"""
        
        return caddyfile
    
    def _health_check_all_services(
        self,
        ip_address: str,
        logger: Callable = print,
        max_attempts: int = 3,
        delay_seconds: int = 10
    ) -> Dict[str, bool]:
        """
        Check health of all services via their routed paths.
        
        Args:
            ip_address: Droplet IP address
            logger: Logging function
            max_attempts: Number of retry attempts per service
            delay_seconds: Delay between retries
        
        Returns:
            Dict mapping service name → healthy (bool)
        """
        import requests
        
        results = {}
        
        logger("\n[cyan]Running health checks...[/cyan]")
        
        for svc in self.services:
            endpoint = f"http://{ip_address}/{svc.name}/"
            healthy = False
            
            for attempt in range(max_attempts):
                try:
                    response = requests.get(endpoint, timeout=5)
                    # Accept any HTTP response as healthy (200, 404, 500, etc.)
                    if response.status_code >= 100:
                        healthy = True
                        logger(f"   ✓ {svc.name} (port {svc.port})")
                        break
                except requests.RequestException:
                    pass
                
                if attempt < max_attempts - 1:
                    time.sleep(delay_seconds)
            
            if not healthy:
                logger(f"   ✗ {svc.name} (port {svc.port}) - failed")
            
            results[svc.name] = healthy
        
        return results
    
    def deploy_multi_droplet(self, logger: Callable = print, **kwargs) -> Dict:
        """
        Deploy each service on its own droplet with private networking.
        
        This is the scalable option for production workloads.
        Each service runs on a dedicated droplet with private IP communication.
        
        Architecture:
        - Gateway droplet: Runs Caddy and routes traffic to service droplets
        - Service droplets: Each runs one service, accessible via private IP
        
        Returns:
            Dict with deployment result:
            {
                "gateway": Droplet object,
                "droplets": {"svc1": Droplet, "svc2": Droplet, ...},
                "services": {"svc1": True, "svc2": False, ...},
                "status": "SUCCESS" | "PARTIAL" | "FAILED",
                "url": "http://gateway-ip"
            }
        """
        logger(f"[bold blue]🚀 Deploying {len(self.services)} services (multi-droplet mode)[/bold blue]")
        
        for svc in self.services:
            logger(f"   - {svc.name} (port {svc.port})")
        
        logger(f"\n[dim]This will create {len(self.services) + 1} droplets (1 gateway + {len(self.services)} services)[/dim]")
        
        result = {
            "gateway": None,
            "droplets": {},
            "private_ips": {},
            "services": {},
            "status": "FAILED",
            "url": None,
        }
        
        created_droplets = []
        cleanup_on_failure = kwargs.get("cleanup_on_failure", False)
        
        try:
            # Step 1: Deploy each service on its own droplet
            logger("\n[bold cyan]Phase 1: Deploying service droplets[/bold cyan]")
            
            # Common sanitization for service droplets
            service_kwargs = kwargs.copy()
            for key in ["name", "size", "framework", "port", "is_dockerized", "entrypoint", "multi_service_compose", "logger", "extra_assets"]:
                service_kwargs.pop(key, None)

            for svc in self.services:
                logger(f"\n[cyan]Deploying {svc.name}...[/cyan]")
                
                # Generate single-service docker-compose
                compose_content = self._generate_single_service_compose(svc)
                
                try:
                    droplet_result = self.engine.deploy_server(
                        name=f"{self.project_name}-{svc.name}",
                        size="s-1vcpu-1gb",  # Minimal size per service
                        framework=svc.framework,
                        port=svc.port,
                        is_dockerized=True,
                        entrypoint=svc.entrypoint,
                        multi_service_compose=compose_content,
                        logger=logger,
                        **service_kwargs
                    )
                    
                    droplet = droplet_result.get("droplet")
                    if droplet:
                        result["droplets"][svc.name] = droplet
                        created_droplets.append(droplet)
                        
                        # Get private IP for internal routing
                        private_ip = self._get_private_ip(droplet)
                        result["private_ips"][svc.name] = private_ip or droplet.ip_address
                        if not private_ip:
                            logger(f"[yellow]   Start Up Warning: No private IP found for {svc.name}. Routing will use public IP.[/yellow]")
                        
                        logger(f"   [green]✓ {svc.name} deployed at {droplet.ip_address}[/green]")
                    else:
                        logger(f"   [red]✗ {svc.name} deployment failed[/red]")
                        
                except Exception as e:
                    logger(f"   [red]✗ {svc.name} failed: {e}[/red]")
                    # If a service fails, we continue best-effort deployment for now
                    # But status will reflect failure.
            
            # Step 2: Deploy gateway droplet with Caddy routing
            logger("\n[bold cyan]Phase 2: Deploying gateway droplet[/bold cyan]")
            
            if result["private_ips"]:
                # Generate Caddyfile pointing to private IPs
                caddy_content = self._generate_multi_droplet_caddyfile(result["private_ips"])
                
                # Sanitize kwargs for Gateway deployment
                gateway_kwargs = kwargs.copy()
                for key in ["name", "size", "framework", "port", "is_dockerized", "multi_service_caddy", "install_caddy", "logger"]:
                    gateway_kwargs.pop(key, None)

                gateway_result = self.engine.deploy_server(
                    name=f"{self.project_name}-gateway",
                    size="s-1vcpu-1gb",  # Gateway is lightweight
                    framework="other",
                    port=80,
                    is_dockerized=False,  # Gateway runs Caddy directly
                    multi_service_caddy=caddy_content,
                    install_caddy=True,  # Ensure Caddy is installed on host
                    logger=logger,
                    **gateway_kwargs
                )
                
                gateway = gateway_result.get("droplet")
                if gateway:
                    result["gateway"] = gateway
                    created_droplets.append(gateway)
                    result["url"] = f"http://{gateway.ip_address}"
                    logger(f"   [green]✓ Gateway deployed at {gateway.ip_address}[/green]")
            
            # Step 3: Health check all services via gateway
            logger("\n[bold cyan]Phase 3: Health checks[/bold cyan]")
            
            if result["gateway"]:
                result["services"] = self._health_check_all_services(
                    result["gateway"].ip_address,
                    logger=logger
                )
                
                # Determine overall status
                healthy_count = sum(1 for v in result["services"].values() if v)
                total_count = len(result["services"])
                
                if healthy_count == total_count:
                    result["status"] = "SUCCESS"
                    logger(f"\n[bold green]✨ All {total_count} services healthy![/bold green]")
                elif healthy_count > 0:
                    result["status"] = "PARTIAL"
                    logger(f"\n[yellow]⚠ {healthy_count}/{total_count} services healthy[/yellow]")
                else:
                    result["status"] = "FAILED"
                    logger(f"\n[bold red]❌ All services failed health check[/bold red]")
            else:
                result["status"] = "FAILED"
                logger("\n[bold red]❌ Gateway deployment failed[/bold red]")
                
        except Exception as e:
            logger(f"[bold red]Multi-droplet deployment failed: {e}[/bold red]")
            result["error"] = str(e)
            
            if cleanup_on_failure:
                logger("[bold yellow]Cleaning up created resources...[/bold yellow]")
                for d in created_droplets:
                    try:
                        logger(f"   - Destroying droplet {d.name} ({d.id})...")
                        d.destroy()
                    except Exception as cleanup_err:
                        logger(f"   - Failed to destroy {d.id}: {cleanup_err}")
            else:
                 logger("[yellow]Resource cleanup skipped (cleanup_on_failure=False). Orphaned droplets may exist.[/yellow]")
        
        return result
    
    def _generate_single_service_compose(self, svc: ServiceDefinition) -> str:
        """Generate docker-compose.yml for a single service."""
        command = svc.command
        if not command and svc.entrypoint:
            if svc.framework == "fastapi":
                command = f"uvicorn {svc.entrypoint} --host 0.0.0.0 --port {svc.port}"
            elif svc.framework == "flask":
                command = f"gunicorn {svc.entrypoint} -b 0.0.0.0:{svc.port}"
            elif svc.framework == "django":
                command = f"gunicorn {svc.entrypoint} --bind 0.0.0.0:{svc.port}"
        
        service_entry = {
            "build": svc.path or ".",
            "ports": [f"{svc.port}:{svc.port}"],
            "restart": "unless-stopped",
        }
        
        if command:
            service_entry["command"] = command
        
        if svc.env:
            service_entry["environment"] = svc.env
        
        compose = {
            "services": {
                svc.name: service_entry
            }
        }
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)
    
    def _generate_multi_droplet_caddyfile(self, private_ips: Dict[str, str]) -> str:
        """
        Generate Caddyfile for multi-droplet routing.
        
        Routes traffic to service droplets via their private IPs.
        Includes 404 fallback to prevent false positive health checks.
        """
        routes = []
        
        for svc in self.services:
            ip = private_ips.get(svc.name)
            if ip:
                route = f"""    handle_path /{svc.name}* {{
        reverse_proxy {ip}:{svc.port}
    }}"""
                routes.append(route)
        
        caddyfile = f""":80 {{
{chr(10).join(routes)}

    # Root page
    handle / {{
        respond "Xenfra Gateway - {self.project_name}" 200
    }}

    # Fallback for unmatched routes (prevents false positive health checks)
    handle {{
        respond "Not Found" 404
    }}
}}"""
        
        return caddyfile
    
    def _get_private_ip(self, droplet) -> Optional[str]:
        """Get private IP of droplet if available."""
        try:
            for network in droplet.networks.get("v4", []):
                if network.get("type") == "private":
                    return network.get("ip_address")
        except (AttributeError, KeyError):
            pass
        return None


def get_orchestrator_for_project(engine, project_path: str = ".") -> Optional[ServiceOrchestrator]:
    """
    Factory function to create an orchestrator if xenfra.yaml has services.
    
    Args:
        engine: InfraEngine instance
        project_path: Path to project directory
    
    Returns:
        ServiceOrchestrator if services found in xenfra.yaml, None otherwise
    """
    from .manifest import load_services_from_xenfra_yaml, get_deployment_mode
    
    services = load_services_from_xenfra_yaml(project_path)
    
    if services and len(services) > 1:
        # Get project name from xenfra.yaml
        yaml_path = Path(project_path) / "xenfra.yaml"
        project_name = Path(project_path).name
        mode = "single-droplet"
        
        if yaml_path.exists():
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
                project_name = data.get("project_name", project_name)
                mode = data.get("mode", "single-droplet")
        
        return ServiceOrchestrator(engine, services, project_name, mode)
    
    return None

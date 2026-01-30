# src/xenfra/engine.py

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import digitalocean
import fabric
from dotenv import load_dotenv
from sqlmodel import Session, select

import shutil
import subprocess

# Xenfra modules
from . import dockerizer, recipes
from .db.models import Project
from .db.session import get_session


class DeploymentError(Exception):
    """Custom exception for deployment failures."""

    def __init__(self, message, stage="Unknown"):
        self.message = message
        self.stage = stage
        super().__init__(f"Deployment failed at stage '{stage}': {message}")


class InfraEngine:
    """
    The InfraEngine is the core of Xenfra. It handles all interactions
    with the cloud provider and orchestrates the deployment lifecycle.
    """

    def __init__(self, token: str = None, db_session: Session = None):
        """
        Initializes the engine and validates the API token.
        """
        load_dotenv()
        self.token = token or os.getenv("DIGITAL_OCEAN_TOKEN")
        self.db_session = db_session or next(get_session())

        if not self.token:
            raise ValueError(
                "DigitalOcean API token not found. Please set the DIGITAL_OCEAN_TOKEN environment variable."
            )
        try:
            self.manager = digitalocean.Manager(token=self.token)
            self.get_user_info()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to DigitalOcean: {e}")

    def _get_connection(self, ip_address: str):
        """Establishes a Fabric connection to the server."""
        private_key_path = str(Path.home() / ".ssh" / "id_rsa")
        if not Path(private_key_path).exists():
            raise DeploymentError("No private SSH key found at ~/.ssh/id_rsa.", stage="Setup")

        return fabric.Connection(
            host=ip_address,
            user="root",
            connect_kwargs={"key_filename": [private_key_path]},
        )

    def get_user_info(self):
        """Retrieves user account information."""
        return self.manager.get_account()

    def list_servers(self):
        """Retrieves a list of all Droplets."""
        return self.manager.get_all_droplets()

    def list_domains(self):
        """Retrieves a list of all domains from DigitalOcean."""
        return self.manager.get_all_domains()

    def destroy_server(self, droplet_id: int, db_session: Session = None):
        """
        Idempotent droplet destruction.

        Destroys the droplet and removes DB records. Handles 404 errors gracefully
        (if droplet already destroyed, continues to DB cleanup).
        """
        session = db_session or self.db_session

        # Find the project in the local DB
        statement = select(Project).where(Project.droplet_id == droplet_id)
        project_to_delete = session.exec(statement).first()

        # Destroy the droplet on DigitalOcean (handle 404 gracefully)
        try:
            droplet = digitalocean.Droplet(token=self.token, id=droplet_id)
            droplet.destroy()
        except Exception as e:
            # If 404, droplet already gone - that's OK
            error_str = str(e).lower()
            if "404" in error_str or "not found" in error_str:
                pass  # Continue to DB cleanup
            else:
                raise  # Unexpected error

        # If it was in our DB, delete it
        if project_to_delete:
            session.delete(project_to_delete)
            session.commit()

    def list_projects_from_db(self, db_session: Session = None):
        """Lists all projects from the local database."""
        session = db_session or self.db_session
        statement = select(Project)
        return session.exec(statement).all()

    def sync_with_provider(self, user_id: int, db_session: Session = None):
        """Reconciles the local database with the live state from DigitalOcean for a specific user."""
        session = db_session or self.db_session

        # 1. Get live and local states
        # Filter by 'xenfra' tag to only manage droplets created by us
        live_droplets = self.manager.get_all_droplets(tag_name="xenfra")
        
        # Filter local projects by user_id
        statement = select(Project).where(Project.user_id == user_id)
        local_projects = session.exec(statement).all()

        live_map = {d.id: d for d in live_droplets}
        local_map = {p.droplet_id: p for p in local_projects}

        # 2. Reconcile
        # Add new servers found on DO to our DB if they match our naming/tagging convention
        for droplet_id, droplet in live_map.items():
            if droplet_id not in local_map:
                # We only add it if it's NOT in our DB yet. 
                # Note: In a multi-tenant environment, we'd need a way to know WHICH user
                # owns a tagged droplet if it's not in our DB. For now, we assume the 
                # calling user potentially owns it if they are syncing.
                new_project = Project(
                    droplet_id=droplet.id,
                    name=droplet.name,
                    ip_address=droplet.ip_address,
                    status=droplet.status,
                    region=droplet.region["slug"],
                    size=droplet.size_slug,
                    user_id=user_id,
                )
                session.add(new_project)

        # Remove servers from our DB that no longer exist on DO
        for droplet_id, project in local_map.items():
            if droplet_id not in live_map:
                session.delete(project)

        session.commit()
        
        # Return refreshed list for this user
        statement = select(Project).where(Project.user_id == user_id)
        return session.exec(statement).all()

    def stream_logs(self, droplet_id: int, db_session: Session = None):
        """
        Verifies a server exists and streams its logs in real-time.
        """
        session = db_session or self.db_session

        # 1. Find project in local DB
        statement = select(Project).where(Project.droplet_id == droplet_id)
        project = session.exec(statement).first()
        if not project:
            raise DeploymentError(
                f"Project with Droplet ID {droplet_id} not found in local database.",
                stage="Log Streaming",
            )

        # 2. Just-in-Time Verification
        try:
            droplet = self.manager.get_droplet(droplet_id)
        except digitalocean.baseapi.DataReadError as e:
            if e.response.status_code == 404:
                # The droplet doesn't exist, so remove it from our DB
                session.delete(project)
                session.commit()
                raise DeploymentError(
                    f"Server '{project.name}' (ID: {droplet_id}) no longer exists on DigitalOcean. It has been removed from your local list.",
                    stage="Log Streaming",
                )
            else:
                raise e

        # 3. Stream logs
        ip_address = droplet.ip_address
        with self._get_connection(ip_address) as conn:
            conn.run("cd /root/app && docker compose logs -f app", pty=True)

    def get_account_balance(self) -> dict:
        """
        Retrieves the current account balance from DigitalOcean.
        Placeholder: Actual implementation needed.
        """
        # In a real scenario, this would call the DigitalOcean API for billing info
        # For now, return mock data
        return {
            "month_to_date_balance": "0.00",
            "account_balance": "0.00",
            "month_to_date_usage": "0.00",
            "generated_at": datetime.now().isoformat(),
        }

    def get_droplet_cost_estimates(self) -> list:
        """
        Retrieves a list of Xenfra-managed DigitalOcean droplets with their estimated monthly costs.
        Placeholder: Actual implementation needed.
        """
        # In a real scenario, this would list droplets and calculate costs
        # For now, return mock data
        return []

    def _ensure_ssh_key(self, logger):
        """Ensures a local public SSH key is on DigitalOcean. Generates one if missing (Zen Mode)."""
        pub_key_path = Path.home() / ".ssh" / "id_rsa.pub"
        priv_key_path = Path.home() / ".ssh" / "id_rsa"
        
        if not pub_key_path.exists():
            logger("   - [Zen Mode] No SSH key found at ~/.ssh/id_rsa.pub. Generating a new one...")
            try:
                # Ensure .ssh directory exists
                pub_key_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Generate RSA keypair without passphrase
                subprocess.run(
                    ["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", str(priv_key_path)],
                    check=True,
                    capture_output=True
                )
                logger("   - [Zen Mode] Successfully generated SSH keypair.")
            except Exception as e:
                logger(f"   - [ERROR] Failed to generate SSH key: {e}")
                raise DeploymentError(
                    f"Could not find or generate SSH key: {e}", stage="Setup"
                )

        with open(pub_key_path) as f:
            pub_key_content = f.read()

        # Check if the key is already on DigitalOcean
        existing_keys = self.manager.get_all_sshkeys()
        for key in existing_keys:
            if key.public_key.strip() == pub_key_content.strip():
                logger("   - Found existing SSH key on DigitalOcean.")
                return key

        logger("   - No matching SSH key found on provider. Registering new key...")
        # Use a descriptive name including hostname if possible
        import socket
        key_name = f"xenfra-key-{socket.gethostname()}"
        key = digitalocean.SSHKey(
            token=self.token, name=key_name, public_key=pub_key_content
        )
        key.create()
        return key

    def deploy_server(
        self,
        name: str,
        region: str = "nyc3",
        size: str = "s-1vcpu-1gb",
        image: str = "ubuntu-22-04-x64",
        logger: Optional[callable] = None,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        domain: Optional[str] = None,
        repo_url: Optional[str] = None,
        is_dockerized: bool = True,
        db_session: Session = None,
        port: int = 8000,
        command: str = None,
        entrypoint: str = None,  # e.g., "todo.main:app"
        database: str = None,
        package_manager: str = None,
        dependency_file: str = None,
        file_manifest: list = None,  # Delta upload: [{path, sha, size}, ...]
        get_file_content: callable = None,  # Function to get file content by SHA
        cleanup_on_failure: bool = False,  # Auto-cleanup resources on failure
        extra_assets: Dict[str, str] = None,  # Additional files to write (e.g. Dockerfiles)
        # Multi-service deployment (from ServiceOrchestrator)
        multi_service_compose: str = None,  # Pre-generated docker-compose.yml for multi-service
        multi_service_caddy: str = None,  # Pre-generated Caddyfile for multi-service routing
        services: list = None,  # List of ServiceDefinition for multi-service deployments
        **kwargs,
    ):
        """A stateful, blocking orchestrator for deploying a new server."""
        droplet = None
        session = db_session or self.db_session
        branch = kwargs.get("branch", "main")  # Extract branch from kwargs
        framework = kwargs.get("framework")  # Extract framework from kwargs
        
        try:
            # === 0. MICROSERVICES DELEGATION ===
            # If services are provided but no pre-generated assets, delegate to Orchestrator
            if services and not (multi_service_compose or multi_service_caddy):
                logger("\n[bold magenta]MICROSERVICES DETECTED - Delegating to ServiceOrchestrator[/bold magenta]")
                from .orchestrator import ServiceOrchestrator, load_services_from_xenfra_yaml
                from .manifest import create_services_from_detected
                
                # Convert dicts to ServiceDefinition objects if needed
                service_objs = []
                if services and isinstance(services[0], dict):
                    service_objs = create_services_from_detected(services)
                else:
                    service_objs = services
                
                # Determine mode (can be passed in kwargs or default to single-droplet)
                mode = kwargs.get("mode", "single-droplet")
                
                orchestrator = ServiceOrchestrator(
                    engine=self,
                    services=service_objs,
                    project_name=name,
                    mode=mode,
                    file_manifest=file_manifest
                )
                
                return orchestrator.deploy(
                    logger=logger,
                    # Pass all original arguments to ensure they propagate
                    region=region,
                    size=size,
                    image=image,
                    user_id=user_id,
                    email=email,
                    domain=domain,
                    repo_url=repo_url,
                    is_dockerized=is_dockerized,
                    db_session=db_session,
                    port=port,
                    command=command,
                    entrypoint=entrypoint,
                    database=database,
                    package_manager=package_manager,
                    dependency_file=dependency_file,
                    file_manifest=file_manifest,
                    get_file_content=get_file_content,
                    cleanup_on_failure=cleanup_on_failure,
                    extra_assets=extra_assets,
                    **kwargs
                )

            # === 0. EARLY VALIDATION ===
            # Check code source BEFORE creating droplet
            has_code_source = repo_url or (file_manifest and get_file_content)
            if os.getenv("XENFRA_SERVICE_MODE") == "true" and not has_code_source:
                raise DeploymentError(
                    "No code source provided. Use git_repo URL or upload files first. "
                    "Local folder deployment is not supported via the cloud API.",
                    stage="Validation",
                )
            
            # === 1. SETUP STAGE ===
            logger("\n[bold blue]PHASE 1: SETUP[/bold blue]")
            ssh_key = self._ensure_ssh_key(logger)

            # === 2. ASSET GENERATION STAGE ===
            logger("\n[bold blue]PHASE 2: GENERATING DEPLOYMENT ASSETS[/bold blue]")
            
            # Detect Python version from project files if using delta upload
            python_version = "python:3.11-slim"  # Default
            if file_manifest and get_file_content:
                # Build file info with content for version detection
                version_files = []
                for finfo in file_manifest:
                    path = finfo.get('path', '')
                    if path in ['.python-version', 'pyproject.toml']:
                        content = get_file_content(finfo.get('sha', ''))
                        if content:
                            version_files.append({
                                'path': path,
                                'content': content.decode('utf-8', errors='ignore')
                            })
                
                if version_files:
                    python_version = dockerizer.detect_python_version(version_files)
                    logger(f"   - Detected Python version: {python_version}")
            
            context = {
                "email": email,
                "domain": domain,
                "repo_url": repo_url,
                "port": port or 8000,
                "command": command,
                "entrypoint": entrypoint,  # Pass entrypoint to templates (e.g., "todo.main:app")
                "database": database,
                "package_manager": package_manager or "pip",
                "dependency_file": dependency_file or "requirements.txt",
                "framework": framework,  # Explicitly include framework
                "python_version": python_version,  # Auto-detected or default
                **kwargs,  # Pass any additional config
            }
            
            # Check if this is a multi-service deployment
            if multi_service_compose:
                # Use pre-generated assets from ServiceOrchestrator
                logger("   - Using multi-service configuration")
                rendered_assets = {
                    "docker-compose.yml": multi_service_compose,
                }
                if multi_service_caddy:
                    rendered_assets["Caddyfile"] = multi_service_caddy
                    logger(f"   - Caddyfile for {len(services) if services else 0} services")
            else:
                # Render templates to strings (NOT written to disk) - single service
                rendered_assets = dockerizer.render_deployment_assets(context)
                if not rendered_assets:
                    raise DeploymentError("Failed to render deployment assets. Is framework specified?", stage="Asset Generation")
            
            # Merge extra assets (like service-specific Dockerfiles)
            if extra_assets:
                rendered_assets.update(extra_assets)
                logger(f"   - Included {len(extra_assets)} extra assets")
            
            for filename in rendered_assets:
                logger(f"   - Rendered {filename} ({len(rendered_assets[filename])} bytes)")

            # === 3. CLOUD-INIT STAGE ===
            logger("\n[bold blue]PHASE 3: CREATING SERVER SETUP SCRIPT[/bold blue]")
            cloud_init_script = recipes.generate_stack(context, is_dockerized=is_dockerized)
            logger("   - Generated cloud-init script.")
            logger(
                f"--- Cloud-init script content ---\n{cloud_init_script}\n---------------------------------"
            )

            # === 4. DROPLET CREATION STAGE ===
            logger("\n[bold blue]PHASE 4: PROVISIONING SERVER[/bold blue]")
            
            # Machine Reuse: Look for existing droplet with same name and 'xenfra' tag
            existing_droplets = digitalocean.Manager(token=self.token).get_all_droplets(tag_name="xenfra")
            droplet = next((d for d in existing_droplets if d.name == name), None)
            
            if droplet and droplet.status == "active":
                logger(f"   - Found existing active droplet '{name}' (ID: {droplet.id}). Reusing machine...")
            else:
                if droplet:
                    logger(f"   - Found existing droplet '{name}' but it's not active ({droplet.status}). Creating new one...")
                
                droplet = digitalocean.Droplet(
                    token=self.token,
                    name=name,
                    region=region,
                    image=image,
                    size_slug=size,
                    ssh_keys=[ssh_key.id],
                    user_data=cloud_init_script,
                    tags=["xenfra"],
                    private_networking=True,
                )
                droplet.create()
                logger(
                    f"   - Droplet '{name}' creation initiated (ID: {droplet.id}). Waiting for it to become active..."
                )

            # === 5. POLLING STAGE ===
            logger("\n[bold blue]PHASE 5: WAITING FOR SERVER SETUP[/bold blue]")
            while True:
                droplet.load()
                if droplet.status == "active":
                    logger("   - Droplet is active. Waiting for SSH to be available...")
                    break
                time.sleep(10)

            ip_address = droplet.ip_address

            # Retry SSH connection
            conn = None
            max_retries = 12  # 2-minute timeout for SSH
            for i in range(max_retries):
                try:
                    logger(f"   - Attempting SSH connection ({i + 1}/{max_retries})...")
                    conn = self._get_connection(ip_address)
                    conn.open()  # Explicitly open the connection
                    logger("   - SSH connection established.")
                    break
                except Exception as e:
                    if i < max_retries - 1:
                        logger("   - SSH connection failed. Retrying in 10s...")
                        time.sleep(10)
                    else:
                        raise DeploymentError(
                            f"Failed to establish SSH connection: {e}", stage="Polling"
                        )

            if not conn or not conn.is_connected:
                raise DeploymentError("Could not establish SSH connection.", stage="Polling")

            logger("   - [DEBUG] Entering SSH context for Phase 5 polling...")
            with conn:
                last_log_line = 0
                logger("   - Polling server setup log (/root/setup.log)...")
                for i in range(120):  # 20-minute timeout
                    # Heartbeat
                    if i % 3 == 0:  # Every 30 seconds
                        logger(f"   - Phase 5 Heartbeat: Waiting for setup completion ({i+1}/120)...")

                    # Check for completion with timeout
                    try:
                        check_result = conn.run("test -f /root/setup_complete", warn=True, hide=True, timeout=10)
                        if check_result.ok:
                            logger("   - Cloud-init setup complete.")
                            break
                    except Exception as e:
                        logger(f"   - [Warning] Status check failed: {e}. Retrying...")
                    
                    # Tail the setup log for visibility
                    try:
                        log_result = conn.run(f"tail -n +{last_log_line + 1} /root/setup.log 2>/dev/null", warn=True, hide=True, timeout=10)
                        if log_result.ok and log_result.stdout.strip():
                            new_lines = log_result.stdout.strip().split("\n")
                            for line in new_lines:
                                if line.strip():
                                    logger(f"     [Server Setup] {line.strip()}")
                            last_log_line += len(new_lines)
                    except Exception as e:
                        # Log doesn't exist yet or tail failed
                        pass

                    time.sleep(10)
                else:
                    raise DeploymentError(
                        "Server setup script failed to complete in time.", stage="Polling"
                    )

            # === 6. CODE UPLOAD STAGE ===
            logger("\n[bold blue]PHASE 6: UPLOADING APPLICATION CODE[/bold blue]")
            with self._get_connection(ip_address) as conn:
                # Option 1: Git clone (if repo_url provided)
                if repo_url:
                    logger(f"   - Cloning repository from {repo_url} (branch: {branch})...")
                    # Use --branch to checkout specific branch, --single-branch for efficiency
                    clone_cmd = f"git clone --branch {branch} --single-branch {repo_url} /root/app"
                    result = conn.run(clone_cmd, warn=True, hide=True)
                    if result.failed:
                        # Try without --single-branch in case branch doesn't exist
                        # Clean up any partial clone first
                        logger(f"   - Branch '{branch}' clone failed, trying default branch...")
                        conn.run("rm -rf /root/app", warn=True, hide=True)
                        conn.run(f"git clone {repo_url} /root/app")
                
                # Option 2: Delta upload (if file_manifest provided)
                elif file_manifest and get_file_content:
                    logger(f"   - Syncing {len(file_manifest)} files via delta upload...")
                    
                    # Ensure /root/app exists
                    conn.run("mkdir -p /root/app", hide=True)
                    
                    for i, file_info in enumerate(file_manifest):
                        path = file_info['path']
                        sha = file_info['sha']
                        size = file_info.get('size', 0)
                        
                        # Build Safety: Placeholder for 0-byte critical files
                        # (Hatchling/Pip fail if README.md or __init__.py are mentioned but empty)
                        is_critical_empty = (
                            size == 0 and 
                            (path.lower() == 'readme.md' or path.endswith('__init__.py'))
                        )
                        
                        # Smart Incremental Sync: Check if file exists and has same SHA
                        remote_path = f"/root/app/{path}"
                        check_sha_cmd = f"sha256sum {remote_path}"
                        result = conn.run(check_sha_cmd, warn=True, hide=True)
                        
                        if result.ok:
                            remote_sha = result.stdout.split()[0]
                            if remote_sha == sha and not is_critical_empty:
                                # File already exists and matches, skip upload
                                continue

                        # Get file content from storage
                        content = get_file_content(sha)
                        if content is None:
                            raise DeploymentError(f"File not found in storage: {path} (sha: {sha})", stage="Code Upload")
                        
                        # Apply placeholder if critical and empty
                        if is_critical_empty:
                            content = b"# xenfra placeholder\n"
                            logger(f"   - [Zen Mode] Injected placeholder into empty {path}")

                        # Create directory if needed
                        dir_path = os.path.dirname(path)
                        if dir_path:
                            conn.run(f"mkdir -p /root/app/{dir_path}", warn=True, hide=True)
                        
                        # Use SFTP for file transfer (handles large files)
                        from io import BytesIO
                        conn.put(BytesIO(content), remote_path)
                        
                        # Progress update every 10 files
                        if (i + 1) % 10 == 0 or i == len(file_manifest) - 1:
                            logger(f"   - Synced {i + 1}/{len(file_manifest)} files...")
                    
                    logger(f"   - All {len(file_manifest)} files synced.")
                
                # Option 3: Local rsync (only works locally, not in service mode)
                else:
                    # Note: Early validation in Phase 0 should have caught this for service mode
                    private_key_path = str(Path.home() / ".ssh" / "id_rsa")
                    rsync_cmd = f'rsync -avz --exclude=".git" --exclude=".venv" --exclude="__pycache__" -e "ssh -i {private_key_path} -o StrictHostKeyChecking=no" . root@{ip_address}:/root/app/'
                    logger(f"   - Uploading local code via rsync...")
                    result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise DeploymentError(f"rsync failed: {result.stderr}", stage="Code Upload")
            logger("   - Code upload complete.")

            
            # === 6.5. WRITE DEPLOYMENT ASSETS TO DROPLET ===
            logger("\n[bold blue]PHASE 6.5: WRITING DEPLOYMENT ASSETS[/bold blue]")
            with self._get_connection(ip_address) as conn:
                for filename, content in rendered_assets.items():
                    # Use heredoc with unique delimiter to write file content
                    # Single-quoted delimiter prevents shell variable expansion
                    logger(f"   - Writing {filename}...")
                    try:
                        # Use base64 encoding to safely transfer file content
                        # Use printf to avoid issues with special characters
                        import base64
                        encoded_content = base64.b64encode(content.encode()).decode()
                        # Use printf with %s to handle any special characters in base64
                        conn.run(f"printf '%s' '{encoded_content}' | base64 -d > /root/app/{filename}")
                    except Exception as e:
                        raise DeploymentError(f"Failed to write {filename}: {e}", stage="Asset Write")
            logger("   - Deployment assets written.")

            # === 7. FINAL DEPLOY STAGE ===
            if is_dockerized:
                logger("\n[bold blue]PHASE 7: BUILDING AND DEPLOYING CONTAINERS[/bold blue]")
                with self._get_connection(ip_address) as conn:
                    # Force --no-cache to ensure updated files (like README.md placeholders) are used
                    result = conn.run("cd /root/app && docker compose build --no-cache && docker compose up -d", hide=True)
                    if result.failed:
                        raise DeploymentError(f"docker-compose failed: {result.stderr}", stage="Deploy")
                logger("   - Docker build complete, containers starting...")
            else:
                logger("\n[bold blue]PHASE 7: STARTING HOST-BASED APPLICATION[/bold blue]")
                start_command = context.get("command", f"uvicorn main:app --port {context.get('port', 8000)}")
                with self._get_connection(ip_address) as conn:
                    result = conn.run(f"cd /root/app && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && nohup .venv/bin/{start_command} > app.log 2>&1 &", hide=True)
                    if result.failed:
                        raise DeploymentError(f"Host-based start failed: {result.stderr}", stage="Deploy")
                logger(f"   - Application started via: {start_command}")

            # Multi-service: Configure Caddy for path-based routing (Gateway or Single-Droplet)
            if multi_service_caddy:
                logger("   - Configuring Caddy for multi-service routing...")
                with self._get_connection(ip_address) as conn:
                    # Write Caddyfile to Caddy's config directory
                    import base64
                    encoded_caddy = base64.b64encode(multi_service_caddy.encode()).decode()
                    conn.run(f"printf '%s' '{encoded_caddy}' | base64 -d > /etc/caddy/Caddyfile", warn=True)
                    # Reload Caddy to pick up new config
                    conn.run("systemctl reload caddy || systemctl restart caddy", warn=True)
                logger("   - Caddy configured for path-based routing")

            # === 8. VERIFICATION STAGE ===
            logger("\n[bold blue]PHASE 8: VERIFYING DEPLOYMENT[/bold blue]")
            
            # Give container a moment to initialize before first health check
            time.sleep(5)
            
            app_port = context.get("port", 8000)
            for i in range(24):  # 2-minute timeout for health checks
                logger(f"   - Health check attempt {i + 1}/24...")
                with self._get_connection(ip_address) as conn:
                    # Check if running
                    if is_dockerized:
                        ps_result = conn.run("cd /root/app && docker compose ps", hide=True)
                        ps_output = ps_result.stdout.lower()
                        # Docker Compose V1 shows "running", V2 shows "Up" in status
                        running = "running" in ps_output or " up " in ps_output
                        if "restarting" in ps_output:
                            logs = conn.run("cd /root/app && docker compose logs --tail 20", hide=True).stdout
                            raise DeploymentError(f"Application is crash-looping (restarting). Logs:\n{logs}", stage="Verification")
                    else:
                        ps_result = conn.run("ps aux | grep -v grep | grep python", hide=True)
                        running = ps_result.ok and len(ps_result.stdout.strip()) > 0

                    if not running:
                        time.sleep(5)
                        continue

                    # Check if application is responsive (port is listening)
                    # Accept ANY HTTP response (including 404) - it means the app is running
                    # Use curl with -w to get HTTP code, accept any response >= 100
                    port_check = conn.run(
                        f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 3 http://localhost:{app_port}/",
                        warn=True, hide=True
                    )
                    # curl may exit non-zero for 404, but still outputs HTTP code
                    http_code = port_check.stdout.strip()
                    
                    # Any HTTP response (200, 404, 500, etc.) means app is running
                    if http_code.isdigit() and int(http_code) >= 100:

                        logger(
                            "[bold green]   - Health check passed! Application is live.[/bold green]"
                        )

                        # === 9. PERSISTENCE STAGE ===
                        logger("\n[bold blue]PHASE 9: SAVING DEPLOYMENT TO DATABASE[/bold blue]")
                        project = Project(
                            droplet_id=droplet.id,
                            name=droplet.name,
                            ip_address=ip_address,
                            status=droplet.status,
                            region=droplet.region["slug"],
                            size=droplet.size_slug,
                            user_id=user_id,  # Save the user_id
                        )
                        session.add(project)
                        session.commit()
                        logger("   - Deployment saved.")

                        return droplet  # Return the full droplet object
                time.sleep(5)
            else:
                # Capture logs on timeout failure
                with self._get_connection(ip_address) as conn:
                    logs = conn.run("cd /root/app && docker compose logs --tail 50", hide=True, warn=True).stdout if is_dockerized else ""
                raise DeploymentError(f"Application failed to become healthy in time. Logs:\n{logs}", stage="Verification")

        except Exception as e:
            if droplet:
                if cleanup_on_failure:
                    logger("[bold yellow]Cleaning up resources...[/bold yellow]")
                    try:
                        # 1. Destroy droplet (DigitalOcean API)
                        logger(f"   - Destroying droplet '{droplet.name}'...")
                        droplet.destroy()
                        logger("   - Droplet destroyed.")

                        # 2. Remove from database
                        if session:
                            statement = select(Project).where(Project.droplet_id == droplet.id)
                            project_to_delete = session.exec(statement).first()
                            if project_to_delete:
                                session.delete(project_to_delete)
                                session.commit()
                                logger("   - Database record removed.")

                        logger("[bold green]Cleanup completed.[/bold green]")
                    except Exception as cleanup_error:
                        logger(f"[bold red]Cleanup failed: {cleanup_error}[/bold red]")
                        logger("[yellow]You may need to manually delete from DigitalOcean.[/yellow]")
                else:
                    logger(
                        f"[bold red]Deployment failed. Server '{droplet.name}' NOT cleaned up.[/bold red]"
                    )
                    logger("[dim]Tip: Use --cleanup-on-failure to auto-cleanup.[/dim]")
            raise e

"""
Security Scanner - Pre-deployment secret detection for Xenfra.

This module scans codebases for:
- Hardcoded secrets (API keys, passwords, tokens)
- Exposed .env files
- Missing .gitignore entries
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Severity levels for security issues."""
    CRITICAL = "critical"  # Must fix before deploy
    WARNING = "warning"    # Should fix
    INFO = "info"          # Nice to have


@dataclass
class SecurityIssue:
    """A single security issue found in the codebase."""
    severity: Severity
    issue_type: str
    file: str
    line: Optional[int] = None
    description: str = ""
    suggestion: str = ""
    match: str = ""  # The actual matched content (redacted)
    
    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "type": self.issue_type,
            "file": self.file,
            "line": self.line,
            "description": self.description,
            "suggestion": self.suggestion,
            "match": self.match,
        }


@dataclass
class ScanResult:
    """Result of a security scan."""
    passed: bool
    issues: List[SecurityIssue] = field(default_factory=list)
    files_scanned: int = 0
    
    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)
    
    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)
    
    @property
    def summary(self) -> str:
        if self.passed:
            return f"No issues found ({self.files_scanned} files scanned)"
        parts = []
        if self.critical_count:
            parts.append(f"{self.critical_count} critical")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning")
        if self.info_count:
            parts.append(f"{self.info_count} info")
        return f"{len(self.issues)} issues found ({', '.join(parts)})"
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
            "files_scanned": self.files_scanned,
            "summary": self.summary,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
        }


# Secret detection patterns
# Format: (name, pattern, severity, description, suggestion)
SECRET_PATTERNS = [
    # AWS
    (
        "aws_access_key",
        r"AKIA[0-9A-Z]{16}",
        Severity.CRITICAL,
        "AWS Access Key ID found",
        "Move to environment variable: AWS_ACCESS_KEY_ID"
    ),
    (
        "aws_secret_key",
        r"(?i)(aws_secret_access_key|aws_secret_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
        Severity.CRITICAL,
        "AWS Secret Access Key found",
        "Move to environment variable: AWS_SECRET_ACCESS_KEY"
    ),
    
    # Generic API Keys
    (
        "api_key",
        r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
        Severity.CRITICAL,
        "Hardcoded API key found",
        "Move to environment variable"
    ),
    (
        "secret_key",
        r"(?i)(secret[_-]?key|secretkey)\s*[=:]\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
        Severity.CRITICAL,
        "Hardcoded secret key found",
        "Move to environment variable"
    ),
    
    # Database URLs
    (
        "database_url",
        r"(?i)(postgres|mysql|mongodb|redis)://[^\s'\"]+:[^\s'\"]+@",
        Severity.CRITICAL,
        "Database URL with credentials found",
        "Move to environment variable: DATABASE_URL"
    ),
    
    # Private Keys
    (
        "private_key",
        r"-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH)?\s*PRIVATE\s+KEY-----",
        Severity.CRITICAL,
        "Private key found in source code",
        "Move to a secure key management system"
    ),
    
    # JWT Secrets
    (
        "jwt_secret",
        r"(?i)(jwt[_-]?secret|jwt[_-]?key)\s*[=:]\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]",
        Severity.CRITICAL,
        "JWT secret found in source code",
        "Move to environment variable: JWT_SECRET"
    ),
    
    # Passwords
    (
        "password",
        r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]([^'\"]{8,})['\"]",
        Severity.WARNING,
        "Possible hardcoded password found",
        "Move to environment variable or use a secrets manager"
    ),
    
    # Bearer Tokens
    (
        "bearer_token",
        r"(?i)bearer\s+[a-zA-Z0-9_\-\.]+",
        Severity.WARNING,
        "Bearer token found in source code",
        "Move to environment variable"
    ),
    
    # GitHub Tokens
    (
        "github_token",
        r"gh[pousr]_[A-Za-z0-9_]{36,}",
        Severity.CRITICAL,
        "GitHub personal access token found",
        "Move to environment variable: GITHUB_TOKEN"
    ),
    
    # Stripe Keys
    (
        "stripe_key",
        r"sk_live_[0-9a-zA-Z]{24,}",
        Severity.CRITICAL,
        "Stripe live secret key found",
        "Move to environment variable: STRIPE_SECRET_KEY"
    ),
    (
        "stripe_publishable",
        r"pk_live_[0-9a-zA-Z]{24,}",
        Severity.WARNING,
        "Stripe live publishable key found (less sensitive but should be environment variable)",
        "Move to environment variable: STRIPE_PUBLISHABLE_KEY"
    ),
    
    # OpenAI / Anthropic
    (
        "openai_key",
        r"sk-[a-zA-Z0-9]{48,}",
        Severity.CRITICAL,
        "OpenAI API key found",
        "Move to environment variable: OPENAI_API_KEY"
    ),
    
    # DigitalOcean
    (
        "digitalocean_token",
        r"dop_v1_[a-f0-9]{64}",
        Severity.CRITICAL,
        "DigitalOcean API token found",
        "Move to environment variable: DIGITAL_OCEAN_TOKEN"
    ),
    
    # Slack
    (
        "slack_token",
        r"xox[baprs]-[0-9A-Za-z\-]+",
        Severity.CRITICAL,
        "Slack token found",
        "Move to environment variable: SLACK_TOKEN"
    ),
]

# Files to skip during scanning
SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".class", ".o", ".so", ".dylib",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar",
    ".pdf", ".doc", ".docx",
    ".lock", ".sum",
}

SKIP_DIRECTORIES = {
    ".git", ".hg", ".svn",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "venv", ".venv", "env",
    ".tox", ".nox",
    "dist", "build", "*.egg-info",
}


def _should_skip_file(path: Path) -> bool:
    """Check if file should be skipped."""
    # Skip by extension
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    
    # Skip large files (>1MB)
    try:
        if path.stat().st_size > 1_000_000:
            return True
    except OSError:
        return True
    
    return False


def _should_skip_directory(name: str) -> bool:
    """Check if directory should be skipped."""
    return name in SKIP_DIRECTORIES or name.startswith(".")


def _redact_secret(match: str, keep_chars: int = 4) -> str:
    """Redact a secret, keeping only first few characters."""
    if len(match) <= keep_chars * 2:
        return "***REDACTED***"
    return f"{match[:keep_chars]}...{match[-keep_chars:]}"


def scan_file_content(content: str, filename: str) -> List[SecurityIssue]:
    """Scan a single file's content for secrets."""
    issues = []
    lines = content.split("\n")
    
    for pattern_name, pattern, severity, description, suggestion in SECRET_PATTERNS:
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                # Skip if it's clearly a placeholder or example
                matched_text = match.group(0)
                lower_text = matched_text.lower()
                if any(skip in lower_text for skip in [
                    "example", "placeholder", "your_", "xxx", "changeme",
                    "todo", "fixme", "replace", "insert", "<your"
                ]):
                    continue
                
                issues.append(SecurityIssue(
                    severity=severity,
                    issue_type=pattern_name,
                    file=filename,
                    line=line_num,
                    description=description,
                    suggestion=suggestion,
                    match=_redact_secret(matched_text),
                ))
    
    return issues


def scan_directory(path: str) -> ScanResult:
    """Scan a directory for security issues."""
    root = Path(path)
    issues = []
    files_scanned = 0
    
    if not root.exists():
        return ScanResult(passed=True, files_scanned=0)
    
    # Check for .gitignore issues
    gitignore_path = root / ".gitignore"
    env_path = root / ".env"
    
    if env_path.exists():
        # .env exists - check if it's in .gitignore
        gitignore_content = ""
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text(errors="ignore")
        
        if ".env" not in gitignore_content:
            issues.append(SecurityIssue(
                severity=Severity.CRITICAL,
                issue_type="exposed_env",
                file=".env",
                description=".env file exists but is not in .gitignore",
                suggestion="Add '.env' to .gitignore to prevent committing secrets",
            ))
    
    # Scan all files
    for file_path in root.rglob("*"):
        # Skip directories
        if file_path.is_dir():
            continue
        
        # Skip if in a skip directory
        if any(_should_skip_directory(part) for part in file_path.parts):
            continue
        
        # Skip certain file types
        if _should_skip_file(file_path):
            continue
        
        try:
            content = file_path.read_text(errors="ignore")
            files_scanned += 1
            
            relative_path = str(file_path.relative_to(root))
            file_issues = scan_file_content(content, relative_path)
            issues.extend(file_issues)
            
        except Exception:
            # Skip files we can't read
            continue
    
    # Sort by severity (critical first)
    severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
    issues.sort(key=lambda x: severity_order.get(x.severity, 99))
    
    passed = not any(i.severity == Severity.CRITICAL for i in issues)
    
    return ScanResult(
        passed=passed,
        issues=issues,
        files_scanned=files_scanned,
    )


def scan_file_list(files: List[Dict[str, str]]) -> ScanResult:
    """
    Scan a list of files provided as dicts with 'path' and 'content' keys.
    
    This is useful for scanning files that haven't been written to disk yet,
    like files uploaded via API before deployment.
    
    Args:
        files: List of dicts with 'path' (or 'file') and 'content' keys
        
    Returns:
        ScanResult with any issues found
    """
    issues = []
    files_scanned = 0
    
    # Check if .env is in the list but .gitignore doesn't include it
    file_paths = [f.get("path") or f.get("file", "") for f in files]
    has_env = any(p.endswith(".env") or p == ".env" for p in file_paths)
    
    gitignore_content = ""
    for f in files:
        path = f.get("path") or f.get("file", "")
        if path == ".gitignore" or path.endswith("/.gitignore"):
            gitignore_content = f.get("content", "")
            break
    
    if has_env and ".env" not in gitignore_content:
        issues.append(SecurityIssue(
            severity=Severity.CRITICAL,
            issue_type="exposed_env",
            file=".env",
            description=".env file found but not in .gitignore",
            suggestion="Add '.env' to .gitignore to prevent committing secrets",
        ))
    
    # Scan each file
    for file_info in files:
        path = file_info.get("path") or file_info.get("file", "unknown")
        content = file_info.get("content", "")
        
        if not content:
            continue
        
        # Skip binary-looking content
        if "\x00" in content[:1000]:
            continue
        
        files_scanned += 1
        file_issues = scan_file_content(content, path)
        issues.extend(file_issues)
    
    # Sort by severity
    severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
    issues.sort(key=lambda x: severity_order.get(x.severity, 99))
    
    passed = not any(i.severity == Severity.CRITICAL for i in issues)
    
    return ScanResult(
        passed=passed,
        issues=issues,
        files_scanned=files_scanned,
    )

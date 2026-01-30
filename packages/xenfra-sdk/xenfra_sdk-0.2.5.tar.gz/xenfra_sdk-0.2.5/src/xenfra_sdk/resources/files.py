"""
Files resource manager for delta uploads.

Provides methods to check file cache status and upload files to the server.
"""

from typing import Dict, List


class FilesManager:
    """Manager for file upload operations."""
    
    def __init__(self, client):
        """
        Initialize the FilesManager.
        
        Args:
            client: The XenfraClient instance.
        """
        self._client = client
    
    def check(self, files: List[Dict]) -> Dict:
        """
        Check which files are missing from server cache.
        
        Args:
            files: List of file info dicts with keys: path, sha, size
        
        Returns:
            Dict with keys:
                - missing: List of SHA hashes that need to be uploaded
                - cached: Number of files already cached on server
        """
        payload = {
            "files": [
                {"path": f["path"], "sha": f["sha"], "size": f["size"]}
                for f in files
            ]
        }
        
        response = self._client._request("POST", "/files/check", json=payload)
        return response.json()
    
    def upload(self, content: bytes, sha: str, path: str) -> Dict:
        """
        Upload a single file to the server.
        
        Args:
            content: Raw file content as bytes
            sha: SHA256 hash of the content
            path: Relative file path
        
        Returns:
            Dict with keys: sha, size, stored
        """
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self._client._token}",
            "Content-Type": "application/octet-stream",
            "X-Xenfra-Sha": sha,
            "X-Xenfra-Path": path,
        }
        
        response = httpx.post(
            f"{self._client.api_url}/files/upload",
            content=content,
            headers=headers,
            timeout=120.0,  # 2 minutes for large files
        )
        response.raise_for_status()
        return response.json()
    
    def upload_files(self, files: List[Dict], missing_shas: List[str], progress_callback=None) -> int:
        """
        Upload multiple files that are missing from the server.
        
        Args:
            files: List of file info dicts with keys: path, sha, size, abs_path
            missing_shas: List of SHA hashes that need to be uploaded
            progress_callback: Optional callback(uploaded_count, total_count)
        
        Returns:
            Number of files uploaded
        """
        missing_set = set(missing_shas)
        files_to_upload = [f for f in files if f["sha"] in missing_set]
        total = len(files_to_upload)
        uploaded = 0
        
        for file_info in files_to_upload:
            with open(file_info["abs_path"], "rb") as f:
                content = f.read()
            
            self.upload(content, file_info["sha"], file_info["path"])
            uploaded += 1
            
            if progress_callback:
                progress_callback(uploaded, total)
        
        return uploaded

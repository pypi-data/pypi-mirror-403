"""GitHub API publisher for publishing files directly via GitHub REST API.

This publisher does not require a local Git repository and can work in
remote server environments where only a GitHub token is available.
"""

import asyncio
import base64
import os
import re
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .exceptions import PublishError, GitOperationError


class GitHubAPIPublisher:
    """Publisher that uses GitHub REST API to publish files directly.
    
    This publisher is useful when:
    - Running as a remote MCP server without local Git access
    - No local Git repository is available
    - Want to avoid Git operations overhead
    
    Requires:
    - GITHUB_TOKEN environment variable with repo permissions
    - GITHUB_REPO environment variable (e.g., "owner/repo")
    """
    
    DEFAULT_REPO = "gim-home/pm-studio-mcp"
    DEFAULT_BRANCH = "reports"
    API_BASE = "https://api.github.com"
    
    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[str] = None,
        branch: str = DEFAULT_BRANCH
    ):
        """Initialize GitHub API Publisher.
        
        Args:
            token: GitHub personal access token. If not provided, reads from GITHUB_TOKEN env var.
            repo: Repository in "owner/repo" format. If not provided, reads from GITHUB_REPO env var.
            branch: Target branch for publishing. Defaults to "reports".
        """
        if not HTTPX_AVAILABLE:
            raise PublishError(
                "httpx library is required for GitHub API publishing. "
                "Install it with: pip install httpx"
            )
        
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise PublishError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable or pass token parameter.\n"
                "To create a token:\n"
                "1. Go to https://github.com/settings/tokens\n"
                "2. Generate new token (classic) with 'repo' scope\n"
                "3. Set: export GITHUB_TOKEN=ghp_xxxx"
            )
        
        self.repo = repo or os.environ.get("GITHUB_REPO", self.DEFAULT_REPO)
        self.branch = branch
        self.owner, self.repo_name = self.repo.split("/")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        print(f"[DEBUG] GitHubAPIPublisher initialized: repo={self.repo}, branch={self.branch}", flush=True)
    
    def publish(
        self,
        html_file_path: str,
        image_paths: Optional[List[str]] = None
    ) -> str:
        """Publish HTML file and images to GitHub Pages via API.
        
        Args:
            html_file_path: Path to the local HTML file
            image_paths: Optional list of image file paths to upload
            
        Returns:
            GitHub Pages URL where the content can be accessed
        """
        # Run async code in sync context
        # Handle both cases: running in existing event loop or not
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, need to use run_in_executor or nest
            # Create a new event loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    self._publish_async(html_file_path, image_paths)
                )
                return future.result()
        except RuntimeError:
            # No running event loop, we can use asyncio.run directly
            return asyncio.run(self._publish_async(html_file_path, image_paths))
    
    async def _publish_async(
        self,
        html_file_path: str,
        image_paths: Optional[List[str]] = None
    ) -> str:
        """Async implementation of publish."""
        import time
        t0 = time.time()
        
        if not os.path.isfile(html_file_path):
            raise PublishError(f"HTML file does not exist: {html_file_path}")
        
        file_name = os.path.basename(html_file_path)
        print(f"[DEBUG] [T+{time.time()-t0:.2f}s] Starting API publish: {file_name}", flush=True)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Ensure branch exists
            print(f"[DEBUG] [T+{time.time()-t0:.2f}s] Checking if branch '{self.branch}' exists...", flush=True)
            await self._ensure_branch_exists(client)
            print(f"[DEBUG] [T+{time.time()-t0:.2f}s] Branch check complete", flush=True)
            
            # 2. Process HTML and fix image paths
            html_content, image_mapping = self._process_html_for_upload(html_file_path, image_paths)
            
            # 3. Upload HTML file
            print(f"[DEBUG] [T+{time.time()-t0:.2f}s] Uploading HTML file: {file_name}", flush=True)
            await self._upload_file(client, file_name, html_content.encode('utf-8'))
            print(f"[DEBUG] [T+{time.time()-t0:.2f}s] HTML file uploaded", flush=True)
            
            # 4. Upload images in parallel
            if image_paths:
                print(f"[DEBUG] [T+{time.time()-t0:.2f}s] Uploading {len(image_paths)} images...", flush=True)
                await self._upload_images(client, image_mapping)
                print(f"[DEBUG] [T+{time.time()-t0:.2f}s] Images uploaded", flush=True)
            
            # 5. Return GitHub Pages URL
            url = self._get_pages_url(file_name)
            print(f"[DEBUG] [T+{time.time()-t0:.2f}s] Publish complete: {url}", flush=True)
            return url
    
    async def _ensure_branch_exists(self, client: "httpx.AsyncClient") -> None:
        """Ensure the target branch exists, create if not."""
        # Check if branch exists
        url = f"{self.API_BASE}/repos/{self.repo}/branches/{self.branch}"
        response = await client.get(url, headers=self.headers)
        
        if response.status_code == 200:
            print(f"[DEBUG] Branch '{self.branch}' exists", flush=True)
            return
        
        if response.status_code == 404:
            print(f"[DEBUG] Branch '{self.branch}' not found, creating...", flush=True)
            await self._create_branch(client)
        else:
            raise GitOperationError(
                f"Failed to check branch: {response.status_code} - {response.text}"
            )
    
    async def _create_branch(self, client: "httpx.AsyncClient") -> None:
        """Create the target branch from default branch."""
        # Get default branch SHA
        repo_url = f"{self.API_BASE}/repos/{self.repo}"
        response = await client.get(repo_url, headers=self.headers)
        if response.status_code != 200:
            raise GitOperationError(f"Failed to get repo info: {response.text}")
        
        default_branch = response.json().get("default_branch", "main")
        
        # Get SHA of default branch
        ref_url = f"{self.API_BASE}/repos/{self.repo}/git/refs/heads/{default_branch}"
        response = await client.get(ref_url, headers=self.headers)
        if response.status_code != 200:
            raise GitOperationError(f"Failed to get default branch ref: {response.text}")
        
        sha = response.json()["object"]["sha"]
        
        # Create new branch
        create_url = f"{self.API_BASE}/repos/{self.repo}/git/refs"
        payload = {
            "ref": f"refs/heads/{self.branch}",
            "sha": sha
        }
        response = await client.post(create_url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            print(f"[DEBUG] Created branch '{self.branch}'", flush=True)
        elif response.status_code == 422 and "Reference already exists" in response.text:
            print(f"[DEBUG] Branch '{self.branch}' already exists (race condition)", flush=True)
        else:
            raise GitOperationError(f"Failed to create branch: {response.text}")
    
    async def _get_file_sha(self, client: "httpx.AsyncClient", path: str) -> Optional[str]:
        """Get SHA of existing file (needed for updates)."""
        url = f"{self.API_BASE}/repos/{self.repo}/contents/{path}?ref={self.branch}"
        response = await client.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json().get("sha")
        return None
    
    async def _upload_file(
        self,
        client: "httpx.AsyncClient",
        path: str,
        content: bytes,
        message: Optional[str] = None
    ) -> None:
        """Upload a single file to the repository."""
        url = f"{self.API_BASE}/repos/{self.repo}/contents/{path}"
        
        # Check if file exists to get SHA for update
        sha = await self._get_file_sha(client, path)
        
        payload = {
            "message": message or f"Publish {path}",
            "content": base64.b64encode(content).decode('utf-8'),
            "branch": self.branch
        }
        
        if sha:
            payload["sha"] = sha
            print(f"[DEBUG] Updating existing file: {path}", flush=True)
        else:
            print(f"[DEBUG] Creating new file: {path}", flush=True)
        
        response = await client.put(url, headers=self.headers, json=payload)
        
        if response.status_code not in (200, 201):
            raise PublishError(f"Failed to upload {path}: {response.status_code} - {response.text}")
    
    async def _upload_images(
        self,
        client: "httpx.AsyncClient",
        image_mapping: List[Tuple[str, str]]
    ) -> None:
        """Upload multiple images in parallel."""
        tasks = []
        for local_path, target_path in image_mapping:
            if os.path.isfile(local_path):
                with open(local_path, 'rb') as f:
                    content = f.read()
                task = self._upload_file(
                    client,
                    target_path,
                    content,
                    f"Upload image {os.path.basename(local_path)}"
                )
                tasks.append(task)
            else:
                print(f"[DEBUG] Warning: Image not found: {local_path}", flush=True)
        
        if tasks:
            # Upload images concurrently (max 5 at a time to avoid rate limits)
            for i in range(0, len(tasks), 5):
                batch = tasks[i:i+5]
                await asyncio.gather(*batch, return_exceptions=True)
    
    def _process_html_for_upload(
        self,
        html_file_path: str,
        image_paths: Optional[List[str]]
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """Process HTML file and prepare image mapping.
        
        Returns:
            Tuple of (html_content, list of (local_path, target_path) for images)
        """
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        image_mapping = []
        
        if not image_paths:
            return html_content, image_mapping
        
        # Parse image references from HTML
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        html_image_refs = {}
        
        for match in re.finditer(img_pattern, html_content, re.IGNORECASE):
            src_path = match.group(1)
            # Skip external URLs
            if src_path.startswith(('http://', 'https://', '//', 'data:', 'blob:')):
                continue
            filename = os.path.basename(src_path)
            html_image_refs[filename] = src_path
        
        # Match provided images to HTML references
        for image_path in image_paths:
            if not os.path.isfile(image_path):
                continue
            
            filename = os.path.basename(image_path)
            
            if filename in html_image_refs:
                target_path = html_image_refs[filename]
                # Normalize path (remove leading ./ or ../)
                target_path = re.sub(r'^\.\.?[/\\]+', '', target_path)
                target_path = target_path.replace('\\', '/')
            else:
                target_path = f"assets/images/{filename}"
            
            image_mapping.append((image_path, target_path))
        
        # Fix invalid paths in HTML (../ paths)
        for filename, src_path in html_image_refs.items():
            if src_path.startswith('..') or src_path.startswith('/') or src_path.startswith('\\'):
                new_src = f"assets/images/{filename}"
                html_content = html_content.replace(f'src="{src_path}"', f'src="{new_src}"')
                html_content = html_content.replace(f"src='{src_path}'", f"src='{new_src}'")
        
        return html_content, image_mapping
    
    def _get_pages_url(self, file_name: str) -> str:
        """Generate GitHub Pages URL for the published file."""
        return f"https://{self.owner}.github.io/{self.repo_name}/{file_name}"


def is_github_api_available() -> bool:
    """Check if GitHub API publishing is available."""
    return bool(os.environ.get("GITHUB_TOKEN")) and HTTPX_AVAILABLE


def is_local_git_available(path: Optional[str] = None) -> bool:
    """Check if local Git repository is available."""
    import subprocess
    
    try:
        cwd = path or os.getcwd()
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,  # Prevent hanging on input
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

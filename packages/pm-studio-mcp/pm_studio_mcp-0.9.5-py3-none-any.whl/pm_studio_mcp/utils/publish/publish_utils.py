from pm_studio_mcp.utils.publish.config import PublishConfig
from pm_studio_mcp.utils.publish.publisher import GitHubPagesPublisher
from pm_studio_mcp.utils.publish.github_api_publisher import (
    GitHubAPIPublisher,
    is_github_api_available,
    is_local_git_available
)
from pm_studio_mcp.utils.publish.exceptions import PublishError
from typing import List, Optional
import os


def find_git_repo(start_path: Optional[str] = None) -> Optional[str]:
    """Find Git repository by traversing up from start_path.
    
    Args:
        start_path: Starting directory to search from. Defaults to current directory.
        
    Returns:
        Path to Git repository root, or None if not found.
    """
    from pathlib import Path
    
    path = Path(start_path or os.getcwd()).resolve()
    
    # Traverse up to find .git directory
    while path != path.parent:
        if (path / '.git').exists():
            return str(path)
        path = path.parent
    
    return None


class PublishUtils:
    """Utility class for publishing HTML files to GitHub Pages.
    
    Supports two publishing modes:
    1. GitHub API mode: Uses REST API directly (requires GITHUB_TOKEN)
    2. Local Git mode: Uses local Git operations (requires local repository)
    
    The mode is automatically selected based on available resources:
    - If GITHUB_TOKEN is set, prefers API mode (works in remote environments)
    - Falls back to local Git mode if a repository is available
    """
    
    @staticmethod
    def publish_html(
        html_file_path: str,
        image_paths: Optional[List[str]] = None,
        repo_dir: Optional[str] = None,
        use_api: Optional[bool] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None
    ) -> str:
        """Publish HTML file and images to GitHub Pages.
        
        Args:
            html_file_path: Path to the HTML file to publish
            image_paths: Optional list of image file paths to upload
            repo_dir: Optional path to Git repository (for local Git mode)
            use_api: Force API mode (True) or local Git mode (False). 
                    If None, auto-detects based on environment.
            github_token: GitHub token for API mode. Defaults to GITHUB_TOKEN env var.
            github_repo: Target repository for API mode. Defaults to GITHUB_REPO env var.
            
        Returns:
            GitHub Pages URL where the content can be accessed
            
        Raises:
            PublishError: If publishing fails
        """
        print(f"[DEBUG] Entered publish_html with html_file_path={html_file_path}, image_paths={image_paths}", flush=True)
        print(f"[DEBUG] Options: repo_dir={repo_dir}, use_api={use_api}", flush=True)
        
        # Determine which mode to use
        if use_api is None:
            # Auto-detect: prefer API mode if token is available
            use_api = is_github_api_available()
            print(f"[DEBUG] Auto-detected mode: {'API' if use_api else 'Local Git'}", flush=True)
        
        if use_api:
            return PublishUtils._publish_via_api(
                html_file_path, 
                image_paths, 
                github_token, 
                github_repo
            )
        else:
            return PublishUtils._publish_via_local_git(
                html_file_path, 
                image_paths, 
                repo_dir
            )
    
    @staticmethod
    def _publish_via_api(
        html_file_path: str,
        image_paths: Optional[List[str]],
        github_token: Optional[str],
        github_repo: Optional[str]
    ) -> str:
        """Publish using GitHub REST API."""
        print(f"[DEBUG] Using GitHub API mode", flush=True)
        
        publisher = GitHubAPIPublisher(
            token=github_token,
            repo=github_repo,
            branch="reports"
        )
        
        return publisher.publish(html_file_path, image_paths)
    
    @staticmethod
    def _publish_via_local_git(
        html_file_path: str,
        image_paths: Optional[List[str]],
        repo_dir: Optional[str]
    ) -> str:
        """Publish using local Git operations."""
        print(f"[DEBUG] Using Local Git mode", flush=True)
        
        # Determine repo_dir - use the same logic as main branch (hardcoded relative path)
        if repo_dir is None:
            repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
        
        print(f"[DEBUG] publish_html repo_dir resolved to: {repo_dir}", flush=True)
        
        config_obj = PublishConfig(
            html_file_path=html_file_path,
            repo_dir=repo_dir,
            publish_branch="reports",
            commit_message="Publish HTML report to GitHub Pages",
            image_paths=image_paths
        )
        print(f"[DEBUG] PublishConfig created", flush=True)
        
        publisher = GitHubPagesPublisher(config_obj)
        print(f"[DEBUG] GitHubPagesPublisher instantiated", flush=True)
        
        return publisher.publish()

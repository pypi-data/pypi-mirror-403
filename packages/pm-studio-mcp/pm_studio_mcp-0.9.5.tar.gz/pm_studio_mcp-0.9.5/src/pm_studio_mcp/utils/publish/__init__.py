"""GitHub Pages publishing package for pm-studio-mcp.

This package provides tools to publish HTML files and associated images to GitHub Pages.

Supports two publishing modes:
1. GitHub API mode: Uses REST API directly (requires GITHUB_TOKEN, works in remote environments)
2. Local Git mode: Uses local Git operations (requires local repository)
"""

from .config import PublishConfig
from .publisher import GitHubPagesPublisher
from .github_api_publisher import (
    GitHubAPIPublisher,
    is_github_api_available,
    is_local_git_available
)
from .publish_utils import PublishUtils, find_git_repo
from .exceptions import (
    PublishError,
    GitOperationError,
    FileProcessingError,
    ValidationError,
    UncommittedChangesError
)

__all__ = [
    # Main utilities
    'PublishUtils',
    'find_git_repo',
    # Publishers
    'GitHubPagesPublisher',
    'GitHubAPIPublisher',
    # Configuration
    'PublishConfig',
    # Helper functions
    'is_github_api_available',
    'is_local_git_available',
    # Exceptions
    'PublishError',
    'GitOperationError',
    'FileProcessingError',
    'ValidationError',
    'UncommittedChangesError'
]

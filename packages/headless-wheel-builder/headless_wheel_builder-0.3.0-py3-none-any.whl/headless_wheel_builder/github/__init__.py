"""GitHub integration for Headless Wheel Builder.

Provides headless GitHub operations for releases, repositories, and workflows.

Example:
    >>> from headless_wheel_builder.github import GitHubClient, create_release
    >>>
    >>> async def release():
    ...     client = GitHubClient()
    ...     release = await client.create_release(
    ...         repo="owner/repo",
    ...         tag="v1.0.0",
    ...         name="Version 1.0.0",
    ...         body="Release notes...",
    ...     )
    ...     await client.upload_assets(release.upload_url, ["dist/pkg-1.0.0.whl"])
"""

from headless_wheel_builder.github.client import GitHubClient
from headless_wheel_builder.github.models import (
    GitHubConfig,
    Release,
    ReleaseAsset,
    ReleaseResult,
    Repository,
)

__all__ = [
    "GitHubClient",
    "GitHubConfig",
    "Release",
    "ReleaseAsset",
    "ReleaseResult",
    "Repository",
]

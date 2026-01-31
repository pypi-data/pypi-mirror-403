"""Publish private PRs to public repos with LaminDB asset hosting."""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import lamindb as ln
import requests
from dotenv import load_dotenv


def _parse_github_repo_url(url: str) -> tuple[str | Any, ...]:
    """Parse GitHub repository URL into owner and repo.

    Args:
        url: GitHub repo URL like "https://github.com/owner/repo"

    Returns:
        Tuple of (owner, repo)
    """
    match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        raise ValueError(f"Invalid GitHub repository URL: {url}")
    return match.groups()


def _get_pr_data(owner: str, repo: str, pr_number: str | int, token: str) -> dict:
    """Fetch PR data from GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        token: GitHub token

    Returns:
        PR data dictionary
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def _get_commits_data(pr_data: dict, token: str) -> tuple[str, str]:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Fetch commits from the original PR to get author info
    commits_url = pr_data["commits_url"]
    commits_response = requests.get(commits_url, headers=headers)
    commits_response.raise_for_status()
    commits = commits_response.json()

    # Use the author info from the first commit in the PR
    author_name = commits[0]["commit"]["author"]["name"]
    author_email = commits[0]["commit"]["author"]["email"]
    return author_name, author_email


def _process_assets(
    repo_name: str, pr_body: str, pr_number: str | int, github_token: str
) -> str:
    """Download assets from PR, upload to LaminDB, and replace URLs.

    Args:
        repo_name: Repository name for organizing assets
        pr_body: PR description/body text
        pr_number: PR number for organizing assets
        github_token: GitHub token for downloading assets

    Returns:
        Updated PR body with replaced URLs
    """
    # Find all GitHub asset URLs
    asset_urls = re.findall(
        r"https://github\.com/user-attachments/assets/[a-f0-9\-]+", pr_body
    )
    asset_urls += re.findall(
        r"https://user-images\.githubusercontent\.com/[0-9]+/[a-f0-9\-]+", pr_body
    )
    asset_urls = list(set(asset_urls))  # Remove duplicates

    if not asset_urls:
        print("No assets found in PR description")
        return pr_body

    print(f"Found {len(asset_urls)} assets to process")
    url_mapping = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        asset_dir = Path(tmpdir)

        for old_url in asset_urls:
            filename = f"{old_url.split('/')[-1]}.png"
            local_path = asset_dir / filename

            # Download asset
            print(f"Downloading: {old_url}")
            response = requests.get(
                old_url,
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/octet-stream",
                },
                allow_redirects=True,
            )
            response.raise_for_status()
            local_path.write_bytes(response.content)

            # Upload to LaminDB
            key = f"{repo_name}/pr-assets/pr-{pr_number}/{filename}"
            print(f"Uploading to LaminDB: {key}")
            artifact = ln.Artifact(local_path, key=key).save()

            # Map to new URL
            new_url = artifact.path.to_url()
            url_mapping[old_url] = new_url
            print(f"✓ Mapped: {old_url} -> {new_url}")

    # Replace URLs in description
    new_description = pr_body
    for old_url, new_url in url_mapping.items():
        new_description = new_description.replace(old_url, new_url)

    print(f"✓ Processed {len(url_mapping)} assets")
    return new_description


def _create_public_pr(
    dest_owner: str,
    dest_repo: str,
    source_repo: str,
    pr_data: dict,
    updated_body: str,
    author_name: str,
    author_email: str,
    github_token: str,
) -> str:
    """Create PR in public repository.

    Args:
        dest_owner: Destination repository owner
        dest_repo: Destination repository name
        source_repo: Source repository name
        pr_data: Original PR data
        updated_body: Updated PR body with replaced asset URLs
        author_name: Original PR author's name
        author_email: Original PR author's email
        github_token: GitHub token

    Returns:
        URL of created PR
    """
    # Create branch name
    branch_name = f"pr-sync-{pr_data['number']}"

    # Get original author info from the PR's head commit
    # This gives us the actual email used in commits, not a privacy email
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Create a dummy file and branch
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / dest_repo

        # Clone repo
        subprocess.run(
            [
                "git",
                "clone",
                "--depth=1",
                f"https://{github_token}@github.com/{dest_owner}/{dest_repo}.git",
                str(repo_dir),
            ],
            check=True,
            capture_output=True,
        )

        # Configure git with original author info
        subprocess.run(
            ["git", "config", "user.name", author_name],
            cwd=repo_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", author_email],
            cwd=repo_dir,
            check=True,
        )

        subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_dir, check=True)

        existing_content = (repo_dir / "source-prs.txt").read_text()
        (repo_dir / "source-prs.txt").write_text(
            f"{pr_data['number']}\n{existing_content}"
        )
        subprocess.run(["git", "add", "source-prs.txt"], cwd=repo_dir, check=True)

        # Set environment variables to override committer info
        env = os.environ.copy()
        env["GIT_COMMITTER_NAME"] = author_name
        env["GIT_COMMITTER_EMAIL"] = author_email

        # git author info is set via --author flag
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Sync PR #{pr_data['number']}",
                "--author",
                f"{author_name} <{author_email}>",
            ],
            cwd=repo_dir,
            env=env,
            check=True,
        )
        subprocess.run(["git", "push", "origin", branch_name], cwd=repo_dir, check=True)

    # Create PR using GitHub API
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Remove the author attribution footer
    pr_body = f"""{updated_body}

---

Original PR: https://github.com/{dest_owner}/{source_repo}/pull/{pr_data["number"]}
"""

    create_pr_url = f"https://api.github.com/repos/{dest_owner}/{dest_repo}/pulls"
    response = requests.post(
        create_pr_url,
        json={
            "title": pr_data["title"],
            "body": pr_body,
            "head": branch_name,
            "base": "main",
        },
        headers=headers,
    )
    response.raise_for_status()

    created_pr = response.json()
    print(f"✓ Created PR: {created_pr['html_url']}")

    return created_pr["html_url"]


class Publisher:
    """Publisher for syncing private PRs to public repositories with LaminDB asset hosting.

    Downloads any GitHub-hosted assets (user-attachments, user-images) from the
    source PR, uploads them to LaminDB, and creates a new PR in the destination
    repository with updated asset URLs.

    Args:
        source_repo: Source GitHub repository URL (e.g., "https://github.com/owner/repo")
        target_repo: Target GitHub repository URL (e.g., "https://github.com/owner/public-repo")
        source_token: GitHub token (defaults to GITHUB_SOURCE_TOKEN env var)
        target_token: GitHub token for target repo (defaults to GITHUB_TARGET_TOKEN env var)

    Example:
        >>> from publishprs import Publisher
        >>> publisher = Publisher(
        ...     source_repo="https://github.com/laminlabs/laminhub",
        ...     target_repo="https://github.com/laminlabs/laminhub-public",
        ... )
        >>> url = publisher.publish(pull_id=3820, close_pr=True)
        >>> print(f"Published to: {url}")
    """

    def __init__(
        self,
        source_repo: str,
        target_repo: str,
        source_token: str | None = None,
        target_token: str | None = None,
    ):
        """Initialize the Publisher.

        Args:
            source_repo: Source GitHub repository URL
            target_repo: Target GitHub repository URL
            db: LaminDB instance (defaults to LAMINDB_INSTANCE env var
                     or "laminlabs/lamin-site-assets")
            source_token: GitHub token (defaults to GITHUB_SOURCE_TOKEN env var)
            target_token: GitHub token for target repo (defaults to GITHUB_TARGET_TOKEN env var)
        """
        self.source_owner, self.source_repo = _parse_github_repo_url(source_repo)
        self.target_owner, self.target_repo = _parse_github_repo_url(target_repo)
        load_dotenv()
        self.source_token = source_token or os.environ.get("GITHUB_SOURCE_TOKEN")
        self.target_token = target_token or os.environ.get("GITHUB_TARGET_TOKEN")

        if not self.source_token:
            raise ValueError(
                "GitHub token required (pass source_token or set GITHUB_SOURCE_TOKEN env var)"
            )
        if not self.target_token:
            raise ValueError(
                "GitHub token required (pass target_token or set GITHUB_TARGET_TOKEN env var)"
            )

    def publish(self, pull_id: int, close_pr: bool = True) -> str:
        """Publish a private PR to the public repository.

        Args:
            pull_id: PR number/ID from the source repository
            close_pr: Whether to auto-merge the created PR (default: True)

        Returns:
            URL of the created PR in the target repository
        """
        # Get PR data
        print(f"Fetching PR #{pull_id} from {self.source_owner}/{self.source_repo}")
        pr_data = _get_pr_data(
            self.source_owner, self.source_repo, pull_id, self.source_token
        )

        if not pr_data.get("merged"):
            print("Warning: PR is not merged")

        author_name, author_email = _get_commits_data(pr_data, self.source_token)

        # Process assets (download, upload to LaminDB, replace URLs)
        updated_body = _process_assets(
            self.source_repo, pr_data["body"] or "", pull_id, self.source_token
        )

        # Create PR in target repo
        pr_url = _create_public_pr(
            self.target_owner,
            self.target_repo,
            self.source_repo,
            pr_data,
            updated_body,
            author_name,
            author_email,
            self.target_token,
        )

        # Auto-merge if requested
        if close_pr:
            print("Auto-merging PR...")

            # Get the created PR number
            created_pr_number = pr_url.split("/")[-1]

            # Merge via API
            headers = {
                "Authorization": f"token {self.target_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            merge_url = f"https://api.github.com/repos/{self.target_owner}/{self.target_repo}/pulls/{created_pr_number}/merge"
            # only if we rebase we maintain the identity of the original user
            # otherwise the PR author (for which no on-behalf flow is possible) will be the committer on main
            response = requests.put(
                merge_url, json={"merge_method": "squash"}, headers=headers
            )
            response.raise_for_status()
            print("✓ PR merged")

        return pr_url

import os
import pathlib
import re
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse

import click


@dataclass
class ParsedGitUrl:
    host: str
    owner: str
    repo: str


def parse_git_url(url: str) -> ParsedGitUrl:
    """
    Parse a git URL and extract host, owner, and repo.

    Handles:
    - HTTPS URLs: https://github.com/owner/repo
    - SSH URLs: git@github.com:owner/repo
    - Git protocol: git://github.com/owner/repo
    - URLs with or without .git suffix
    - Sourcehut-style URLs with ~ prefix: https://git.sr.ht/~user/repo
    """
    # Normalize: remove trailing .git
    url = re.sub(r"\.git$", "", url)

    # Handle SSH format: git@host:path
    ssh_match = re.match(r"^(?:[\w-]+@)?([\w.-]+):(.+)$", url)
    if ssh_match and not url.startswith(("http://", "https://", "git://")):
        host = ssh_match.group(1)
        path = ssh_match.group(2)
    else:
        # Handle HTTP(S) and git:// URLs
        parsed = urlparse(url)
        host = parsed.netloc or parsed.hostname or ""
        # Remove user@ prefix if present
        if "@" in host:
            host = host.split("@")[-1]
        path = parsed.path.lstrip("/")

    # Split path into owner and repo
    parts = [p for p in path.split("/") if p]

    if len(parts) >= 2:
        owner = parts[0]
        repo = parts[1]
    elif len(parts) == 1:
        owner = ""
        repo = parts[0]
    else:
        owner = ""
        repo = ""

    # Clean up owner (remove ~ prefix for sourcehut-style URLs)
    owner = owner.lstrip("~")

    return ParsedGitUrl(host=host, owner=owner, repo=repo)


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("repo", type=str)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def git_smart_clone(repo: str, args):
    home_folder = pathlib.Path.home()
    base_path = pathlib.Path(
        os.environ.get("GIT_SMART_CLONE_BASE_PATH", home_folder / "src")
    )

    url = parse_git_url(repo)
    destination_path = base_path / url.host / url.owner / url.repo

    destination_path.mkdir(parents=True, exist_ok=True)
    git_args = ["git", "clone", repo, destination_path.absolute()]
    git_args.extend(args)
    subprocess.run(git_args)


if __name__ == "__main__":
    git_smart_clone()

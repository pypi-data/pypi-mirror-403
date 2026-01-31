"""Problem set management for Wafer CLI.

Download and manage kernel optimization problem sets for evaluation.
Follows the same pattern as corpus.py for consistency.
"""

import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import httpx

PROBLEMS_CACHE_DIR = Path.home() / ".cache" / "wafer" / "problems"

ProblemSetName = Literal["kernelbench", "gpumode"]


@dataclass
class ProblemSetConfig:
    """Configuration for a downloadable problem set."""

    name: ProblemSetName
    description: str
    repo: str  # GitHub repo in "owner/repo" format
    repo_paths: list[str]  # Paths within repo to download
    format_description: str  # Brief description of the format


PROBLEM_SETS: dict[ProblemSetName, ProblemSetConfig] = {
    "kernelbench": ProblemSetConfig(
        name="kernelbench",
        description="KernelBench GPU kernel optimization problems (level1-4)",
        repo="ScalingIntelligence/KernelBench",
        repo_paths=["KernelBench"],
        format_description="Class-based: Model/ModelNew with get_inputs/get_init_inputs",
    ),
    "gpumode": ProblemSetConfig(
        name="gpumode",
        description="GPU Mode reference kernels (pmpp, amd, nvidia, bioml)",
        repo="gpu-mode/reference-kernels",
        repo_paths=["problems"],
        format_description="Functional: ref_kernel/custom_kernel with generate_input",
    ),
}


def _problems_path(name: ProblemSetName) -> Path:
    """Get local path for problem set."""
    return PROBLEMS_CACHE_DIR / name


def _ensure_cache_dir() -> None:
    """Ensure cache directory exists."""
    PROBLEMS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _download_github_repo(config: ProblemSetConfig, dest: Path, verbose: bool = True) -> int:
    """Download specific paths from GitHub repo.

    Args:
        config: Problem set configuration
        dest: Destination directory
        verbose: Print progress

    Returns:
        Number of files downloaded
    """
    # Fetch tarball from GitHub
    resp = _fetch_github_tarball(config.repo, verbose)

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = Path(tmp.name)

    # Extract matching files
    try:
        downloaded = _extract_tarball(tmp_path, dest, config.repo_paths, verbose)
    finally:
        tmp_path.unlink()

    return downloaded


def _fetch_github_tarball(repo: str, verbose: bool) -> httpx.Response:
    """Fetch tarball from GitHub, trying main then master branch."""
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        for branch in ["main", "master"]:
            tarball_url = f"https://api.github.com/repos/{repo}/tarball/{branch}"
            if verbose:
                print(f"  Fetching {repo} ({branch} branch)...")
            try:
                resp = client.get(tarball_url)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError:
                if branch == "master":
                    raise
    raise RuntimeError(f"Failed to fetch tarball from {repo}")  # Should not reach


def _extract_tarball(tmp_path: Path, dest: Path, repo_paths: list[str], verbose: bool) -> int:
    """Extract files from tarball matching repo_paths."""
    downloaded = 0
    with tarfile.open(tmp_path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            # Strip the root directory (e.g., "ScalingIntelligence-KernelBench-abc123/")
            rel_path = "/".join(member.name.split("/")[1:])
            if not _matches_repo_paths(rel_path, repo_paths):
                continue
            target = dest / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted = tar.extractfile(member)
            if extracted:
                target.write_bytes(extracted.read())
                downloaded += 1
                if verbose and downloaded <= 10:
                    print(f"  ✓ {rel_path}")
        if verbose and downloaded > 10:
            print(f"  ... and {downloaded - 10} more files")
    return downloaded


def _matches_repo_paths(rel_path: str, repo_paths: list[str]) -> bool:
    """Check if rel_path starts with any of the repo_paths."""
    return any(rel_path.startswith(rp) for rp in repo_paths)


def download_problems(name: ProblemSetName, force: bool = False, verbose: bool = True) -> Path:
    """Download a problem set to local cache.

    Args:
        name: Problem set name
        force: Re-download even if exists
        verbose: Print progress

    Returns:
        Path to downloaded problem set

    Raises:
        ValueError: If problem set name is unknown
        httpx.HTTPError: If download fails
    """
    if name not in PROBLEM_SETS:
        raise ValueError(f"Unknown problem set: {name}. Available: {list(PROBLEM_SETS.keys())}")

    config = PROBLEM_SETS[name]
    dest = _problems_path(name)

    if dest.exists() and not force:
        if verbose:
            print(f"Problem set '{name}' already exists at {dest}")
            print("Use --force to re-download")
        return dest

    _ensure_cache_dir()

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    if verbose:
        print(f"Downloading {name}: {config.description}")

    try:
        count = _download_github_repo(config, dest, verbose)
    except Exception:
        # Clean up partial download so next run doesn't skip with stale cache
        if dest.exists():
            shutil.rmtree(dest)
        raise

    if verbose:
        print(f"Downloaded {count} files to {dest}")

    return dest


def get_problems_path(name: ProblemSetName) -> Path | None:
    """Get path to downloaded problem set, or None if not downloaded.

    Args:
        name: Problem set name

    Returns:
        Path if downloaded, None otherwise
    """
    if name not in PROBLEM_SETS:
        return None
    path = _problems_path(name)
    return path if path.exists() else None


def list_problem_sets(verbose: bool = True) -> dict[ProblemSetName, bool]:
    """List available problem sets and their download status.

    Returns:
        Dict of problem set name -> is_downloaded
    """
    result: dict[ProblemSetName, bool] = {}
    for name, config in PROBLEM_SETS.items():
        path = _problems_path(name)
        exists = path.exists()
        result[name] = exists
        if verbose:
            status = "✓" if exists else " "
            print(f"[{status}] {name}: {config.description}")
            print(f"    Format: {config.format_description}")
            if exists:
                file_count = sum(1 for _ in path.rglob("*.py") if _.is_file())
                print(f"    Location: {path} ({file_count} Python files)")
    return result


def list_problems(name: ProblemSetName, verbose: bool = True) -> list[str]:
    """List available problems in a problem set.

    Args:
        name: Problem set name
        verbose: Print to stdout

    Returns:
        List of problem IDs

    Raises:
        ValueError: If problem set not downloaded
    """
    path = get_problems_path(name)
    if path is None:
        raise ValueError(
            f"Problem set '{name}' is not downloaded. Run:\n  wafer evaluate {name} download"
        )

    if name == "kernelbench":
        problems = _list_kernelbench_problems(path)
    elif name == "gpumode":
        problems = _list_gpumode_problems(path)
    else:
        problems = []

    if verbose:
        if not problems:
            print(f"No problems found in {name}")
        else:
            print(f"Available problems in {name} ({len(problems)} total):\n")
            for p in problems:
                print(f"  {p}")

    return problems


def _list_kernelbench_problems(path: Path) -> list[str]:
    """List KernelBench problems: level1/1_Name.py format."""
    problems: list[str] = []
    kb_root = path / "KernelBench"
    if not kb_root.exists():
        kb_root = path  # In case structure is flat

    for level_dir in sorted(kb_root.iterdir()):
        if not (level_dir.is_dir() and level_dir.name.startswith("level")):
            continue
        for problem_file in sorted(level_dir.glob("*.py")):
            if problem_file.name.startswith("__"):
                continue
            problem_id = f"{level_dir.name}/{problem_file.stem}"
            problems.append(problem_id)
    return problems


def _list_gpumode_problems(path: Path) -> list[str]:
    """List GPUMode problems: category/problem_name format."""
    problems: list[str] = []
    problems_root = path / "problems"
    if not problems_root.exists():
        problems_root = path

    for category_dir in sorted(problems_root.iterdir()):
        if not _is_valid_problem_dir(category_dir):
            continue
        for problem_dir in sorted(category_dir.iterdir()):
            if not _is_valid_problem_dir(problem_dir):
                continue
            # Check if it has the expected files
            has_reference = (problem_dir / "reference.py").exists()
            has_task = (problem_dir / "task.yml").exists()
            if has_reference or has_task:
                problem_id = f"{category_dir.name}/{problem_dir.name}"
                problems.append(problem_id)
    return problems


def _is_valid_problem_dir(path: Path) -> bool:
    """Check if path is a valid problem directory (not hidden/special)."""
    return path.is_dir() and not path.name.startswith((".", "_"))


def get_problem_path(name: ProblemSetName, problem_id: str) -> Path | None:
    """Get path to a specific problem.

    Args:
        name: Problem set name
        problem_id: Problem ID (e.g., "level4/103" or "pmpp/vectoradd_py")

    Returns:
        Path to problem file/directory, or None if not found
    """
    base_path = get_problems_path(name)
    if base_path is None:
        return None

    if name == "kernelbench":
        # Parse problem_id like "level4/103" or "level4/103_GroupedQueryAttention"
        parts = problem_id.split("/")
        if len(parts) != 2:
            return None

        level_str, problem_part = parts
        if not level_str.startswith("level"):
            level_str = f"level{level_str}"

        kb_root = base_path / "KernelBench"
        if not kb_root.exists():
            kb_root = base_path

        problem_dir = kb_root / level_str
        if not problem_dir.exists():
            return None

        # Find matching problem file
        problem_files = list(problem_dir.glob(f"{problem_part}*.py"))
        if not problem_files:
            # Try exact match
            exact = problem_dir / f"{problem_part}.py"
            if exact.exists():
                return exact
            return None

        return problem_files[0]

    elif name == "gpumode":
        # Parse problem_id like "pmpp/vectoradd_py"
        problems_root = base_path / "problems"
        if not problems_root.exists():
            problems_root = base_path

        problem_path = problems_root / problem_id
        if problem_path.exists() and problem_path.is_dir():
            return problem_path

        return None

    return None

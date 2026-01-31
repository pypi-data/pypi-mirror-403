"""Corpus management for Wafer CLI.

Download and manage documentation corpora for agent filesystem access.
"""

import re
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import httpx

CACHE_DIR = Path.home() / ".cache" / "wafer" / "corpora"

CorpusName = Literal["cuda", "cutlass", "hip", "amd"]


@dataclass
class RepoSource:
    """A single GitHub repo source within a corpus."""

    repo: str
    paths: list[str]
    branch: str = "main"


@dataclass
class CorpusConfig:
    """Configuration for a downloadable corpus."""

    name: CorpusName
    description: str
    source_type: Literal["nvidia_md", "github_repo", "github_multi_repo", "mixed"]
    urls: list[str] | None = None
    repo: str | None = None
    repo_paths: list[str] | None = None
    repos: list[RepoSource] | None = None  # For multi-repo corpora


CORPORA: dict[CorpusName, CorpusConfig] = {
    "cuda": CorpusConfig(
        name="cuda",
        description="CUDA Programming Guide and Best Practices",
        source_type="nvidia_md",
        urls=[
            "https://docs.nvidia.com/cuda/cuda-programming-guide/index.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/introduction.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/programming-model.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/cuda-platform.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/intro-to-cuda-cpp.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/nvcc.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/advanced-kernel-programming.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/advanced-host-programming.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/stream-ordered-memory-allocation.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/dynamic-parallelism.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/virtual-memory-management.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cluster-launch-control.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/graphics-interop.html",
            "https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/cpp-language-extensions.html",
            "https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html",
        ],
    ),
    "cutlass": CorpusConfig(
        name="cutlass",
        description="CUTLASS C++ documentation, examples, and tutorials",
        source_type="mixed",
        # Official NVIDIA CUTLASS documentation (scraped as markdown)
        urls=[
            "https://docs.nvidia.com/cutlass/latest/overview.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/functionality.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/terminology.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/fundamental_types.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/programming_guidelines.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/heuristics.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/efficient_gemm.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/pipeline.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/profiler.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/dependent_kernel_launch.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/blackwell_functionality.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/blackwell_cluster_launch_control.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/00_quickstart.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/01_layout.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/02_layout_algebra.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/03_tensor.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/04_algorithms.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/0t_mma_atom.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/0x_gemm_tutorial.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/0y_predication.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cute/0z_tma_tensors.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cutlass_3x_design.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/cutlass_3x_backwards_compatibility.html",
            "https://docs.nvidia.com/cutlass/latest/media/docs/cpp/gemm_api_3x.html",
        ],
        # NVIDIA/cutlass GitHub examples (excluding python/)
        repos=[
            RepoSource(
                repo="NVIDIA/cutlass",
                paths=["examples"],
                branch="main",
            ),
        ],
    ),
    "hip": CorpusConfig(
        name="hip",
        description="HIP programming guide and API reference",
        source_type="github_repo",
        repo="ROCm/HIP",
        repo_paths=["docs"],
    ),
    "amd": CorpusConfig(
        name="amd",
        description="AMD GPU kernel development (rocWMMA, CK, AITER, rocBLAS, HipKittens, vLLM)",
        source_type="github_multi_repo",
        repos=[
            # rocWMMA - wave matrix multiply-accumulate (WMMA) intrinsics
            RepoSource(
                repo="ROCm/rocWMMA",
                paths=["docs", "samples", "library/include"],
                branch="develop",
            ),
            # Composable Kernel - tile-based GPU programming
            RepoSource(
                repo="ROCm/composable_kernel",
                paths=["docs", "example", "tutorial", "include/ck_tile"],
                branch="develop",
            ),
            # AITER - AMD inference tensor runtime
            RepoSource(
                repo="ROCm/aiter",
                paths=["docs", "aiter/ops"],
            ),
            # MIOpen - deep learning primitives (deprecated, use rocm-libraries)
            RepoSource(
                repo="ROCm/MIOpen",
                paths=["docs"],
                branch="develop_deprecated",
            ),
            # rocBLAS - BLAS library (deprecated, use rocm-libraries)
            RepoSource(
                repo="ROCm/rocBLAS",
                paths=["docs"],
                branch="develop_deprecated",
            ),
            # hipBLASLt - lightweight BLAS (deprecated, use rocm-libraries)
            RepoSource(
                repo="ROCm/hipBLASLt",
                paths=["docs"],
                branch="develop_deprecated",
            ),
            # Tensile - GEMM code generator (deprecated, use rocm-libraries)
            RepoSource(
                repo="ROCm/Tensile",
                paths=["docs"],
                branch="develop_deprecated",
            ),
            # HipKittens - high-performance AMD kernels
            RepoSource(
                repo="HazyResearch/HipKittens",
                paths=["docs", "kernels", "include"],
            ),
            # vLLM AMD kernels
            RepoSource(
                repo="vllm-project/vllm",
                paths=["csrc/rocm"],
            ),
            # SGLang AMD kernels
            RepoSource(
                repo="sgl-project/sglang",
                paths=["3rdparty/amd"],
            ),
            # HuggingFace ROCm kernels
            RepoSource(
                repo="huggingface/hf-rocm-kernels",
                paths=["csrc", "hf_rocm_kernels", "docs"],
            ),
        ],
    ),
}


def _corpus_path(name: CorpusName) -> Path:
    """Get local path for corpus."""
    return CACHE_DIR / name


def _ensure_cache_dir() -> None:
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _url_to_filepath(url: str, base_dir: Path) -> Path:
    """Convert URL to local filepath preserving structure."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if path_parts[-1].endswith(".html"):
        path_parts[-1] = path_parts[-1].replace(".html", ".md")
    return base_dir / "/".join(path_parts)


class _HTMLToMarkdown(HTMLParser):
    """HTML to Markdown converter for NVIDIA documentation pages.

    Uses stdlib HTMLParser - requires subclassing due to callback-based API.
    The public interface is the functional `_html_to_markdown()` below.
    """

    def __init__(self) -> None:
        super().__init__()
        self.output: list[str] = []
        self.current_tag: str = ""
        self.in_code_block = False
        self.in_pre = False
        self.list_depth = 0
        self.ordered_list_counters: list[int] = []
        self.skip_content = False
        self.link_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.current_tag = tag
        attrs_dict = dict(attrs)

        # Skip script, style, nav, footer, header
        if tag in ("script", "style", "nav", "footer", "header", "aside"):
            self.skip_content = True
            return

        if tag == "h1":
            self.output.append("\n# ")
        elif tag == "h2":
            self.output.append("\n## ")
        elif tag == "h3":
            self.output.append("\n### ")
        elif tag == "h4":
            self.output.append("\n#### ")
        elif tag == "h5":
            self.output.append("\n##### ")
        elif tag == "h6":
            self.output.append("\n###### ")
        elif tag == "p":
            self.output.append("\n\n")
        elif tag == "br":
            self.output.append("\n")
        elif tag == "strong" or tag == "b":
            self.output.append("**")
        elif tag == "em" or tag == "i":
            self.output.append("*")
        elif tag == "code" and not self.in_pre:
            self.output.append("`")
            self.in_code_block = True
        elif tag == "pre":
            self.in_pre = True
            # Check for language hint in class
            lang = ""
            if class_attr := attrs_dict.get("class"):
                if "python" in class_attr.lower():
                    lang = "python"
                elif "cpp" in class_attr.lower() or "c++" in class_attr.lower():
                    lang = "cpp"
                elif "cuda" in class_attr.lower():
                    lang = "cuda"
            self.output.append(f"\n```{lang}\n")
        elif tag == "ul":
            self.list_depth += 1
            self.output.append("\n")
        elif tag == "ol":
            self.list_depth += 1
            self.ordered_list_counters.append(1)
            self.output.append("\n")
        elif tag == "li":
            indent = "  " * (self.list_depth - 1)
            if self.ordered_list_counters:
                num = self.ordered_list_counters[-1]
                self.output.append(f"{indent}{num}. ")
                self.ordered_list_counters[-1] += 1
            else:
                self.output.append(f"{indent}- ")
        elif tag == "a":
            self.link_href = attrs_dict.get("href")
            self.output.append("[")
        elif tag == "img":
            alt = attrs_dict.get("alt", "image")
            src = attrs_dict.get("src", "")
            self.output.append(f"![{alt}]({src})")
        elif tag == "blockquote":
            self.output.append("\n> ")
        elif tag == "hr":
            self.output.append("\n---\n")
        elif tag == "table":
            self.output.append("\n")
        elif tag == "th":
            self.output.append("| ")
        elif tag == "td":
            self.output.append("| ")
        elif tag == "tr":
            pass  # Handled in endtag

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "nav", "footer", "header", "aside"):
            self.skip_content = False
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.output.append("\n")
        elif tag == "strong" or tag == "b":
            self.output.append("**")
        elif tag == "em" or tag == "i":
            self.output.append("*")
        elif tag == "code" and not self.in_pre:
            self.output.append("`")
            self.in_code_block = False
        elif tag == "pre":
            self.in_pre = False
            self.output.append("\n```\n")
        elif tag == "ul":
            self.list_depth = max(0, self.list_depth - 1)
        elif tag == "ol":
            self.list_depth = max(0, self.list_depth - 1)
            if self.ordered_list_counters:
                self.ordered_list_counters.pop()
        elif tag == "li":
            self.output.append("\n")
        elif tag == "a":
            if self.link_href:
                self.output.append(f"]({self.link_href})")
            else:
                self.output.append("]")
            self.link_href = None
        elif tag == "p":
            self.output.append("\n")
        elif tag == "blockquote":
            self.output.append("\n")
        elif tag == "tr":
            self.output.append("|\n")
        elif tag == "thead":
            # Add markdown table separator after header row
            self.output.append("|---" * 10 + "|\n")

    def handle_data(self, data: str) -> None:
        if self.skip_content:
            return
        # Preserve whitespace in code blocks
        if self.in_pre:
            self.output.append(data)
        else:
            # Collapse whitespace outside code
            text = re.sub(r"\s+", " ", data)
            if text.strip():
                self.output.append(text)

    def get_markdown(self) -> str:
        """Get the converted markdown, cleaned up."""
        md = "".join(self.output)
        # Clean up excessive newlines
        md = re.sub(r"\n{3,}", "\n\n", md)
        # Clean up empty table separators
        md = re.sub(r"\|---\|---.*\|\n(?!\|)", "", md)
        return md.strip()


def _html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown."""
    parser = _HTMLToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


def _download_nvidia_md(config: CorpusConfig, dest: Path, verbose: bool = True) -> int:
    """Download NVIDIA docs and convert HTML to Markdown.

    NVIDIA's .md endpoint no longer works, so we scrape HTML and convert to markdown.
    """
    assert config.urls is not None
    downloaded = 0
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for url in config.urls:
            filepath = _url_to_filepath(url, dest)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            try:
                # Fetch HTML page directly
                resp = client.get(url)
                resp.raise_for_status()

                # Convert HTML to Markdown
                markdown = _html_to_markdown(resp.text)

                # Add source URL as header
                content = f"<!-- Source: {url} -->\n\n{markdown}"
                filepath.write_text(content)
                downloaded += 1
                if verbose:
                    print(f"  ✓ {filepath.relative_to(dest)}")
            except httpx.HTTPError as e:
                if verbose:
                    print(f"  ✗ {url}: {e}")
    return downloaded


def _extract_matching_files(
    tar: tarfile.TarFile,
    repo_paths: list[str],
    dest: Path,
    verbose: bool,
) -> int:
    """Extract files matching repo_paths from tarball."""
    downloaded = 0
    for member in tar.getmembers():
        if not member.isfile():
            continue
        rel_path = "/".join(member.name.split("/")[1:])
        if not any(rel_path.startswith(rp) for rp in repo_paths):
            continue
        target = dest / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        src = tar.extractfile(member)
        if src:
            target.write_bytes(src.read())
            downloaded += 1
            if verbose:
                print(f"  ✓ {rel_path}")
    return downloaded


def _download_single_github_repo(
    client: httpx.Client,
    repo: str,
    repo_paths: list[str],
    dest: Path,
    branch: str = "main",
    verbose: bool = True,
) -> int:
    """Download specific paths from a single GitHub repo."""
    tarball_url = f"https://api.github.com/repos/{repo}/tarball/{branch}"
    if verbose:
        print(f"  Fetching {repo}...")
    resp = client.get(tarball_url)
    resp.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = Path(tmp.name)
    try:
        with tarfile.open(tmp_path, "r:gz") as tar:
            return _extract_matching_files(tar, repo_paths, dest, verbose)
    finally:
        tmp_path.unlink()


def _download_github_repo(config: CorpusConfig, dest: Path, verbose: bool = True) -> int:
    """Download specific paths from GitHub repo."""
    assert config.repo is not None
    assert config.repo_paths is not None
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        return _download_single_github_repo(
            client, config.repo, config.repo_paths, dest, verbose=verbose
        )


def _download_github_multi_repo(config: CorpusConfig, dest: Path, verbose: bool = True) -> int:
    """Download specific paths from multiple GitHub repos."""
    assert config.repos is not None
    downloaded = 0
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        for repo_source in config.repos:
            repo_name = repo_source.repo.split("/")[-1]
            repo_dest = dest / repo_name
            repo_dest.mkdir(parents=True, exist_ok=True)
            try:
                count = _download_single_github_repo(
                    client,
                    repo_source.repo,
                    repo_source.paths,
                    repo_dest,
                    branch=repo_source.branch,
                    verbose=verbose,
                )
                downloaded += count
            except httpx.HTTPError as e:
                if verbose:
                    print(f"  ✗ {repo_source.repo}: {e}")
    return downloaded


def _download_mixed(config: CorpusConfig, dest: Path, verbose: bool = True) -> int:
    """Download from mixed sources (NVIDIA docs + GitHub repos)."""
    total = 0

    # Download NVIDIA markdown docs (urls)
    if config.urls:
        if verbose:
            print("  [NVIDIA docs]")
        total += _download_nvidia_md(config, dest, verbose)

    # Download GitHub repos
    if config.repos:
        if verbose:
            print("  [GitHub repos]")
        total += _download_github_multi_repo(config, dest, verbose)

    return total


def download_corpus(name: CorpusName, force: bool = False, verbose: bool = True) -> Path:
    """Download a corpus to local cache.

    Args:
        name: Corpus name
        force: Re-download even if exists
        verbose: Print progress

    Returns:
        Path to downloaded corpus

    Raises:
        ValueError: If corpus name is unknown
        httpx.HTTPError: If download fails
    """
    if name not in CORPORA:
        raise ValueError(f"Unknown corpus: {name}. Available: {list(CORPORA.keys())}")
    config = CORPORA[name]
    dest = _corpus_path(name)
    if dest.exists() and not force:
        if verbose:
            print(f"Corpus '{name}' already exists at {dest}")
            print("Use --force to re-download")
        return dest
    _ensure_cache_dir()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    if verbose:
        print(f"Downloading {name}: {config.description}")
    if config.source_type == "nvidia_md":
        count = _download_nvidia_md(config, dest, verbose)
    elif config.source_type == "github_repo":
        count = _download_github_repo(config, dest, verbose)
    elif config.source_type == "github_multi_repo":
        count = _download_github_multi_repo(config, dest, verbose)
    elif config.source_type == "mixed":
        count = _download_mixed(config, dest, verbose)
    else:
        raise ValueError(f"Unknown source type: {config.source_type}")
    if verbose:
        print(f"Downloaded {count} files to {dest}")
    return dest


def sync_corpus(name: CorpusName, verbose: bool = True) -> Path:
    """Sync (re-download) a corpus.

    Args:
        name: Corpus name
        verbose: Print progress

    Returns:
        Path to synced corpus
    """
    return download_corpus(name, force=True, verbose=verbose)


def list_corpora(verbose: bool = True) -> dict[CorpusName, bool]:
    """List available corpora and their download status.

    Returns:
        Dict of corpus name -> is_downloaded
    """
    result: dict[CorpusName, bool] = {}
    for name, config in CORPORA.items():
        path = _corpus_path(name)
        exists = path.exists()
        result[name] = exists
        if verbose:
            status = "✓" if exists else " "
            print(f"[{status}] {name}: {config.description}")
            if exists:
                file_count = sum(1 for _ in path.rglob("*") if _.is_file())
                print(f"    {path} ({file_count} files)")
    return result


def get_corpus_path(name: CorpusName) -> Path | None:
    """Get path to downloaded corpus, or None if not downloaded.

    Args:
        name: Corpus name

    Returns:
        Path if downloaded, None otherwise
    """
    if name not in CORPORA:
        return None
    path = _corpus_path(name)
    return path if path.exists() else None

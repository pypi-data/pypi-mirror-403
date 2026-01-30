import subprocess
from collections.abc import Generator
from pathlib import Path


def git_root() -> Path:
    """Return the root directory of the git repository."""
    output = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip()
    return Path(output.decode("utf-8"))


def git_ls_files(path: Path) -> Generator[str, None, None]:
    """Yield files in the git repository one at a time."""
    process = subprocess.Popen(
        [
            "git",
            "ls-files",
            "--cached",
            "--deleted",
            "--others",
            "--exclude-standard",
        ],
        cwd=path,
        stdout=subprocess.PIPE,
        text=True,
    )

    assert process.stdout is not None
    for line in process.stdout:
        yield line.strip()

    process.stdout.close()
    process.wait()


def git_ls_changes(path: Path) -> Generator[str, None, None]:
    process = subprocess.Popen(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        cwd=path,
        stdout=subprocess.PIPE,
        text=True,
    )

    assert process.stdout is not None
    for line in process.stdout:
        yield line.strip().split(" ", 1)[1]

    process.stdout.close()
    process.wait()


def git_diff_stream(path: Path, *diff_args: str) -> Generator[str, None, None]:
    process = subprocess.Popen(
        ["git", "diff", "--no-ext-diff"] + list(diff_args),
        cwd=path,
        stdout=subprocess.PIPE,
        text=True,
    )

    assert process.stdout is not None
    yield from process.stdout

    process.stdout.close()
    process.wait()

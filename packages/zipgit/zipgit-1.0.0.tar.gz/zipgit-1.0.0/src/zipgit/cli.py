import logging
import subprocess
import zipfile
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from pathspec import PathSpec
from rich.logging import RichHandler
from rich.progress import track

from zipgit import __version__

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(show_path=False)],
)
logger = logging.getLogger(__name__)

# Metadata marker added to zip files created by this tool
ZIPGIT_MARKER = "CREATED_BY_ZIPGIT"

app = typer.Typer(
    name="ZipGit",
    help="CLI tool for zipping a git repo and excluding .gitignore and untracked files",
    no_args_is_help=False,
    add_completion=False,
)


@app.command("zip")
def zip(
    op_dir: Annotated[
        Path,
        typer.Option(
            "--dir",
            "-d",
            help=f"Directory to zip (default: current working directory `{Path.cwd()}`)",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=False,
            readable=True,
            resolve_path=True,
            default_factory=Path.cwd,
            show_default=False,
        ),
    ],
    op_gitignore: Annotated[
        Path | None,
        typer.Option(
            "--gitignore",
            "-g",
            help="Name of the gitignore file to use (default: .gitignore in target directory)",
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            show_default=False,
        ),
    ] = None,
    op_include_untracked: Annotated[
        bool,
        typer.Option(
            "--untracked",
            "-u",
            help="Include untracked files in the zip (default: prompt if untracked files are found)",
        ),
    ] = False,
    op_zip_name: Annotated[
        Path | None,
        typer.Option(
            "--name",
            "-n",
            help=f"Name of the output zip file (default: name of the directory `{Path.cwd().name}.zip`)",
        ),
    ] = None,
    op_yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Automatic yes to prompts; assume 'yes' as answer to all prompts and run non-interactively.",
        ),
    ] = False,
):
    """Zip a git repository excluding .gitignore and untracked files."""

    logger.info(f"ZipGit v{__version__}")

    base_path = op_dir

    # Resolve gitignore path relative to target directory if not provided
    if op_gitignore is None:
        op_gitignore = base_path / ".gitignore"

    # Output zip file name
    if op_zip_name is None:
        date_now = datetime.now().strftime("%Y.%m.%d.%H%M%S")
        op_zip_name = Path.cwd() / f"{base_path.name}_{date_now}.zip"

    # Check if directory is a git repository
    is_git_repo = check_git_repo(base_path)
    if not is_git_repo:
        logger.warning(f"Directory is not a git repository: {base_path}")
        if op_yes:
            logger.info("Proceeding due to --yes flag...")
        else:
            typer.confirm("Do you want to proceed?", default=False, abort=True)
            logger.info("Proceeding...")

    # Check gitignore file
    has_gitignore = op_gitignore.is_file()
    if not has_gitignore:
        logger.warning(f"Gitignore file not found: {op_gitignore}")
        if op_yes:
            logger.info("Proceeding without a gitignore file due to --yes flag...")
        else:
            typer.confirm("Do you want to proceed without a gitignore file?", default=False, abort=True)
            logger.info("Proceeding without a gitignore file...")

    # Scan directory
    logger.info(f"Scanning directory: {base_path}")
    total_files_in_dir = get_total_files_in_dir(base_path)
    logger.info(f"{total_files_in_dir} files found")

    # Get ignore spec from gitignore file
    ignore_spec = get_ignore_spec(op_gitignore) if has_gitignore else None

    # Get untracked files
    untracked_files = get_untracked_files(base_path) if is_git_repo else None

    # Handle untracked files
    if untracked_files is not None and len(untracked_files) > 0:
        if op_include_untracked:
            logger.info(f"Including {len(untracked_files)} untracked files in the zip")
        else:
            # Ignore untracked files
            ignore_spec = add_untracked_files_to_ignore_spec(base_path, ignore_spec, untracked_files)
            logger.warning(
                f"Found {len(untracked_files)} untracked files in the repository. "
                "To include them, use the --untracked flag."
            )

    # Always ignore .git directory
    ignore_spec = add_git_dir_to_ignore_spec(ignore_spec)

    # Get files to zip
    files_to_zip = get_files_to_zip(base_path=base_path, ignore_spec=ignore_spec)
    files_to_zip_total = len(files_to_zip)

    logger.info(f"{files_to_zip_total} files to be zipped")

    # Confirm before creating zip file
    if not op_yes:
        typer.confirm(f"Proceed to create zip file {op_zip_name}?", default=True, abort=True)
    else:
        logger.info("Proceeding to create zip file due to --yes flag...")

    # Create zip file and add files
    try:
        with create_zip_file(op_zip_name) as zip_file:
            for file_path in track(
                files_to_zip,
                description="Zipping files...",
                total=files_to_zip_total,
            ):
                if file_path.is_file() and file_path != op_zip_name:
                    # logger.debug(f"Adding file to zip: {file_path}")
                    add_file_to_zip(zip_file, file_path, base_path)
    except Exception:
        # Clean up partial zip file on failure
        if op_zip_name.exists():
            op_zip_name.unlink()
        raise

    logger.info(f"Zip file created: {op_zip_name}")


def check_git_repo(path: Path) -> bool:
    """Check if the given path is a git repository."""

    return (path / ".git").is_dir()


def get_total_files_in_dir(path: Path) -> int:
    """Get total number of files in the given directory."""

    return sum(len(filenames) for _, _, filenames in path.walk())


def get_ignore_spec(gitignore_path: Path) -> PathSpec:
    """Read gitignore file and return PathSpec object."""

    with open(gitignore_path) as f:
        spec = PathSpec.from_lines("gitignore", f)

    return spec


def get_untracked_files(path: Path) -> set[Path]:
    """Get untracked files in the given path using git."""

    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        untracked_files = {path / line.strip() for line in result.stdout.splitlines()}

        # Exclude gitzip created files from untracked files
        untracked_files = {f for f in untracked_files if not is_zipgit_file(f)}

        return untracked_files
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking untracked files: {e}")
        return set()


def add_untracked_files_to_ignore_spec(
    base_path: Path, ignore_spec: PathSpec | None, untracked_files: set[Path]
) -> PathSpec:
    """Add untracked files to the ignore spec."""

    untracked_patterns = [str(file.relative_to(base_path)) for file in untracked_files]

    if ignore_spec is None:
        ignore_spec = PathSpec.from_lines("gitignore", untracked_patterns)
    else:
        ignore_spec += PathSpec.from_lines("gitignore", untracked_patterns)

    return ignore_spec


def add_git_dir_to_ignore_spec(ignore_spec: PathSpec | None) -> PathSpec:
    """Add .git directory to the ignore spec."""

    git_pattern = [".git/"]

    if ignore_spec is None:
        ignore_spec = PathSpec.from_lines("gitignore", git_pattern)
    else:
        ignore_spec += PathSpec.from_lines("gitignore", git_pattern)

    return ignore_spec


def get_files_to_zip(base_path: Path, ignore_spec: PathSpec | None) -> list[Path]:
    """Get list of files to zip based on the ignore spec."""

    files_to_zip: list[Path] = []

    for dir_path, dirs, filenames in base_path.walk():
        # Prune ignored directories to avoid descending into them
        if ignore_spec is not None:
            relative_dir = dir_path.relative_to(base_path)
            dirs[:] = [d for d in dirs if not ignore_spec.match_file(str(relative_dir / d) + "/")]

        for filename in filenames:
            file_path: Path = dir_path / filename
            relative_path = file_path.relative_to(base_path)

            if ignore_spec is not None and ignore_spec.match_file(str(relative_path)):
                # logger.debug(f"Excluding file: {file_path}")
                continue

            if is_zipgit_file(file_path):
                # logger.debug(f"Excluding zipgit-created file: {file_path.name}")
                continue

            # logger.debug(f"Including file: {file_path}")
            files_to_zip.append(file_path)

    return files_to_zip


def is_zipgit_file(file_path: Path) -> bool:
    """Check if a file is a zip created by zipgit by reading its comment."""

    if file_path.suffix.lower() != ".zip":
        return False

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            return zf.comment.decode("utf-8") == ZIPGIT_MARKER
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError):
        return False


@contextmanager
def create_zip_file(file: Path) -> Generator[zipfile.ZipFile]:
    """Create a zip file with the zipgit marker comment."""

    zip_file = zipfile.ZipFile(file, "w", zipfile.ZIP_DEFLATED)
    try:
        zip_file.comment = ZIPGIT_MARKER.encode("utf-8")
        yield zip_file
    finally:
        zip_file.close()


def add_file_to_zip(zip_file: zipfile.ZipFile, file_path: Path, base_path: Path) -> None:
    """Add a file to the zip file with path relative to base path."""

    zip_file.write(file_path, file_path.relative_to(base_path))


if __name__ == "__main__":
    app()

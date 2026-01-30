import os
import sys
from pathlib import Path
from textwrap import dedent

import click
from pydantic import ValidationError

from . import git
from .config import CONFIG_FILENAME, CONFIG_FILENAME_PREFIX, ConfigModel, ConfigModels
from .matches import match_diff, match_files
from .printer import MatchesPrinter


# Most often used as `pullapprove`
# @click.group(invoke_without_command=True)
@click.group()
@click.version_option(package_name="pullapprove")
@click.pass_context
def cli(ctx: click.Context) -> None:
    pass
    # if ctx.invoked_subcommand is None:
    #     ctx.invoke(review)


# Most often used as `pullapprove review`
# @cli.command()
# @click.pass_context
# def review(ctx):
#     """
#     Show changed files that need review
#     """

#     # What might we be reviewing?
#     # - PR number / url
#     # - branch
#     # - diff

#     # This is an alias for files --changed
#     ctx.invoke(files, changed=True)


@cli.command()
@click.option("--filename", default=CONFIG_FILENAME, help="Configuration filename")
def init(filename: str) -> None:
    """Create a new CODEREVIEW.toml"""
    config_path = Path(filename)
    if config_path.exists():
        click.secho(f"{CONFIG_FILENAME} already exists!", fg="red")
        sys.exit(1)

    # Could we use blame to guess?
    # go straight to agent?
    # gh auth status can give us the user? or ask what's their username?
    # keep it simple - agent can do more when I get to it

    contents = """
    [[scopes]]
    name = "default"
    paths = ["**/*"]
    request = 1
    require = 1
    reviewers = ["<YOU>"]

    [[scopes]]
    name = "pullapprove"
    paths = ["**/CODEREVIEW.toml"]
    request = 1
    require = 1
    reviewers = ["<YOU>"]
    """
    config_path.write_text(dedent(contents).strip() + "\n")
    click.secho(f"Created {filename}")


@cli.command()
@click.option("--quiet", is_flag=True)
def check(quiet: bool) -> ConfigModels:
    """
    Validate configuration files
    """

    if not quiet:
        if Path(".pullapprove.yml").exists():
            click.secho(
                f"{click.style('[Warning]', fg='yellow')} This repo still contains a PullApprove v3 config file (.pullapprove.yml). Consider migrating it to PullApprove v5."
            )
        if Path("CODEOWNERS").exists():
            click.secho(
                f"{click.style('[Warning]', fg='yellow')} This repo still contains a CODEOWNERS file. Consider migrating it to PullApprove v5."
            )
        if Path("docs/CODEOWNERS").exists():
            click.secho(
                f"{click.style('[Warning]', fg='yellow')} This repo still contains a CODEOWNERS file (docs/CODEOWNERS). Consider migrating it to PullApprove v5."
            )
        if Path(".github/CODEOWNERS").exists():
            click.secho(
                f"{click.style('[Warning]', fg='yellow')} This repo still contains a CODEOWNERS file (.github/CODEOWNERS). Consider migrating it to PullApprove v5."
            )

    errors = {}
    configs = ConfigModels(root={})

    for root, _, files in os.walk("."):
        for f in files:
            if f.startswith(CONFIG_FILENAME_PREFIX):
                config_path = Path(root) / f

                if not quiet:
                    click.echo(config_path, nl=False)
                try:
                    configs.add_config(
                        ConfigModel.from_filesystem(config_path), config_path
                    )

                    if not quiet:
                        click.secho(" -> OK", fg="green")
                except ValidationError as e:
                    if not quiet:
                        click.secho(" -> ERROR", fg="red")

                    errors[config_path] = e

    for path, error in errors.items():
        click.secho(str(path), fg="red")
        print(error)

    if errors:
        raise click.Abort("Configuration validation failed.")

    if not configs and not quiet:
        click.secho("No CODEREVIEW.toml files found.", fg="red")
        sys.exit(1)

    return configs


@cli.command()
@click.option("--changed", is_flag=True, help="Show only changed files")
@click.option("--staged", is_flag=True, help="Show only staged files")
@click.option("--diff", is_flag=True, help="Show diff content with matches")
@click.option(
    "--by-scope", is_flag=True, help="Organize output by scope instead of by path"
)
@click.option(
    "--scope",
    multiple=True,
    help="Filter to show only files matching these scopes (can be used multiple times)",
)
@click.argument("paths", nargs=-1, type=click.Path())
@click.pass_context
def match(
    ctx: click.Context,
    changed: bool,
    staged: bool,
    diff: bool,
    by_scope: bool,
    scope: tuple[str, ...],
    paths: tuple[str, ...],
) -> None:
    """
    Show files and their matching scopes

    If PATHS are provided, only those specific paths will be matched.
    Directories will be recursively expanded to include all files within them.
    Otherwise, all files in the repository will be matched.
    """
    configs = ctx.invoke(check, quiet=True)

    if not configs:
        click.secho("No valid configurations found.", fg="red")
        raise click.Abort("No configurations to check.")

    if paths:
        # When specific paths are provided, match only those paths
        if diff or staged or changed:
            click.secho(
                "Cannot use --diff, --staged, or --changed with specific paths.",
                fg="red",
            )
            raise click.Abort("Conflicting options.")

        # Get all git-tracked files and filter by provided paths
        all_git_files = set(git.git_ls_files(Path(".")))
        expanded_paths = []

        for path_str in paths:
            path = Path(path_str)
            if path.is_dir():
                # Filter git files that are within this directory
                dir_prefix = str(path) + "/"
                for git_file in all_git_files:
                    if git_file.startswith(dir_prefix) or git_file == str(path):
                        expanded_paths.append(git_file)
            elif path.is_file() or str(path) in all_git_files:
                # Include if it's a git-tracked file
                if str(path) in all_git_files:
                    expanded_paths.append(str(path))
                else:
                    click.secho(f"File not tracked by git: {path}", fg="yellow")
            else:
                click.secho(
                    f"Path does not exist or not tracked by git: {path}", fg="yellow"
                )

        matches = match_files(configs, iter(expanded_paths))
        all_files = expanded_paths
    elif diff or staged:
        # Use git diff for these options
        diff_args = []
        if staged:
            diff_args.append("--staged")

        diff_stream = git.git_diff_stream(Path("."), *diff_args)
        diff_results = match_diff(configs, diff_stream)
        matches = diff_results.matches
        # For diff mode, we only show files in the diff
        all_files = None
    elif changed:
        iterator = git.git_ls_changes(Path("."))
        matches = match_files(configs, iterator)
        # For changed mode, we only show changed files
        all_files = None
    else:
        # For normal mode, show all files to see gaps
        iterator = git.git_ls_files(Path("."))
        matches = match_files(configs, iterator)
        # Get all files again for the printer
        all_files = list(git.git_ls_files(Path(".")))

    printer = MatchesPrinter(matches, all_files=all_files)
    if by_scope:
        printer.print_by_scope(scope_filter=scope)
    else:
        printer.print_by_path(scope_filter=scope)


@cli.command()
@click.option(
    "--check",
    "check_flag",
    is_flag=True,
    help="Exit with non-zero status if coverage is incomplete",
)
@click.argument("path", type=click.Path(exists=True), default=".")
@click.pass_context
def coverage(ctx: click.Context, path: str, check_flag: bool) -> None:
    """
    Calculate file coverage for review scopes
    """
    configs = ctx.invoke(check, quiet=True)

    num_matched = 0
    num_total = 0
    uncovered_files = []

    # First, get all files to know the total count for progress bar
    all_files = list(git.git_ls_files(Path(path)))

    if not all_files:
        click.echo("No files found")
        return

    # Process files with progress bar
    with click.progressbar(
        all_files, label="Analyzing coverage", show_percent=True, show_pos=True
    ) as files:
        # Use match_files to get proper scope matching including code patterns
        results = match_files(configs, iter(files))

        # Count files with and without scope matches
        for path_str, path_match in results.paths.items():
            if path_match.scopes:
                num_matched += 1
            else:
                uncovered_files.append(path_str)
            num_total += 1

        # Also count files that weren't in the results (no scope matches at all)
        for f in all_files:
            if f not in results.paths:
                uncovered_files.append(f)
                num_total += 1

    percentage = (num_matched / num_total) * 100

    # Display coverage statistics
    if num_matched == num_total:
        click.secho(f"\n✓ {num_matched}/{num_total} files covered (100.0%)", fg="green")
    else:
        # Show uncovered files
        if uncovered_files:
            click.echo("\nUncovered files:")
            for file in sorted(uncovered_files)[:10]:  # Show first 10
                click.echo(f"  - {file}")
            if len(uncovered_files) > 10:
                click.echo(f"  ...and {len(uncovered_files) - 10} more")

        click.secho(
            f"\n{num_matched}/{num_total} files covered ({percentage:.1f}%)",
            fg="yellow",
        )

    if check_flag and num_matched != num_total:
        sys.exit(1)


# list - find open PRs, find status url and send json request (needs PA token)

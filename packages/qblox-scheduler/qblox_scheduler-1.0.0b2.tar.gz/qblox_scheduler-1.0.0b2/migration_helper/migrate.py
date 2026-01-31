# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""Migration CLI for scripts and config files."""

import sys
from importlib import resources
from pathlib import Path

from .utils import find_and_replace_in_file


def get_gritdir_path() -> str:
    """Get the path to the grit directory."""
    return str(resources.files("migration_helper").joinpath(".grit"))


try:
    import rich
    import typer
    from gritql import run

except ImportError:

    def app() -> None:
        """Fallback app when CLI dependencies are missing."""
        print("CLI dependencies not installed")
        print('To use the CLI tool, please run: pip install "qblox-scheduler[cli]"')
        sys.exit(1)

else:
    app = typer.Typer(
        name="qblox-scheduler",
        help="Qblox Scheduler CLI tool for file migration.",
        rich_markup_mode="markdown",
        no_args_is_help=True,
        add_completion=False,
    )

    @app.command()
    def migrate_scripts(
        path: str = typer.Argument(
            ..., help="Path to the Python file, notebook or directory to migrate"
        ),
        diff: bool = typer.Option(
            False,
            "--dry-run",
            help="Show the changes that would be made without applying them.",
        ),
    ) -> None:
        """
        Migrate Python script files (*.py, *.ipynb) from 'quantify_scheduler' to 'qblox_scheduler'.

        This command updates import statements, class references, and other code patterns
        to use the new qblox_scheduler package instead of the deprecated quantify_scheduler.

        Parameters
        ----------
        path : str
            Path to Python file or directory containing files to migrate
        diff : bool
            If True, shows changes without applying them (dry-run mode)

        Returns
        -------
        None

        """
        if not diff:
            rich.print(
                "[yellow]Migration will overwrite existing Python files "
                "and notebooks. "
                "Please backup your current python files before proceeding "
                "or use the --dry-run option to preview changes.[/yellow]"
            )
            if not typer.confirm("Do you want to proceed with the migration?"):
                rich.print("[blue]Migration cancelled.[/blue]")
                raise typer.Exit(0)
        else:
            rich.print("[blue]Running in dry-run mode - no files will be modified.[/blue]")

        args = [path]

        if diff:
            args.append("--dry-run")

        final_code = run.apply_pattern(
            "qblox_migrate",
            args,
            grit_dir=get_gritdir_path(),
        )

        raise typer.Exit(code=final_code)

    CONFIG_FILE_ARGUMENT = typer.Argument(
        ...,
        exists=True,  # required argument
        file_okay=True,  # path cannot be a file
        dir_okay=True,  # path must be a directory
        writable=True,
        readable=True,
        resolve_path=True,  # convert to absolute path
        help="Path to the configuration file (*.json,) or directory containing "
        "configuration files to migrate.",
    )

    @app.command()
    def migrate_configs(
        path: Path = CONFIG_FILE_ARGUMENT,
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help="Enable verbose output, listing all files that were or were not migrated.",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show the changes that would be made without applying them.",
        ),
    ) -> None:
        """
        Migrate configuration files (*.json, *.yaml, *.yml) from 'quantify_scheduler' to
        'qblox_scheduler'.

        This command updates references in config files
        to use the new qblox_scheduler package instead of the deprecated quantify_scheduler.

        Parameters
        ----------
        path : Path
            Path to configuration file or directory containing files to migrate
        verbose : bool
            If True, shows detailed output listing all migrated and non-migrated files
        dry_run : bool
            If True, shows changes without applying them (dry-run mode)

        Returns
        -------
        None

        """
        if not dry_run:
            rich.print(
                "[yellow]Migration will overwrite existing configuration "
                "files. Please backup your current configurations before proceeding "
                "or use the --dry-run option to preview changes.[/yellow]"
            )
            if not typer.confirm("Do you want to proceed with the migration?"):
                rich.print("[blue]Migration cancelled.[/blue]")
                raise typer.Exit(0)
        else:
            rich.print("[blue]Running in dry-run mode - no files will be modified.[/blue]")

        if path.is_file():
            if path.suffix.lower() not in [".json", ".yaml", ".yml"]:
                rich.print(f"Error: {path} is not a supported configuration file type.")
                rich.print("Supported types: *.json, *.yaml, *.yml")
                raise typer.Exit(1)
            config_files = [path]
        else:
            config_files = (
                list(path.rglob("*.json")) + list(path.rglob("*.yaml")) + list(path.rglob("*.yml"))
            )

        if not config_files:
            rich.print("No configuration files found to migrate.")
            raise typer.Exit(-1)
        migrated_files, non_migrated_files = find_and_replace_in_file(
            config_files, verbose, dry_run
        )
        if not migrated_files:
            action = "would be made" if dry_run else "were"
            rich.print(f"No changes {action} to any files.")
            return

        action = "Analysis complete!" if dry_run else "Migration successful!"
        rich.print(action)

        if verbose:
            action_tense = "would be" if dry_run else "were"
            migrated_list = f"The following files {action_tense} migrated: {migrated_files}"
            not_migrated_list = (
                f"The following files {action_tense} [bold]NOT[/bold] be migrated: "
                f"{non_migrated_files}"
            )
            rich.print(migrated_list)
            rich.print(not_migrated_list)
        else:
            action_tense = "would be" if dry_run else "were"
            summary = (
                f"{len(migrated_files)} files {action_tense} migrated and "
                f"{len(non_migrated_files)} files {action_tense} [bold]NOT[/bold] be migrated"
            )
            rich.print(summary)


if __name__ == "__main__":
    app()

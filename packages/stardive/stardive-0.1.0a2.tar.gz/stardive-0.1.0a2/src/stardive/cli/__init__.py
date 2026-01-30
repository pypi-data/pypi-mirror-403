from __future__ import annotations

import sys

import click

from stardive import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """Stardive CLI for audit, lineage, and replay operations."""


@cli.command("version")
def version_cmd() -> None:
    """Print the installed Stardive version."""
    click.echo(__version__)


@cli.group()
def audit() -> None:
    """Audit operations."""


@audit.command("show")
@click.argument("run_id")
def audit_show(run_id: str) -> None:
    """Show audit record for a run."""
    click.echo(f"Audit CLI is not yet implemented. run_id={run_id}")


@cli.group()
def lineage() -> None:
    """Lineage operations."""


@lineage.command("trace")
@click.argument("run_id")
def lineage_trace(run_id: str) -> None:
    """Trace lineage for a run."""
    click.echo(f"Lineage CLI is not yet implemented. run_id={run_id}")


@cli.group()
def replay() -> None:
    """Replay operations."""


@replay.command("run")
@click.argument("run_id")
def replay_run(run_id: str) -> None:
    """Replay a run from snapshots."""
    click.echo(f"Replay CLI is not yet implemented. run_id={run_id}")


@cli.group()
def artifact() -> None:
    """Artifact operations."""


@artifact.command("get")
@click.argument("artifact_id")
def artifact_get(artifact_id: str) -> None:
    """Fetch an artifact by ID."""
    click.echo(f"Artifact CLI is not yet implemented. artifact_id={artifact_id}")


def main() -> None:
    """Entry point for the stardive CLI."""
    try:
        cli(standalone_mode=True)
    except click.ClickException as exc:
        exc.show()
        sys.exit(exc.exit_code)

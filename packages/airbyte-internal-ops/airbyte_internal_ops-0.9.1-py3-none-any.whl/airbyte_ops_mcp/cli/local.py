# Copyright (c) 2025 Airbyte, Inc., all rights reserved.
"""CLI commands for local Airbyte monorepo operations.

Commands:
    airbyte-ops local connector list - List connectors in the monorepo
    airbyte-ops local connector info - Get metadata for a single connector
    airbyte-ops local connector bump-version - Bump connector version
    airbyte-ops local connector qa - Run QA checks on a connector
    airbyte-ops local connector qa-docs-generate - Generate QA checks documentation
    airbyte-ops local connector changelog check - Check changelog entries for issues
    airbyte-ops local connector changelog fix - Fix changelog entry dates
    airbyte-ops local connector enterprise-stub check - Validate enterprise stub entries
    airbyte-ops local connector enterprise-stub sync - Sync stub from connector metadata
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal

import yaml
from cyclopts import App, Parameter
from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console

from airbyte_ops_mcp.airbyte_repo.bump_version import (
    ConnectorNotFoundError,
    InvalidVersionError,
    VersionNotFoundError,
    bump_connector_version,
)
from airbyte_ops_mcp.airbyte_repo.changelog_fix import (
    ChangelogCheckResult,
    ChangelogFixResult,
    check_all_changelogs,
    check_changelog,
    fix_all_changelog_dates,
    fix_changelog_dates,
)
from airbyte_ops_mcp.airbyte_repo.list_connectors import (
    CONNECTOR_PATH_PREFIX,
    METADATA_FILE_NAME,
    _detect_connector_language,
    get_connectors_with_local_cdk,
)
from airbyte_ops_mcp.cli._base import app
from airbyte_ops_mcp.cli._shared import error_console, exit_with_error, print_json
from airbyte_ops_mcp.connector_ops.utils import Connector
from airbyte_ops_mcp.connector_qa.checks import ENABLED_CHECKS
from airbyte_ops_mcp.connector_qa.consts import CONNECTORS_QA_DOC_TEMPLATE_NAME
from airbyte_ops_mcp.connector_qa.models import (
    Check,
    CheckCategory,
    CheckStatus,
    Report,
)
from airbyte_ops_mcp.connector_qa.utils import (
    get_all_connectors_in_directory,
    remove_strict_encrypt_suffix,
)
from airbyte_ops_mcp.mcp.github_repo_ops import list_connectors_in_repo
from airbyte_ops_mcp.registry.connector_stubs import (
    CONNECTOR_STUBS_FILE,
    ConnectorStub,
    find_stub_by_connector,
    load_local_stubs,
    save_local_stubs,
)

console = Console()

OutputFormat = Literal["csv", "lines", "json-gh-matrix"]

# Support level mapping: keyword -> integer value
# Higher values indicate higher support/quality levels
SUPPORT_LEVEL_MAP: dict[str, int] = {
    "archived": 100,
    "community": 200,
    "certified": 300,
}

# Reverse mapping for input parsing
SUPPORT_LEVEL_KEYWORDS = set(SUPPORT_LEVEL_MAP.keys())


def _parse_support_level(value: str) -> int:
    """Parse a support level string to an integer.

    Accepts either an integer string ("200") or a keyword ("certified").
    """
    value = value.strip().lower()
    if value in SUPPORT_LEVEL_MAP:
        return SUPPORT_LEVEL_MAP[value]
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"Invalid support level: {value}. "
            f"Use an integer or one of: {', '.join(SUPPORT_LEVEL_KEYWORDS)}"
        ) from None


def _get_connector_support_level(connector_dir: Path) -> int | None:
    """Read support level from connector's metadata.yaml and return as integer."""
    metadata_file = connector_dir / METADATA_FILE_NAME
    if not metadata_file.exists():
        return None
    metadata = yaml.safe_load(metadata_file.read_text())
    support_level_str = metadata.get("data", {}).get("supportLevel")
    if support_level_str and support_level_str.lower() in SUPPORT_LEVEL_MAP:
        return SUPPORT_LEVEL_MAP[support_level_str.lower()]
    return None


def _parse_connector_types(value: str) -> set[str]:
    """Parse connector types from CSV or newline-delimited string."""
    types = set()
    for item in value.replace(",", "\n").split("\n"):
        item = item.strip().lower()
        if item:
            if item not in ("source", "destination"):
                raise ValueError(
                    f"Invalid connector type: {item}. Must be 'source' or 'destination'."
                )
            types.add(item)
    return types


def _get_connector_type(connector_name: str) -> str:
    """Derive connector type from name prefix."""
    if connector_name.startswith("source-"):
        return "source"
    elif connector_name.startswith("destination-"):
        return "destination"
    return "unknown"


def _parse_connector_names(value: str) -> set[str]:
    """Parse connector names from CSV or newline-delimited string."""
    names = set()
    for item in value.replace(",", "\n").split("\n"):
        item = item.strip()
        if item:
            names.add(item)
    return names


def _get_connector_version(connector_dir: Path) -> str | None:
    """Read connector version (dockerImageTag) from metadata.yaml."""
    metadata_file = connector_dir / METADATA_FILE_NAME
    if not metadata_file.exists():
        return None
    metadata = yaml.safe_load(metadata_file.read_text())
    return metadata.get("data", {}).get("dockerImageTag")


def _get_connector_info(
    connector_name: str, connector_dir: Path
) -> dict[str, str | int | None]:
    """Get full connector metadata as a dict with connector_ prefixed keys.

    This is shared between the `list --output-format json-gh-matrix` and `info` commands.
    """
    return {
        "connector": connector_name,
        "connector_type": _get_connector_type(connector_name),
        "connector_language": _detect_connector_language(connector_dir, connector_name)
        or "unknown",
        "connector_support_level": _get_connector_support_level(connector_dir),
        "connector_version": _get_connector_version(connector_dir),
        "connector_dir": f"{CONNECTOR_PATH_PREFIX}/{connector_name}",
    }


# Create the local sub-app
local_app = App(name="local", help="Local Airbyte monorepo operations.")
app.command(local_app)

# Create the connector sub-app under local
connector_app = App(name="connector", help="Connector operations in the monorepo.")
local_app.command(connector_app)


@connector_app.command(name="list")
def list_connectors(
    repo_path: Annotated[
        str,
        Parameter(help="Absolute path to the Airbyte monorepo."),
    ],
    certified_only: Annotated[
        bool,
        Parameter(help="Include only certified connectors."),
    ] = False,
    modified_only: Annotated[
        bool,
        Parameter(help="Include only modified connectors (requires PR context)."),
    ] = False,
    local_cdk: Annotated[
        bool,
        Parameter(
            help=(
                "Include connectors using local CDK reference. "
                "When combined with --modified-only, adds local-CDK connectors to the modified set."
            )
        ),
    ] = False,
    language: Annotated[
        list[str] | None,
        Parameter(help="Languages to include (python, java, low-code, manifest-only)."),
    ] = None,
    exclude_language: Annotated[
        list[str] | None,
        Parameter(help="Languages to exclude."),
    ] = None,
    connector_type: Annotated[
        str | None,
        Parameter(
            help=(
                "Connector types to include (source, destination). "
                "Accepts CSV or newline-delimited values."
            )
        ),
    ] = None,
    min_support_level: Annotated[
        str | None,
        Parameter(
            help=(
                "Minimum support level (inclusive). "
                "Accepts integer (100, 200, 300) or keyword (archived, community, certified)."
            )
        ),
    ] = None,
    max_support_level: Annotated[
        str | None,
        Parameter(
            help=(
                "Maximum support level (inclusive). "
                "Accepts integer (100, 200, 300) or keyword (archived, community, certified)."
            )
        ),
    ] = None,
    pr: Annotated[
        str | None,
        Parameter(help="PR number or GitHub URL for modification detection."),
    ] = None,
    exclude_connectors: Annotated[
        list[str] | None,
        Parameter(
            help=(
                "Connectors to exclude from results. "
                "Accepts CSV or newline-delimited values. Can be specified multiple times."
            )
        ),
    ] = None,
    force_include_connectors: Annotated[
        list[str] | None,
        Parameter(
            help=(
                "Connectors to force-include regardless of other filters. "
                "Accepts CSV or newline-delimited values. Can be specified multiple times."
            )
        ),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        Parameter(
            help=(
                'Output format: "csv" (comma-separated), '
                '"lines" (one connector per line), '
                '"json-gh-matrix" (GitHub Actions matrix JSON).'
            )
        ),
    ] = "lines",
) -> None:
    """List connectors in the Airbyte monorepo with filtering options."""
    # Validate mutually exclusive flags
    if language and exclude_language:
        exit_with_error("Cannot specify both --language and --exclude-language.")

    # Map CLI flags to MCP tool parameters
    certified: bool | None = True if certified_only else None
    modified: bool | None = True if modified_only else None

    language_filter: set[str] | None = set(language) if language else None
    language_exclude: set[str] | None = (
        set(exclude_language) if exclude_language else None
    )

    # Parse connector type filter
    connector_type_filter: set[str] | None = None
    if connector_type:
        try:
            connector_type_filter = _parse_connector_types(connector_type)
        except ValueError as e:
            exit_with_error(str(e))

    # Parse support level filters
    min_level: int | None = None
    max_level: int | None = None
    if min_support_level:
        try:
            min_level = _parse_support_level(min_support_level)
        except ValueError as e:
            exit_with_error(str(e))
    if max_support_level:
        try:
            max_level = _parse_support_level(max_support_level)
        except ValueError as e:
            exit_with_error(str(e))

    # Parse exclude/force-include connector lists (merge multiple flag values)
    exclude_set: set[str] = set()
    if exclude_connectors:
        for value in exclude_connectors:
            exclude_set.update(_parse_connector_names(value))

    force_include_set: set[str] = set()
    if force_include_connectors:
        for value in force_include_connectors:
            force_include_set.update(_parse_connector_names(value))

    result = list_connectors_in_repo(
        repo_path=repo_path,
        certified=certified,
        modified=modified,
        language_filter=language_filter,
        language_exclude=language_exclude,
        pr_num_or_url=pr,
    )
    connectors = list(result.connectors)
    repo_path_obj = Path(repo_path)

    # Add connectors with local CDK reference if --local-cdk flag is set
    if local_cdk:
        local_cdk_connectors = get_connectors_with_local_cdk(repo_path)
        connectors = sorted(set(connectors) | local_cdk_connectors)

    # Apply connector type filter
    if connector_type_filter:
        connectors = [
            name
            for name in connectors
            if _get_connector_type(name) in connector_type_filter
        ]

    # Apply support level filters (requires reading metadata)
    if min_level is not None or max_level is not None:
        filtered_connectors = []
        for name in connectors:
            connector_dir = repo_path_obj / CONNECTOR_PATH_PREFIX / name
            level = _get_connector_support_level(connector_dir)
            if level is None:
                continue  # Skip connectors without support level
            if min_level is not None and level < min_level:
                continue
            if max_level is not None and level > max_level:
                continue
            filtered_connectors.append(name)
        connectors = filtered_connectors

    # Apply exclude filter
    if exclude_set:
        connectors = [name for name in connectors if name not in exclude_set]

    # Apply force-include (union, overrides all other filters)
    if force_include_set:
        connectors_set = set(connectors)
        connectors_set.update(force_include_set)
        connectors = sorted(connectors_set)

    if output_format == "csv":
        console.print(",".join(connectors))
    elif output_format == "lines":
        for name in connectors:
            console.print(name)
    elif output_format == "json-gh-matrix":
        # Build matrix with full connector metadata
        include_list = []
        for name in connectors:
            connector_dir = repo_path_obj / CONNECTOR_PATH_PREFIX / name
            include_list.append(_get_connector_info(name, connector_dir))
        matrix = {"include": include_list}
        print_json(matrix)


def _write_github_step_outputs(outputs: dict[str, str | int | None]) -> None:
    """Write outputs to GitHub Actions step output file if running in CI."""
    github_output = os.getenv("GITHUB_OUTPUT")
    if not (os.getenv("CI") and github_output):
        return

    with open(github_output, "a", encoding="utf-8") as f:
        for key, value in outputs.items():
            if value is None:
                continue
            f.write(f"{key}={value}\n")


@connector_app.command(name="info")
def connector_info(
    connector_name: Annotated[
        str,
        Parameter(help="Name of the connector (e.g., source-github)."),
    ],
    repo_path: Annotated[
        str | None,
        Parameter(help="Path to the Airbyte monorepo. Can be inferred from context."),
    ] = None,
) -> None:
    """Get metadata for a single connector.

    Prints JSON output with connector metadata. When running in GitHub Actions
    (CI env var set), also writes each field to GitHub step outputs.
    """
    # Infer repo_path from current directory if not provided
    if repo_path is None:
        # Check if we're in an airbyte repo by looking for the connectors directory
        cwd = Path.cwd()
        # Walk up to find airbyte-integrations/connectors
        for parent in [cwd, *cwd.parents]:
            if (parent / CONNECTOR_PATH_PREFIX).exists():
                repo_path = str(parent)
                break
        if repo_path is None:
            exit_with_error(
                "Could not infer repo path. Please provide --repo-path or run from within the Airbyte monorepo."
            )

    repo_path_obj = Path(repo_path)
    connector_dir = repo_path_obj / CONNECTOR_PATH_PREFIX / connector_name

    if not connector_dir.exists():
        exit_with_error(f"Connector directory not found: {connector_dir}")

    info = _get_connector_info(connector_name, connector_dir)

    # Print JSON output
    print_json(info)

    # Write to GitHub step outputs if in CI
    _write_github_step_outputs(info)


BumpType = Literal["patch", "minor", "major"]


@connector_app.command(name="bump-version")
def bump_version(
    name: Annotated[
        str,
        Parameter(help="Connector technical name (e.g., source-github)."),
    ],
    repo_path: Annotated[
        str,
        Parameter(help="Absolute path to the Airbyte monorepo."),
    ],
    bump_type: Annotated[
        BumpType | None,
        Parameter(help="Version bump type: patch, minor, or major."),
    ] = None,
    new_version: Annotated[
        str | None,
        Parameter(help="Explicit new version (overrides --bump-type if provided)."),
    ] = None,
    changelog_message: Annotated[
        str | None,
        Parameter(help="Message to add to changelog."),
    ] = None,
    pr_number: Annotated[
        int | None,
        Parameter(help="PR number for changelog entry."),
    ] = None,
    dry_run: Annotated[
        bool,
        Parameter(help="Show what would be changed without modifying files."),
    ] = False,
) -> None:
    """Bump a connector's version across all relevant files.

    Updates version in metadata.yaml (always), pyproject.toml (if exists),
    and documentation changelog (if --changelog-message provided).

    Either --bump-type or --new-version must be provided.
    """
    # Call capability function and handle specific errors
    try:
        result = bump_connector_version(
            repo_path=repo_path,
            connector_name=name,
            bump_type=bump_type,
            new_version=new_version,
            changelog_message=changelog_message,
            pr_number=pr_number,
            dry_run=dry_run,
        )
    except ConnectorNotFoundError as e:
        exit_with_error(str(e))
    except VersionNotFoundError as e:
        exit_with_error(str(e))
    except InvalidVersionError as e:
        exit_with_error(str(e))
    except ValueError as e:
        exit_with_error(str(e))

    # Build output matching the issue spec
    output = {
        "connector": result.connector,
        "previous_version": result.previous_version,
        "new_version": result.new_version,
        "files_modified": result.files_modified,
        "dry_run": result.dry_run,
    }
    print_json(output)

    # Write to GitHub step outputs if in CI
    _write_github_step_outputs(
        {
            "connector": result.connector,
            "previous_version": result.previous_version,
            "new_version": result.new_version,
        }
    )


@connector_app.command(name="qa")
def run_qa_checks(
    name: Annotated[
        list[str] | None,
        Parameter(
            help="Connector technical name(s) (e.g., source-github). Can be specified multiple times."
        ),
    ] = None,
    connector_directory: Annotated[
        str | None,
        Parameter(
            help="Directory containing connectors to run checks on all connectors in this directory."
        ),
    ] = None,
    check: Annotated[
        list[str] | None,
        Parameter(help="Specific check(s) to run. Can be specified multiple times."),
    ] = None,
    report_path: Annotated[
        str | None,
        Parameter(help="Path to write the JSON report file."),
    ] = None,
) -> None:
    """Run QA checks on connector(s).

    Validates connector metadata, documentation, packaging, security, and versioning.
    Exit code is non-zero if any checks fail.
    """
    # Determine which checks to run
    checks_to_run = ENABLED_CHECKS
    if check:
        check_names = set(check)
        checks_to_run = [c for c in ENABLED_CHECKS if type(c).__name__ in check_names]
        if not checks_to_run:
            exit_with_error(
                f"No matching checks found. Available checks: {[type(c).__name__ for c in ENABLED_CHECKS]}"
            )

    # Collect connectors to check
    connectors: list[Connector] = []
    if name:
        connectors.extend(Connector(remove_strict_encrypt_suffix(n)) for n in name)
    if connector_directory:
        connectors.extend(get_all_connectors_in_directory(Path(connector_directory)))

    if not connectors:
        exit_with_error("No connectors specified. Use --name or --connector-directory.")

    connectors = sorted(connectors, key=lambda c: c.technical_name)

    # Run checks synchronously (simpler than async for CLI)
    all_results = []
    for connector in connectors:
        for qa_check in checks_to_run:
            result = qa_check.run(connector)
            if result.status == CheckStatus.PASSED:
                status_icon = "[green]✅ PASS[/green]"
            elif result.status == CheckStatus.SKIPPED:
                status_icon = "[yellow]🔶 SKIP[/yellow]"
            else:
                status_icon = "[red]❌ FAIL[/red]"
            console.print(
                f"{status_icon} {connector.technical_name}: {result.check.name}"
            )
            if result.message:
                console.print(f"    {result.message}")
            all_results.append(result)

    # Write report if requested
    if report_path:
        Report(check_results=all_results).write(Path(report_path))
        console.print(f"Report written to {report_path}")

    # Exit with error if any checks failed
    failed = [r for r in all_results if r.status == CheckStatus.FAILED]
    if failed:
        exit_with_error(f"{len(failed)} check(s) failed")


@connector_app.command(name="qa-docs-generate")
def generate_qa_docs(
    output_file: Annotated[
        str,
        Parameter(help="Path to write the generated documentation file."),
    ],
) -> None:
    """Generate documentation for QA checks.

    Creates a markdown file documenting all available QA checks organized by category.
    """
    checks_by_category: dict[CheckCategory, list[Check]] = {}
    for qa_check in ENABLED_CHECKS:
        checks_by_category.setdefault(qa_check.category, []).append(qa_check)

    jinja_env = Environment(
        loader=PackageLoader("airbyte_ops_mcp.connector_qa", "templates"),
        autoescape=select_autoescape(),
        trim_blocks=False,
        lstrip_blocks=True,
    )
    template = jinja_env.get_template(CONNECTORS_QA_DOC_TEMPLATE_NAME)
    documentation = template.render(checks_by_category=checks_by_category)

    output_path = Path(output_file)
    output_path.write_text(documentation)
    console.print(f"Documentation written to {output_file}")


# Create the changelog sub-app under connector
changelog_app = App(name="changelog", help="Changelog operations for connectors.")
connector_app.command(changelog_app)


@changelog_app.command(name="check")
def changelog_check(
    connector_name: Annotated[
        str | None,
        Parameter(help="Connector technical name (e.g., source-github)."),
    ] = None,
    all_connectors: Annotated[
        bool,
        Parameter("--all", help="Check all connectors in the repository."),
    ] = False,
    repo_path: Annotated[
        str | None,
        Parameter(help="Path to the Airbyte monorepo. Can be inferred from context."),
    ] = None,
    lookback_days: Annotated[
        int | None,
        Parameter(help="Only check entries with dates within this many days."),
    ] = None,
    strict: Annotated[
        bool,
        Parameter(help="Exit with error code if any issues are found."),
    ] = False,
) -> None:
    """Check changelog entries for issues.

    Validates changelog dates match PR merge dates and checks for PR number mismatches.
    """
    if not connector_name and not all_connectors:
        exit_with_error("Either --connector-name or --all must be specified.")

    if connector_name and all_connectors:
        exit_with_error("Cannot specify both --connector-name and --all.")

    if repo_path is None:
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            if (parent / CONNECTOR_PATH_PREFIX).exists():
                repo_path = str(parent)
                break
        if repo_path is None:
            exit_with_error(
                "Could not infer repo path. Please provide --repo-path or run from within the Airbyte monorepo."
            )

    total_issues = 0

    if all_connectors:
        results = check_all_changelogs(repo_path=repo_path, lookback_days=lookback_days)
        for result in results:
            if result.has_issues or result.errors:
                _print_check_result(result)
                total_issues += result.issue_count
    else:
        result = check_changelog(
            repo_path=repo_path,
            connector_name=connector_name,
            lookback_days=lookback_days,
        )
        _print_check_result(result)
        total_issues = result.issue_count

    if total_issues > 0:
        console.print(f"\n[bold]Total issues found: {total_issues}[/bold]")
        if strict:
            exit_with_error(f"Found {total_issues} issue(s) in changelog(s).")
    else:
        console.print("[green]No issues found.[/green]")


def _print_check_result(result: ChangelogCheckResult) -> None:
    """Print a changelog check result."""
    if not result.has_issues and not result.errors:
        return

    console.print(f"\n[bold]{result.connector}[/bold]")

    for warning in result.pr_mismatch_warnings:
        console.print(
            f"  [yellow]WARNING[/yellow] Line {warning.line_number} (v{warning.version}): {warning.message}"
        )

    for fix in result.date_issues:
        if fix.changed:
            console.print(
                f"  [red]DATE MISMATCH[/red] Line {fix.line_number} (v{fix.version}): "
                f"changelog has {fix.old_date}, PR merged on {fix.new_date}"
            )

    for error in result.errors:
        console.print(f"  [red]ERROR[/red] {error}")


@changelog_app.command(name="fix")
def changelog_fix(
    connector_name: Annotated[
        str | None,
        Parameter(help="Connector technical name (e.g., source-github)."),
    ] = None,
    all_connectors: Annotated[
        bool,
        Parameter("--all", help="Fix all connectors in the repository."),
    ] = False,
    repo_path: Annotated[
        str | None,
        Parameter(help="Path to the Airbyte monorepo. Can be inferred from context."),
    ] = None,
    lookback_days: Annotated[
        int | None,
        Parameter(help="Only fix entries with dates within this many days."),
    ] = None,
    dry_run: Annotated[
        bool,
        Parameter(help="Print changes without modifying files."),
    ] = False,
) -> None:
    """Fix changelog entry dates to match PR merge dates.

    Looks up the actual merge date for each PR referenced in the changelog
    and updates the date column to match.
    """
    if not connector_name and not all_connectors:
        exit_with_error("Either --connector-name or --all must be specified.")

    if connector_name and all_connectors:
        exit_with_error("Cannot specify both --connector-name and --all.")

    if repo_path is None:
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            if (parent / CONNECTOR_PATH_PREFIX).exists():
                repo_path = str(parent)
                break
        if repo_path is None:
            exit_with_error(
                "Could not infer repo path. Please provide --repo-path or run from within the Airbyte monorepo."
            )

    total_fixed = 0
    total_warnings = 0

    if all_connectors:
        results = fix_all_changelog_dates(
            repo_path=repo_path, dry_run=dry_run, lookback_days=lookback_days
        )
        for result in results:
            if result.has_changes or result.warnings or result.errors:
                _print_fix_result(result)
                total_fixed += result.changed_count
                total_warnings += len(result.warnings)
    else:
        result = fix_changelog_dates(
            repo_path=repo_path,
            connector_name=connector_name,
            dry_run=dry_run,
            lookback_days=lookback_days,
        )
        _print_fix_result(result)
        total_fixed = result.changed_count
        total_warnings = len(result.warnings)

    action = "Would fix" if dry_run else "Fixed"
    console.print(f"\n[bold]{action} {total_fixed} date(s).[/bold]")
    if total_warnings > 0:
        console.print(
            f"[yellow]{total_warnings} warning(s) about PR number mismatches.[/yellow]"
        )


def _print_fix_result(result: ChangelogFixResult) -> None:
    """Print a changelog fix result."""
    if not result.has_changes and not result.warnings and not result.errors:
        return

    console.print(f"\n[bold]{result.connector}[/bold]")

    for warning in result.warnings:
        console.print(
            f"  [yellow]WARNING[/yellow] Line {warning.line_number} (v{warning.version}): {warning.message}"
        )

    for fix in result.fixes:
        if fix.changed:
            action = "Would fix" if result.dry_run else "Fixed"
            console.print(
                f"  [green]{action}[/green] Line {fix.line_number} (v{fix.version}): "
                f"{fix.old_date} -> {fix.new_date}"
            )

    for error in result.errors:
        console.print(f"  [red]ERROR[/red] {error}")


# Create the enterprise-stub sub-app under connector
enterprise_stub_app = App(
    name="enterprise-stub",
    help="Enterprise connector stub operations (local file validation and updates).",
)
connector_app.command(enterprise_stub_app)

# Path to connectors in the airbyte-enterprise repo
ENTERPRISE_CONNECTOR_PATH_PREFIX = "airbyte-integrations/connectors"


def _build_stub_from_metadata(
    connector_name: str,
    metadata: dict,
    existing_stub: dict | None = None,
) -> dict:
    """Build a connector stub from metadata.yaml.

    Args:
        connector_name: The connector name (e.g., 'source-oracle-enterprise').
        metadata: The parsed metadata.yaml content.
        existing_stub: Optional existing stub to preserve extra fields from.

    Returns:
        A connector stub dictionary.
    """
    data = metadata.get("data", {})

    # Determine connector type for the stub
    connector_type = data.get("connectorType", "source")
    stub_type = f"enterprise_{connector_type}"

    # Preserve existing stub ID if available, otherwise use connector name
    stub_id = (existing_stub.get("id") if existing_stub else None) or connector_name

    # Get the icon URL - construct from icon filename if available
    icon_filename = data.get("icon", "")
    if icon_filename and not icon_filename.startswith("http"):
        # Construct icon URL from the standard GCS path
        icon_url = f"https://storage.googleapis.com/prod-airbyte-cloud-connector-metadata-service/resources/connector_stubs/v0/icons/{icon_filename}"
    else:
        icon_url = icon_filename or ""

    # Build the stub
    stub: dict = {
        "id": stub_id,
        "name": data.get("name", connector_name.replace("-", " ").title()),
        "label": "enterprise",
        "icon": icon_url,
        "url": data.get("documentationUrl", ""),
        "type": stub_type,
    }

    # Add definitionId if available
    definition_id = data.get("definitionId")
    if definition_id:
        stub["definitionId"] = definition_id

    # Preserve extra fields from existing stub (like codename)
    if existing_stub:
        for key in existing_stub:
            if key not in stub:
                stub[key] = existing_stub[key]

    return stub


@enterprise_stub_app.command(name="check")
def enterprise_stub_check(
    connector: Annotated[
        str | None,
        Parameter(help="Connector name to check (e.g., 'source-oracle-enterprise')."),
    ] = None,
    all_connectors: Annotated[
        bool,
        Parameter("--all", help="Check all stubs in the file."),
    ] = False,
    repo_root: Annotated[
        Path | None,
        Parameter(
            help="Path to the airbyte-enterprise repository root. Defaults to current directory."
        ),
    ] = None,
) -> None:
    """Validate enterprise connector stub entries.

    Checks that stub entries have valid required fields (id, name, url, icon)
    and optionally validates that the stub matches the connector's metadata.yaml.

    Exit codes:
        0: All checks passed
        1: Validation errors found

    Output:
        STDOUT: JSON validation result
        STDERR: Informational messages

    Example:
        airbyte-ops local connector enterprise-stub check --connector source-oracle-enterprise --repo-root /path/to/airbyte-enterprise
        airbyte-ops local connector enterprise-stub check --all --repo-root /path/to/airbyte-enterprise
    """
    if not connector and not all_connectors:
        exit_with_error("Either --connector or --all must be specified.")

    if connector and all_connectors:
        exit_with_error("Cannot specify both --connector and --all.")

    if repo_root is None:
        repo_root = Path.cwd()

    # Load local stubs
    try:
        stubs = load_local_stubs(repo_root)
    except FileNotFoundError as e:
        exit_with_error(str(e))
    except ValueError as e:
        exit_with_error(str(e))

    stubs_to_check = stubs if all_connectors else []
    if connector:
        stub = find_stub_by_connector(stubs, connector)
        if stub is None:
            exit_with_error(
                f"Connector stub '{connector}' not found in {CONNECTOR_STUBS_FILE}"
            )
        stubs_to_check = [stub]

    errors: list[dict] = []
    warnings: list[dict] = []
    placeholders: list[dict] = []

    for stub in stubs_to_check:
        stub_id = stub.get("id", "<unknown>")
        stub_name = stub.get("name", stub_id)

        # Check required fields
        required_fields = ["id", "name", "url", "icon"]
        for field in required_fields:
            if not stub.get(field):
                errors.append(
                    {"stub_id": stub_id, "error": f"Missing required field: {field}"}
                )

        # Check if corresponding connector exists and validate against metadata
        connector_dir = repo_root / ENTERPRISE_CONNECTOR_PATH_PREFIX / stub_id
        metadata_file = connector_dir / METADATA_FILE_NAME

        if metadata_file.exists():
            metadata = yaml.safe_load(metadata_file.read_text())
            data = metadata.get("data", {})

            # Check if definitionId matches
            metadata_def_id = data.get("definitionId")
            stub_def_id = stub.get("definitionId")
            if metadata_def_id and stub_def_id and metadata_def_id != stub_def_id:
                errors.append(
                    {
                        "stub_id": stub_id,
                        "error": f"definitionId mismatch: stub has '{stub_def_id}', metadata has '{metadata_def_id}'",
                    }
                )

            # Check if name matches
            metadata_name = data.get("name")
            if metadata_name and stub_name and metadata_name != stub_name:
                warnings.append(
                    {
                        "stub_id": stub_id,
                        "warning": f"name mismatch: stub has '{stub_name}', metadata has '{metadata_name}'",
                    }
                )
        else:
            # No connector directory - this is a registry placeholder for a future connector
            placeholders.append(
                {
                    "stub_id": stub_id,
                    "name": stub_name,
                }
            )

    result = {
        "checked_count": len(stubs_to_check),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "placeholder_count": len(placeholders),
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "placeholders": placeholders,
    }

    # Print placeholders as info (not warnings - these are valid registry placeholders)
    if placeholders:
        error_console.print(
            f"[blue]Found {len(placeholders)} registry placeholder(s) (no local directory):[/blue]"
        )
        for placeholder in placeholders:
            error_console.print(
                f"  Found Connector Registry Placeholder (no local directory): {placeholder['name']}"
            )

    if errors:
        error_console.print(f"[red]Found {len(errors)} error(s):[/red]")
        for err in errors:
            error_console.print(f"  {err['stub_id']}: {err['error']}")

    if warnings:
        error_console.print(f"[yellow]Found {len(warnings)} warning(s):[/yellow]")
        for warn in warnings:
            error_console.print(f"  {warn['stub_id']}: {warn['warning']}")

    if not errors and not warnings:
        error_console.print(
            f"[green]All {len(stubs_to_check)} stub(s) passed validation[/green]"
        )

    print_json(result)

    if errors:
        exit_with_error("Validation failed", code=1)


@enterprise_stub_app.command(name="sync")
def enterprise_stub_sync(
    connector: Annotated[
        str | None,
        Parameter(help="Connector name to sync (e.g., 'source-oracle-enterprise')."),
    ] = None,
    all_connectors: Annotated[
        bool,
        Parameter("--all", help="Sync all connectors that have metadata.yaml files."),
    ] = False,
    repo_root: Annotated[
        Path | None,
        Parameter(
            help="Path to the airbyte-enterprise repository root. Defaults to current directory."
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        Parameter(help="Show what would be synced without making changes."),
    ] = False,
) -> None:
    """Sync connector stub(s) from connector metadata.yaml file(s).

    Reads the connector's metadata.yaml file and updates the corresponding
    entry in connector_stubs.json with the current values.

    Exit codes:
        0: Sync successful (or dry-run completed)
        1: Error (connector not found, no metadata, etc.)

    Output:
        STDOUT: JSON representation of the synced stub(s)
        STDERR: Informational messages

    Example:
        airbyte-ops local connector enterprise-stub sync --connector source-oracle-enterprise --repo-root /path/to/airbyte-enterprise
        airbyte-ops local connector enterprise-stub sync --all --repo-root /path/to/airbyte-enterprise
        airbyte-ops local connector enterprise-stub sync --connector source-oracle-enterprise --dry-run
    """
    if not connector and not all_connectors:
        exit_with_error("Either --connector or --all must be specified.")

    if connector and all_connectors:
        exit_with_error("Cannot specify both --connector and --all.")

    if repo_root is None:
        repo_root = Path.cwd()

    # Load existing stubs
    try:
        stubs = load_local_stubs(repo_root)
    except FileNotFoundError:
        stubs = []
    except ValueError as e:
        exit_with_error(str(e))

    # Determine which connectors to sync
    connectors_to_sync: list[str] = []
    if connector:
        connectors_to_sync = [connector]
    else:
        # Find all connectors with metadata.yaml in the enterprise connectors directory
        connectors_dir = repo_root / ENTERPRISE_CONNECTOR_PATH_PREFIX
        if connectors_dir.exists():
            for item in connectors_dir.iterdir():
                if item.is_dir() and (item / METADATA_FILE_NAME).exists():
                    connectors_to_sync.append(item.name)
        connectors_to_sync.sort()

    if not connectors_to_sync:
        exit_with_error("No connectors found to sync.")

    synced_stubs: list[dict] = []
    updated_count = 0
    added_count = 0

    for conn_name in connectors_to_sync:
        connector_dir = repo_root / ENTERPRISE_CONNECTOR_PATH_PREFIX / conn_name
        metadata_file = connector_dir / METADATA_FILE_NAME

        if not connector_dir.exists():
            if connector:
                exit_with_error(f"Connector directory not found: {connector_dir}")
            continue

        if not metadata_file.exists():
            if connector:
                exit_with_error(f"Metadata file not found: {metadata_file}")
            continue

        # Load metadata
        metadata = yaml.safe_load(metadata_file.read_text())

        # Find existing stub if any
        existing_stub = find_stub_by_connector(stubs, conn_name)

        # Build new stub from metadata
        new_stub = _build_stub_from_metadata(conn_name, metadata, existing_stub)

        # Validate the new stub
        ConnectorStub(**new_stub)

        if dry_run:
            action = "update" if existing_stub else "create"
            error_console.print(f"[DRY RUN] Would {action} stub for '{conn_name}'")
            synced_stubs.append(new_stub)
            continue

        # Update or add the stub
        if existing_stub:
            # Find and replace
            for i, stub in enumerate(stubs):
                if stub.get("id") == existing_stub.get("id"):
                    stubs[i] = new_stub
                    break
            updated_count += 1
        else:
            stubs.append(new_stub)
            added_count += 1

        synced_stubs.append(new_stub)

    if not dry_run:
        # Save the updated stubs
        save_local_stubs(repo_root, stubs)
        error_console.print(
            f"[green]Synced {len(synced_stubs)} stub(s) to {CONNECTOR_STUBS_FILE} "
            f"({added_count} added, {updated_count} updated)[/green]"
        )
    else:
        error_console.print(
            f"[DRY RUN] Would sync {len(synced_stubs)} stub(s) to {CONNECTOR_STUBS_FILE}"
        )

    print_json(
        synced_stubs if all_connectors else synced_stubs[0] if synced_stubs else {}
    )

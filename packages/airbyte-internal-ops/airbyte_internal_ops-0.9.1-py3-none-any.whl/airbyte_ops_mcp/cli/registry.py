# Copyright (c) 2025 Airbyte, Inc., all rights reserved.
"""CLI commands for connector registry operations.

This module provides CLI wrappers for registry operations. The core logic
lives in the `airbyte_ops_mcp.registry` capability module.

Commands:
    airbyte-ops registry connector compute-prerelease-tag - Compute prerelease version tag
    airbyte-ops registry connector publish-prerelease - Publish connector prerelease
    airbyte-ops registry connector publish - Publish connector (apply/rollback version override)
    airbyte-ops registry enterprise-stubs sync --bucket prod|dev - Sync connector_stubs.json to GCS
    airbyte-ops registry enterprise-stubs check --bucket prod|dev - Compare local file with GCS
    airbyte-ops registry image inspect - Inspect Docker image on DockerHub
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from typing import Annotated, Literal

import yaml
from cyclopts import App, Parameter

from airbyte_ops_mcp.cli._base import app
from airbyte_ops_mcp.cli._shared import (
    error_console,
    exit_with_error,
    print_error,
    print_json,
    print_success,
)
from airbyte_ops_mcp.github_api import (
    get_file_contents_at_ref,
    resolve_github_token,
)
from airbyte_ops_mcp.mcp.github_actions import get_docker_image_info
from airbyte_ops_mcp.mcp.prerelease import (
    compute_prerelease_docker_image_tag,
    publish_connector_to_airbyte_registry,
)
from airbyte_ops_mcp.registry import (
    ConnectorPublishResult,
    PublishAction,
    publish_connector,
)
from airbyte_ops_mcp.registry._gcs_util import get_bucket_name
from airbyte_ops_mcp.registry.connector_stubs import (
    CONNECTOR_STUBS_FILE,
    CONNECTOR_STUBS_PATH,
    ConnectorStub,
    load_local_stubs,
    read_connector_stubs,
    write_connector_stubs,
)

# Create the registry sub-app
registry_app = App(
    name="registry", help="Connector registry and Docker image operations."
)
app.command(registry_app)

# Create the connector sub-app under registry
connector_app = App(name="connector", help="Registry-facing connector operations.")
registry_app.command(connector_app)

# Create the image sub-app under registry
image_app = App(name="image", help="Docker image operations.")
registry_app.command(image_app)

# Create the enterprise-stubs sub-app under registry (for whole-file GCS operations)
enterprise_stubs_app = App(
    name="enterprise-stubs",
    help="Enterprise connector stubs GCS operations (whole-file sync).",
)
registry_app.command(enterprise_stubs_app)


AIRBYTE_REPO_OWNER = "airbytehq"
AIRBYTE_ENTERPRISE_REPO_NAME = "airbyte-enterprise"
AIRBYTE_REPO_NAME = "airbyte"
CONNECTOR_PATH_PREFIX = "airbyte-integrations/connectors"

# Type alias for bucket argument
BucketArg = Literal["dev", "prod"]


def _validate_bucket_arg(bucket: str) -> BucketArg:
    """Validate and return the bucket argument.

    Args:
        bucket: The bucket argument from CLI.

    Returns:
        The validated bucket value.

    Raises:
        SystemExit: If the bucket value is invalid.
    """
    if bucket not in ("prod", "dev"):
        exit_with_error(f"Invalid bucket '{bucket}'. Must be 'prod' or 'dev'.")
    return bucket  # type: ignore[return-value]


def _get_connector_version_from_github(
    connector_name: str,
    ref: str,
    token: str | None = None,
) -> str | None:
    """Fetch connector version from metadata.yaml via GitHub API.

    Args:
        connector_name: Connector name (e.g., "source-github")
        ref: Git ref (commit SHA, branch name, or tag)
        token: GitHub API token (optional for public repos)

    Returns:
        Version string from metadata.yaml, or None if not found.
    """
    path = f"{CONNECTOR_PATH_PREFIX}/{connector_name}/metadata.yaml"
    contents = get_file_contents_at_ref(
        owner=AIRBYTE_REPO_OWNER,
        repo=AIRBYTE_REPO_NAME,
        path=path,
        ref=ref,
        token=token,
    )
    if contents is None:
        return None

    metadata = yaml.safe_load(contents)
    return metadata.get("data", {}).get("dockerImageTag")


@connector_app.command(name="compute-prerelease-tag")
def compute_prerelease_tag(
    connector_name: Annotated[
        str,
        Parameter(help="Connector name (e.g., 'source-github')."),
    ],
    sha: Annotated[
        str,
        Parameter(help="Git commit SHA (full or at least 7 characters)."),
    ],
    base_version: Annotated[
        str | None,
        Parameter(
            help="Base version override. If not provided, fetched from metadata.yaml at the given SHA."
        ),
    ] = None,
) -> None:
    """Compute the pre-release docker image tag.

    Outputs the version tag to stdout for easy capture in shell scripts.
    This is the single source of truth for pre-release version format.

    The command fetches the connector's metadata.yaml from GitHub at the given SHA
    to determine the base version. It also compares against the master branch and
    prints a warning to stderr if no version bump is detected.

    If --base-version is provided, it is used directly instead of fetching from GitHub.

    Example:
        airbyte-ops registry connector compute-prerelease-tag --connector-name source-github --sha abcdef1234567
        # Output: 1.2.3-preview.abcdef1

        airbyte-ops registry connector compute-prerelease-tag --connector-name source-github --sha abcdef1234567 --base-version 1.2.3
        # Output: 1.2.3-preview.abcdef1 (uses provided version, skips GitHub API)
    """
    # Try to get a GitHub token (optional, but helps avoid rate limiting)
    # Token resolution may fail if no token is configured, which is fine for public repos
    token: str | None = None
    with contextlib.suppress(ValueError):
        token = resolve_github_token()

    # Determine base version
    version: str
    if base_version:
        version = base_version
    else:
        # Fetch version from metadata.yaml at the given SHA
        fetched_version = _get_connector_version_from_github(connector_name, sha, token)
        if fetched_version is None:
            print(
                f"Error: Could not fetch metadata.yaml for {connector_name} at ref {sha}",
                file=sys.stderr,
            )
            sys.exit(1)
        version = fetched_version

    # Compare with master branch version and warn if no bump detected
    master_version = _get_connector_version_from_github(connector_name, "master", token)
    if master_version and master_version == version:
        print(
            f"Warning: No version bump detected for {connector_name}. "
            f"Version {version} matches master branch.",
            file=sys.stderr,
        )

    # Compute and output the prerelease tag
    tag = compute_prerelease_docker_image_tag(version, sha)
    print(tag)


@connector_app.command(name="publish-prerelease")
def publish_prerelease(
    connector_name: Annotated[
        str,
        Parameter(
            help="The connector name to publish (e.g., 'source-github', 'destination-postgres')."
        ),
    ],
    pr: Annotated[
        int,
        Parameter(help="The pull request number containing the connector changes."),
    ],
) -> None:
    """Publish a connector prerelease to the Airbyte registry.

    Triggers the publish-connectors-prerelease workflow in the airbytehq/airbyte
    repository. Pre-release versions are tagged with format: {version}-preview.{git-sha}

    Requires GITHUB_CONNECTOR_PUBLISHING_PAT or GITHUB_TOKEN environment variable
    with 'actions:write' permission.
    """
    result = publish_connector_to_airbyte_registry(
        connector_name=connector_name,
        pr_number=pr,
        prerelease=True,
    )
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)
    print_json(result.model_dump())


@connector_app.command(name="publish")
def publish(
    name: Annotated[
        str,
        Parameter(help="Connector technical name (e.g., source-github)."),
    ],
    repo_path: Annotated[
        Path,
        Parameter(help="Path to the Airbyte monorepo. Defaults to current directory."),
    ] = Path.cwd(),
    apply_override: Annotated[
        bool,
        Parameter(
            help="Apply a version override (promote RC to stable).",
            negative="",  # Disable --no-apply-override
        ),
    ] = False,
    rollback_override: Annotated[
        bool,
        Parameter(
            help="Rollback a version override.",
            negative="",  # Disable --no-rollback-override
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        Parameter(help="Show what would be published without making changes."),
    ] = False,
    prod: Annotated[
        bool,
        Parameter(
            help="Target the production GCS bucket. Without this flag, operations target the dev bucket for safe testing.",
            negative="",  # Disable --no-prod
        ),
    ] = False,
) -> None:
    """Publish a connector to the Airbyte registry.

    This command handles connector publishing operations including applying
    version overrides (promoting RC to stable) or rolling back version overrides.

    By default, operations target the dev bucket (dev-airbyte-cloud-connector-metadata-service-2)
    for safe testing. Use --prod to target the production bucket.
    """
    if apply_override and rollback_override:
        exit_with_error("Cannot use both --apply-override and --rollback-override")

    if not apply_override and not rollback_override:
        exit_with_error("Must specify either --apply-override or --rollback-override")

    # Map CLI flags to PublishAction
    action: PublishAction = (
        "apply-version-override" if apply_override else "rollback-version-override"
    )

    # Delegate to the capability module
    if not repo_path.exists():
        exit_with_error(f"Repository path not found: {repo_path}")

    result: ConnectorPublishResult = publish_connector(
        repo_path=repo_path,
        connector_name=name,
        action=action,
        dry_run=dry_run,
        use_prod=prod,
    )

    # Output result as JSON
    print_json(result.model_dump())

    if result.status == "failure":
        exit_with_error(result.message or "Operation failed", code=1)


@image_app.command(name="inspect")
def inspect_image(
    image: Annotated[
        str,
        Parameter(help="Docker image name (e.g., 'airbyte/source-github')."),
    ],
    tag: Annotated[
        str,
        Parameter(help="Image tag (e.g., '2.1.5-preview.abc1234')."),
    ],
) -> None:
    """Check if a Docker image exists on DockerHub.

    Returns information about the image if it exists, or indicates if it doesn't exist.
    Useful for confirming that a pre-release connector was successfully published.
    """
    result = get_docker_image_info(
        image=image,
        tag=tag,
    )
    if result.exists:
        print_success(f"Image {result.full_name} exists.")
    else:
        print_error(f"Image {result.full_name} not found.")
    print_json(result.model_dump())


@enterprise_stubs_app.command(name="check")
def enterprise_stubs_check(
    bucket: Annotated[
        BucketArg,
        Parameter(
            help="Target GCS bucket: 'prod' or 'dev'.",
        ),
    ],
    repo_root: Annotated[
        Path,
        Parameter(
            help="Path to the airbyte-enterprise repository root. Defaults to current directory."
        ),
    ] = Path.cwd(),
) -> None:
    """Compare local connector_stubs.json with the version in GCS.

    This command reads the entire local connector_stubs.json file and compares it
    with the version currently published in GCS.

    Exit codes:
        0: Local file matches GCS (check passed)
        1: Differences found (check failed)

    Output:
        STDOUT: JSON representation of the comparison result
        STDERR: Informational messages and comparison details

    Example:
        airbyte-ops registry enterprise-stubs check --bucket prod --repo-root /path/to/airbyte-enterprise
        airbyte-ops registry enterprise-stubs check --bucket dev
    """
    bucket = _validate_bucket_arg(bucket)

    # Load local stubs
    try:
        local_stubs = load_local_stubs(repo_root)
    except FileNotFoundError as e:
        exit_with_error(str(e))
    except ValueError as e:
        exit_with_error(str(e))

    # Load published stubs from GCS
    bucket_name = get_bucket_name(bucket)
    published_stubs = read_connector_stubs(bucket_name)

    error_console.print(
        f"Comparing local {CONNECTOR_STUBS_FILE} with {bucket_name}/{CONNECTOR_STUBS_PATH}"
    )

    # Build lookup dicts by stub ID (filter out stubs without IDs)
    local_by_id = {stub["id"]: stub for stub in local_stubs if stub.get("id")}
    published_by_id = {stub["id"]: stub for stub in published_stubs if stub.get("id")}

    all_ids = set(local_by_id.keys()) | set(published_by_id.keys())
    differences: list[dict[str, str]] = []

    for stub_id in sorted(all_ids):
        local_stub = local_by_id.get(stub_id)
        published_stub = published_by_id.get(stub_id)

        if local_stub is None:
            differences.append({"id": stub_id, "status": "only_in_gcs"})
        elif published_stub is None:
            differences.append({"id": stub_id, "status": "only_in_local"})
        elif local_stub != published_stub:
            differences.append({"id": stub_id, "status": "modified"})

    result = {
        "local_count": len(local_stubs),
        "published_count": len(published_stubs),
        "in_sync": len(differences) == 0,
        "differences": differences,
    }

    if differences:
        error_console.print(
            f"[yellow]Warning:[/yellow] {len(differences)} difference(s) found:"
        )
        for diff in differences:
            error_console.print(f"  {diff['id']}: {diff['status']}")
        print_json(result)
        sys.exit(1)

    error_console.print(
        f"[green]Local file is in sync with GCS ({len(local_stubs)} stubs)[/green]"
    )
    print_json(result)


@enterprise_stubs_app.command(name="sync")
def enterprise_stubs_sync(
    bucket: Annotated[
        BucketArg,
        Parameter(
            help="Target GCS bucket: 'prod' or 'dev'.",
        ),
    ],
    repo_root: Annotated[
        Path,
        Parameter(
            help="Path to the airbyte-enterprise repository root. Defaults to current directory."
        ),
    ] = Path.cwd(),
    dry_run: Annotated[
        bool,
        Parameter(help="Show what would be uploaded without making changes."),
    ] = False,
) -> None:
    """Sync local connector_stubs.json to GCS.

    This command uploads the entire local connector_stubs.json file to GCS,
    replacing the existing file. Use this after merging changes to master
    in the airbyte-enterprise repository.

    Exit codes:
        0: Sync successful (or dry-run completed)
        1: Error (file not found, validation failed, etc.)

    Output:
        STDOUT: JSON representation of the sync result
        STDERR: Informational messages and status updates

    Example:
        airbyte-ops registry enterprise-stubs sync --bucket prod --repo-root /path/to/airbyte-enterprise
        airbyte-ops registry enterprise-stubs sync --bucket dev
        airbyte-ops registry enterprise-stubs sync --bucket dev --dry-run
    """
    bucket = _validate_bucket_arg(bucket)

    # Load local stubs
    try:
        local_stubs = load_local_stubs(repo_root)
    except FileNotFoundError as e:
        exit_with_error(str(e))
    except ValueError as e:
        exit_with_error(str(e))

    # Validate all stubs
    for stub in local_stubs:
        ConnectorStub(**stub)

    bucket_name = get_bucket_name(bucket)

    if dry_run:
        error_console.print(
            f"[DRY RUN] Would upload {len(local_stubs)} stubs to "
            f"{bucket_name}/{CONNECTOR_STUBS_PATH}"
        )
        result = {
            "dry_run": True,
            "stub_count": len(local_stubs),
            "bucket": bucket_name,
            "path": CONNECTOR_STUBS_PATH,
        }
        print_json(result)
        return

    # Write to GCS (replaces entire file)
    write_connector_stubs(bucket_name, local_stubs)

    error_console.print(
        f"[green]Synced {len(local_stubs)} stubs to {bucket_name}/{CONNECTOR_STUBS_PATH}[/green]"
    )
    result = {
        "dry_run": False,
        "stub_count": len(local_stubs),
        "bucket": bucket_name,
        "path": CONNECTOR_STUBS_PATH,
        "stub_ids": [stub.get("id") for stub in local_stubs],
    }
    print_json(result)

"""Helper functions for S3 operations."""

import json
import os
import time
from typing import Literal, Optional, Tuple, TypedDict, Union

import click
import requests
from loguru import logger

from gable.api.client import GableAPIClient
from gable.cli.helpers.npm import get_installed_package_dir
from gable.cli.helpers.repo_interactions import get_git_repo_info, get_pr_link
from gable.common_types import LineageDataFile
from gable.openapi import (
    Action1,
    CrossServiceDataStore,
    CrossServiceEdge,
    ErrorResponse,
    EventType,
    GetConfigResponse,
    OutputFormat,
    PostScaStartRunRequest,
    PrBaseBranch,
    S3PresignedUrl,
    StaticAnalysisCodeMetadata,
    StaticAnalysisToolConfig,
    StaticAnalysisToolMetadata,
    Type,
)


class GithubEventMetadata(TypedDict, total=False):
    """Metadata extracted from GitHub event data."""

    event_repo: Optional[str]
    event_type: Optional[EventType]
    repo_commit_timestamp: Optional[str]
    is_default_branch: Optional[bool]
    pr_base_branch: Optional[PrBaseBranch]
    pr_number: Optional[int]


class AdditionalMetadata(TypedDict, total=False):
    """Additional metadata for the StaticAnalysisCodeMetadata."""

    operating_system: Optional[str]
    has_uncommitted_changes: Optional[bool]
    namespace: Optional[str]
    docker_image_version: Optional[str]
    sca_config_version: Optional[str]


def extract_additional_metadata(
    additional_metadata: str, cli_namespace: Optional[str] = None
) -> AdditionalMetadata:
    try:
        additional_metadata_dict = json.loads(additional_metadata)
    except json.JSONDecodeError:
        logger.debug(f"Error parsing additional metadata: {additional_metadata}")
        additional_metadata_dict = {}
    env_namespace = additional_metadata_dict.get("namespace")

    # Resolve namespace conflict
    if cli_namespace is not None and env_namespace is not None:
        if cli_namespace != env_namespace:
            raise click.ClickException(
                f"Namespace conflict: CLI option '{cli_namespace}' does not match "
                f"environment variable '{env_namespace}'. Please use only one method "
                "to specify the namespace."
            )
    # Use CLI option if provided, otherwise fall back to env var
    resolved_namespace = cli_namespace if cli_namespace is not None else env_namespace

    return AdditionalMetadata(
        operating_system=additional_metadata_dict.get("operating_system"),
        has_uncommitted_changes=additional_metadata_dict.get("has_uncommitted_changes"),
        namespace=resolved_namespace,
        docker_image_version=additional_metadata_dict.get("docker_image_version"),
        sca_config_version=additional_metadata_dict.get("sca_config_version"),
    )


def extract_event_type(
    event_data: dict,
) -> EventType:
    event_type = os.getenv("GITHUB_EVENT_NAME")
    logger.debug(f"Event type: {event_type}")
    git_action = event_data.get("action", "")
    logger.debug(f"Action: {git_action}")
    if event_type == "pull_request":
        if git_action == "opened":
            return EventType.PULL_REQUEST_CREATED
        elif git_action == "synchronize":
            return EventType.PULL_REQUEST_UPDATED
    elif event_type == "issue_comment":
        if (
            git_action == "created"
            and "pull_request" in event_data.get("issue", {})
            and event_data.get("comment", {})
            .get("body", "")
            .lower()
            .startswith("/gable")
        ):
            return EventType.PULL_REQUEST_COMMENT
    elif event_type == "push":
        if event_data.get("ref", "") in [
            "refs/heads/main",
            "refs/heads/master",
        ]:
            return EventType.MERGE_TO_MAIN
    return EventType.UNKNOWN


def extract_github_event_metadata(
    event_data: dict,
    git_branch: str,
    user_event_type: EventType | None,
) -> GithubEventMetadata:
    """Extract metadata from GitHub event data for StaticAnalysisCodeMetadata.

    Args:
        event_data: The GitHub event JSON data
        git_branch: The current git branch name

    Returns:
        A dictionary with extracted metadata fields
    """
    # Extract repository info
    event_repo = event_data.get("repository", {}).get("full_name")
    event_type = (
        user_event_type
        if user_event_type is not None
        else extract_event_type(event_data)
    )
    logger.debug(f"Chosen event type for upload: '{event_type}'")

    # Get commit timestamp from different event types
    repo_commit_timestamp = None
    if "head_commit" in event_data:
        repo_commit_timestamp = event_data["head_commit"].get("timestamp")
    elif "pull_request" in event_data:
        pr_data = event_data.get("pull_request", {})
        # Try head.repo.pushed_at first, then updated_at
        repo_commit_timestamp = pr_data.get("head", {}).get("repo", {}).get(
            "pushed_at"
        ) or pr_data.get("updated_at")

    # Check if this is the default branch
    default_branch = event_data.get("repository", {}).get("default_branch")
    is_default_branch = default_branch == git_branch if default_branch else None

    # Get PR base branch
    pr_base_branch = None
    pr_number = None
    if "pull_request" in event_data:
        base_ref = event_data["pull_request"].get("base", {}).get("ref")
        base_sha = event_data["pull_request"].get("base", {}).get("sha")
        if base_ref or base_sha:
            pr_base_branch = PrBaseBranch(branch=base_ref, commit=base_sha)
        pr_number = event_data["pull_request"].get("number")
    elif "issue" in event_data:
        pr_number = event_data["issue"].get("number")
    return {
        "event_repo": event_repo,
        "event_type": event_type,
        "repo_commit_timestamp": repo_commit_timestamp,
        "is_default_branch": is_default_branch,
        "pr_base_branch": pr_base_branch,
        "pr_number": pr_number,
    }


def start_sca_run(
    client: GableAPIClient,
    project_root: str,
    action: Literal["register", "check", "upload"],
    output: str | None,
    include_unchanged_assets: bool | None,
    external_component_id: str | None,
    upload_type: Type | None,
    repo_name: str | None,
    external_run_id: str | None = None,
    namespace: str | None = None,
    user_event_type: EventType | None = None,
) -> Tuple[str, S3PresignedUrl | None, GetConfigResponse | None]:
    """Call the SCA start run API to get the S3 presigned URL to upload the SCA results

    Args:
        client: The Gable API client
        project_root: The root directory of the project to analyze

    Returns:
        A tuple of (run_id, presigned_url, config)
        config will be None if not present in the response

    Raises:
        ClickException: If the API call was not successful
    """
    try:
        git_info = get_git_repo_info(project_root)
    except click.ClickException:
        logger.debug(
            f"No git repository found at project root {project_root}, trying env vars instead, otherwise default values"
        )
        git_info = {
            "gitRemoteOriginHTTPS": os.environ.get(
                "GABLE_REMOTE_ORIGIN_HTTPS", "unknown"
            ),
            "gitBranch": os.environ.get("GABLE_BRANCH", "unknown"),
            "gitHash": os.environ.get("GABLE_HASH", "unknown"),
        }

    package_name, package_version = get_sca_package_info()
    include = True if include_unchanged_assets else False
    output_f = None
    if action == "check":
        if output == "markdown":
            output_f = OutputFormat.markdown
        elif output == "text":
            output_f = OutputFormat.text
        else:
            output_f = OutputFormat.json

    event_data = json.loads(os.getenv("GITHUB_EVENT", "{}"))
    logger.debug(f"All event data dict: {event_data}")
    github_metadata = extract_github_event_metadata(
        event_data, git_info["gitBranch"], user_event_type
    )
    logger.debug(f"GitHub metadata: {github_metadata}")
    additional_metadata: AdditionalMetadata = extract_additional_metadata(
        os.getenv("GABLE_ADDITIONAL_METADATA", "{}"), cli_namespace=namespace
    )

    # Call the SCA start run API to get the S3 presigned URL to upload the SCA results
    response, success, _status_code = client.post_sca_start_run(
        PostScaStartRunRequest(
            code_info=StaticAnalysisCodeMetadata(
                repo_uri=git_info["gitRemoteOriginHTTPS"],
                repo_branch=git_info["gitBranch"],
                repo_commit=git_info["gitHash"],
                project_root=project_root,
                external_component_id=external_component_id,
                repo_name=repo_name,
                operating_system=additional_metadata.get("operating_system"),
                has_uncommitted_changes=additional_metadata.get(
                    "has_uncommitted_changes"
                ),
                docker_image_version=additional_metadata.get("docker_image_version"),
                namespace=additional_metadata.get("namespace"),
                sca_config_version=additional_metadata.get("sca_config_version"),
                **github_metadata,
            ),
            sca_info=StaticAnalysisToolMetadata(
                name=package_name,
                version=package_version,
                config=StaticAnalysisToolConfig(
                    ingress_signatures=[],
                    egress_signatures=[],
                ),
            ),
            action=Action1(action),
            pr_link=get_pr_link(),
            output_format=output_f,
            include_unchanged_assets=include,
            type=upload_type,
            run_id=external_run_id,
        )
    )

    if not success or isinstance(response, ErrorResponse):
        if _status_code == 409:
            raise click.ClickException(
                f"A run with ID '{external_run_id}' already exists. "
                "Remove the 'run_id' field from your results file or use a unique ID.\n"
                f"Details: {response.message}"  # type: ignore
            )
        raise click.ClickException(
            f"Error starting static code analysis run: {response.title} - {response.message}"  # type: ignore
        )

    return response.runId, response.s3PresignedUrl, response.config


def get_sca_package_info() -> tuple[str, str]:
    """Get the name and version of the installed @gable-eng/sca package."""
    try:
        package_dir = get_installed_package_dir()
        package_json_path = os.path.join(package_dir, "package.json")
        with open(package_json_path, "r") as f:
            package_data = json.load(f)
            return (package_data.get("name", ""), package_data.get("version", ""))
    except Exception as e:
        logger.debug(f"Error getting SCA package info: {e}")
        return ("", "")


def poll_sca_job_status(
    api_client: GableAPIClient,
    job_id: str,
    timeout_seconds: float = 300,
    interval_seconds: float = 5,
) -> dict:
    """
    Poll the job status until it completes successfully or fails, or until timeout.

    Parameters:
        api_client (GableAPIClient): Client used to fetch job status.
        job_id (str): The ID of the job to check.
        timeout_seconds (float): Max seconds to poll before timing out.
        interval_seconds (float): Seconds to wait between polling attempts.

    Returns:
        dict: The final status response from the API.

    Raises:
        click.ClickException: If the job fails or polling times out.
    """
    start_time = time.time()
    logger.debug(f"Polling job status for job_id: {job_id}")
    poll_until_complete = False if timeout_seconds <= 0 else True
    while True:
        elapsed_time = time.time() - start_time

        if poll_until_complete and elapsed_time > timeout_seconds:
            raise click.ClickException(
                f"Timed out after {timeout_seconds}s waiting for job ID: {job_id}"
            )
        try:
            response, success, _ = api_client.get_sca_run_status(job_id)
        except requests.RequestException as error:
            click.echo(f"[retrying] Error polling job status: {error}", err=True)
            logger.error("Error polling job status: %s, retrying…", error)
            time.sleep(interval_seconds)
            continue
        if not success or isinstance(response, ErrorResponse):
            error_msg = (
                f"Error polling job status for job ID {job_id}: " f"{response.message}"
            )
            logger.error(error_msg)
            raise click.ClickException(error_msg)
        status_data = response.dict()
        job_status = status_data.get("status", "").lower()
        message = status_data.get("message", "")
        click.echo(
            f"[{int(elapsed_time)}s] Status for Job with ID {job_id}: {job_status}"
        )
        click.echo(f"{message}")
        if not poll_until_complete:
            return status_data

        if job_status == "success":
            return status_data

        if job_status == "error":
            error_msg = status_data.get("message", "No error message provided.")
            raise click.ClickException(
                f"Job failed with status '{job_status}': {error_msg}"
            )

        time.sleep(interval_seconds)


def upload_sca_results(
    run_id: str,
    presigned_url: S3PresignedUrl,
    lineage_data_file: Union[CrossServiceDataStore, CrossServiceEdge, LineageDataFile],
) -> None:
    """Upload SCA results to S3 using the presigned URL.

    Args:
        run_id: The ID of the run
        presigned_url: The S3 presigned URL to upload to
        lineage_data_file: The lineage object to serialize and upload
    """

    if isinstance(lineage_data_file, LineageDataFile):
        upload_request = LineageDataFile(
            run_id=run_id,
            paths=lineage_data_file.paths,
            external_component_id=lineage_data_file.external_component_id,
            name=lineage_data_file.name,
            metadata=lineage_data_file.metadata,
        )
    elif isinstance(lineage_data_file, CrossServiceDataStore):
        upload_request = CrossServiceDataStore(
            run_id=run_id,
            external_component_id=lineage_data_file.external_component_id,
            type=lineage_data_file.type,
            external_table_id=lineage_data_file.external_table_id,
            schema=lineage_data_file.schema_,
            table_metadata=lineage_data_file.table_metadata,
        )
    elif isinstance(lineage_data_file, CrossServiceEdge):
        upload_request = CrossServiceEdge(
            run_id=run_id,
            source_component_id=lineage_data_file.source_component_id,
            destination_component_id=lineage_data_file.destination_component_id,
            external_edge_id=lineage_data_file.external_edge_id,
            type=lineage_data_file.type,
            field_mappings=lineage_data_file.field_mappings,
            source=lineage_data_file.source,
            destination=lineage_data_file.destination,
        )
    else:
        raise ValueError(
            f"Unsupported lineage_data_file type: {type(lineage_data_file)}"
        )

    try:
        files = {
            "file": (
                "results.json",
                upload_request.json(by_alias=True, exclude_none=True).encode("utf-8"),
                "application/octet-stream",
            )
        }
        data = presigned_url.fields
        response = requests.post(presigned_url.url, files=files, data=data)
        response.raise_for_status()
        logger.debug("Successfully uploaded SCA results to S3")
    except requests.exceptions.HTTPError as e:
        error_msg = f"S3 upload failed with HTTP error: {e.response.text}"
        raise click.ClickException(error_msg)

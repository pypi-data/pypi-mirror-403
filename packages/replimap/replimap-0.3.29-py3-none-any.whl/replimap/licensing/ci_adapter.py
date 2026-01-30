"""
CI/CD environment detection and metadata extraction.

Provides structured CI environment information for:
- License binding (use repo ID instead of machine fingerprint)
- Audit logging (track CI usage)
- Analytics (understand CI adoption)

Supported Providers:
- GitHub Actions
- GitLab CI
- CircleCI
- Jenkins
- Azure DevOps
- Bitbucket Pipelines
- AWS CodeBuild
- Travis CI
- Buildkite

Usage:
    ci = detect_ci_environment()
    if ci:
        print(f"Running in {ci.provider}: {ci.repo}")
        fingerprint = ci.stable_identifier

    # Quick check
    if is_ci_environment():
        print("Running in CI")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CIEnvironment:
    """
    CI environment metadata.

    Attributes:
        provider: CI provider name (github, gitlab, circleci, etc.)
        repo: Repository identifier (typically owner/repo format)
        run_id: Unique run/job identifier
        actor: User or bot triggering the run
        branch: Branch name
        commit: Commit SHA
        pr_number: Pull request number if applicable
        extra: Provider-specific additional data
    """

    provider: str
    repo: str | None = None
    run_id: str | None = None
    actor: str | None = None
    branch: str | None = None
    commit: str | None = None
    pr_number: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "provider": self.provider,
            "repo": self.repo,
            "run_id": self.run_id,
            "actor": self.actor,
            "branch": self.branch,
            "commit": self.commit,
            "pr_number": self.pr_number,
        }
        if self.extra:
            result["extra"] = self.extra
        return result

    @property
    def stable_identifier(self) -> str:
        """
        Get a stable identifier for license binding.

        Format: {provider}:{repo}
        Example: github:acme/infrastructure

        This identifier remains constant across CI runs for the same repo,
        making it suitable for license seat allocation.
        """
        if self.repo:
            return f"{self.provider}:{self.repo}"
        return f"{self.provider}:unknown"

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        provider_names = {
            "github": "GitHub Actions",
            "gitlab": "GitLab CI",
            "circleci": "CircleCI",
            "jenkins": "Jenkins",
            "azure": "Azure DevOps",
            "bitbucket": "Bitbucket Pipelines",
            "codebuild": "AWS CodeBuild",
            "travis": "Travis CI",
            "buildkite": "Buildkite",
        }
        return provider_names.get(self.provider, self.provider.title())


def _detect_github() -> CIEnvironment | None:
    """Detect GitHub Actions environment."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return None

    return CIEnvironment(
        provider="github",
        repo=os.environ.get("GITHUB_REPOSITORY"),
        run_id=os.environ.get("GITHUB_RUN_ID"),
        actor=os.environ.get("GITHUB_ACTOR"),
        branch=os.environ.get("GITHUB_REF_NAME"),
        commit=os.environ.get("GITHUB_SHA"),
        pr_number=os.environ.get("GITHUB_PR_NUMBER"),
        extra={
            "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "event_name": os.environ.get("GITHUB_EVENT_NAME"),
            "runner_os": os.environ.get("RUNNER_OS"),
        },
    )


def _detect_gitlab() -> CIEnvironment | None:
    """Detect GitLab CI environment."""
    if os.environ.get("GITLAB_CI") != "true":
        return None

    return CIEnvironment(
        provider="gitlab",
        repo=os.environ.get("CI_PROJECT_PATH"),
        run_id=os.environ.get("CI_JOB_ID"),
        actor=os.environ.get("GITLAB_USER_LOGIN"),
        branch=os.environ.get("CI_COMMIT_REF_NAME"),
        commit=os.environ.get("CI_COMMIT_SHA"),
        pr_number=os.environ.get("CI_MERGE_REQUEST_IID"),
        extra={
            "pipeline_id": os.environ.get("CI_PIPELINE_ID"),
            "project_id": os.environ.get("CI_PROJECT_ID"),
        },
    )


def _detect_circleci() -> CIEnvironment | None:
    """Detect CircleCI environment."""
    if os.environ.get("CIRCLECI") != "true":
        return None

    # CircleCI uses CIRCLE_PROJECT_USERNAME/CIRCLE_PROJECT_REPONAME
    username = os.environ.get("CIRCLE_PROJECT_USERNAME", "")
    reponame = os.environ.get("CIRCLE_PROJECT_REPONAME", "")
    repo = f"{username}/{reponame}" if username and reponame else None

    return CIEnvironment(
        provider="circleci",
        repo=repo,
        run_id=os.environ.get("CIRCLE_BUILD_NUM"),
        actor=os.environ.get("CIRCLE_USERNAME"),
        branch=os.environ.get("CIRCLE_BRANCH"),
        commit=os.environ.get("CIRCLE_SHA1"),
        pr_number=os.environ.get("CIRCLE_PR_NUMBER"),
        extra={
            "job": os.environ.get("CIRCLE_JOB"),
            "workflow_id": os.environ.get("CIRCLE_WORKFLOW_ID"),
        },
    )


def _detect_jenkins() -> CIEnvironment | None:
    """Detect Jenkins environment."""
    if not os.environ.get("JENKINS_URL"):
        return None

    return CIEnvironment(
        provider="jenkins",
        repo=os.environ.get("JOB_NAME"),
        run_id=os.environ.get("BUILD_NUMBER"),
        actor=os.environ.get("BUILD_USER"),
        branch=os.environ.get("GIT_BRANCH"),
        commit=os.environ.get("GIT_COMMIT"),
        extra={
            "build_url": os.environ.get("BUILD_URL"),
            "node_name": os.environ.get("NODE_NAME"),
        },
    )


def _detect_azure() -> CIEnvironment | None:
    """Detect Azure DevOps environment."""
    if os.environ.get("TF_BUILD") != "True":
        return None

    return CIEnvironment(
        provider="azure",
        repo=os.environ.get("BUILD_REPOSITORY_NAME"),
        run_id=os.environ.get("BUILD_BUILDID"),
        actor=os.environ.get("BUILD_REQUESTEDFOR"),
        branch=os.environ.get("BUILD_SOURCEBRANCHNAME"),
        commit=os.environ.get("BUILD_SOURCEVERSION"),
        pr_number=os.environ.get("SYSTEM_PULLREQUEST_PULLREQUESTNUMBER"),
        extra={
            "project": os.environ.get("SYSTEM_TEAMPROJECT"),
            "definition_name": os.environ.get("BUILD_DEFINITIONNAME"),
        },
    )


def _detect_bitbucket() -> CIEnvironment | None:
    """Detect Bitbucket Pipelines environment."""
    if not os.environ.get("BITBUCKET_COMMIT"):
        return None

    # Bitbucket uses workspace/repo format
    workspace = os.environ.get("BITBUCKET_WORKSPACE", "")
    repo_slug = os.environ.get("BITBUCKET_REPO_SLUG", "")
    repo = f"{workspace}/{repo_slug}" if workspace and repo_slug else repo_slug or None

    return CIEnvironment(
        provider="bitbucket",
        repo=repo,
        run_id=os.environ.get("BITBUCKET_BUILD_NUMBER"),
        actor=None,  # Not available in Bitbucket
        branch=os.environ.get("BITBUCKET_BRANCH"),
        commit=os.environ.get("BITBUCKET_COMMIT"),
        pr_number=os.environ.get("BITBUCKET_PR_ID"),
        extra={
            "pipeline_uuid": os.environ.get("BITBUCKET_PIPELINE_UUID"),
        },
    )


def _detect_codebuild() -> CIEnvironment | None:
    """Detect AWS CodeBuild environment."""
    if not os.environ.get("CODEBUILD_BUILD_ID"):
        return None

    # Extract repo from source URL
    source_url = os.environ.get("CODEBUILD_SOURCE_REPO_URL", "")
    repo: str | None = None
    if source_url:
        # URL might be https://github.com/owner/repo.git
        parts = source_url.rstrip(".git").split("/")
        if len(parts) >= 2:
            repo = "/".join(parts[-2:])

    # Extract project name from ARN
    build_arn = os.environ.get("CODEBUILD_BUILD_ARN", "")
    project_name = None
    if build_arn:
        # ARN format: arn:aws:codebuild:region:account:build/project-name:build-id
        arn_parts = build_arn.split("/")
        if len(arn_parts) >= 2:
            project_name = arn_parts[-1].split(":")[0]

    return CIEnvironment(
        provider="codebuild",
        repo=repo,
        run_id=os.environ.get("CODEBUILD_BUILD_ID"),
        actor=os.environ.get("CODEBUILD_INITIATOR"),
        branch=os.environ.get("CODEBUILD_SOURCE_VERSION"),
        commit=os.environ.get("CODEBUILD_RESOLVED_SOURCE_VERSION"),
        extra={
            "project_name": project_name,
        },
    )


def _detect_travis() -> CIEnvironment | None:
    """Detect Travis CI environment."""
    if os.environ.get("TRAVIS") != "true":
        return None

    pr_number = os.environ.get("TRAVIS_PULL_REQUEST")
    # Travis sets TRAVIS_PULL_REQUEST to "false" string when not a PR
    if pr_number == "false":
        pr_number = None

    return CIEnvironment(
        provider="travis",
        repo=os.environ.get("TRAVIS_REPO_SLUG"),
        run_id=os.environ.get("TRAVIS_BUILD_NUMBER"),
        actor=None,
        branch=os.environ.get("TRAVIS_BRANCH"),
        commit=os.environ.get("TRAVIS_COMMIT"),
        pr_number=pr_number,
        extra={
            "job_number": os.environ.get("TRAVIS_JOB_NUMBER"),
        },
    )


def _detect_buildkite() -> CIEnvironment | None:
    """Detect Buildkite environment."""
    if os.environ.get("BUILDKITE") != "true":
        return None

    pr_number = os.environ.get("BUILDKITE_PULL_REQUEST")
    # Buildkite sets BUILDKITE_PULL_REQUEST to "false" string when not a PR
    if pr_number == "false":
        pr_number = None

    return CIEnvironment(
        provider="buildkite",
        repo=os.environ.get("BUILDKITE_REPO"),
        run_id=os.environ.get("BUILDKITE_BUILD_NUMBER"),
        actor=os.environ.get("BUILDKITE_BUILD_CREATOR"),
        branch=os.environ.get("BUILDKITE_BRANCH"),
        commit=os.environ.get("BUILDKITE_COMMIT"),
        pr_number=pr_number,
        extra={
            "pipeline": os.environ.get("BUILDKITE_PIPELINE_SLUG"),
            "organization": os.environ.get("BUILDKITE_ORGANIZATION_SLUG"),
        },
    )


# Ordered list of detection functions (more specific first)
_DETECTORS = [
    _detect_github,
    _detect_gitlab,
    _detect_circleci,
    _detect_azure,
    _detect_bitbucket,
    _detect_codebuild,
    _detect_travis,
    _detect_buildkite,
    _detect_jenkins,  # Jenkins last as it's more generic
]


def detect_ci_environment() -> CIEnvironment | None:
    """
    Detect CI environment and extract metadata.

    Checks for various CI providers in order and returns
    the first match, or None if not in a CI environment.

    Returns:
        CIEnvironment if running in CI, None otherwise.
    """
    for detector in _DETECTORS:
        result = detector()
        if result is not None:
            return result
    return None


def is_ci_environment() -> bool:
    """
    Check if running in any CI environment.

    This is a quick check without full metadata extraction.
    More efficient than calling detect_ci_environment() when
    you only need to know if you're in CI.
    """
    # Quick checks for common CI indicators
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "JENKINS_URL",
        "TRAVIS",
        "BUILDKITE",
        "TF_BUILD",
        "BITBUCKET_COMMIT",
        "CODEBUILD_BUILD_ID",
    ]
    return any(os.environ.get(var) for var in ci_indicators)


def get_ci_stable_identifier() -> str | None:
    """
    Get stable identifier for CI license binding.

    Returns:
        Stable identifier string (e.g., "github:owner/repo"),
        or None if not in CI.
    """
    ci = detect_ci_environment()
    if ci:
        return ci.stable_identifier
    return None

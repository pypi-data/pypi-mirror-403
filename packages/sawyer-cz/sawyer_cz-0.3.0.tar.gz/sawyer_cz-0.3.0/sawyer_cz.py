from commitizen.cz.conventional_commits.conventional_commits import ConventionalCommitsCz
from commitizen.cz.conventional_commits.conventional_commits import ConventionalCommitsAnswers
from commitizen.cz.utils import multiple_line_breaker, required_validator
from commitizen.question import CzQuestion
from commitizen.config.base_config import BaseConfig
import importlib.metadata
import json
import logging
import urllib.error
import urllib.request

__all__ = ["SawyerCZ"]



def _parse_scope(text: str) -> str:
    return "-".join(text.strip().split())


def _parse_subject(text: str) -> str:
    return required_validator(text.strip(".").strip(), msg="Subject is required.")


def _get_installed_version(dist_name: str) -> str | None:
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _get_latest_pypi_version(project: str) -> str | None:
    url = f"https://pypi.org/pypi/{project}/json"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload.get("info", {}).get("version")
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
        return None


def _is_outdated(installed: str, latest: str) -> bool | None:
    try:
        from packaging.version import Version  # type: ignore

        return Version(installed) < Version(latest)
    except Exception:
        if installed == latest:
            return False
        return None


class SawyerCZ(ConventionalCommitsCz):
    name = "sawyer_cz"
    _version_check_done = False

    def __init__(self, config: BaseConfig):
        super().__init__(config)

        if SawyerCZ._version_check_done:
            return
        SawyerCZ._version_check_done = True

        logger = logging.getLogger(__name__)

        installed = (
            _get_installed_version("sawyer-cz")
            or _get_installed_version("sawyer_cz")
            or _get_installed_version(__name__.split(".", 1)[0])
        )
        if not installed:
            return

        latest = _get_latest_pypi_version("sawyer-cz")
        if not latest:
            return

        outdated = _is_outdated(installed, latest)
        if outdated is True:
            logger.warning(
                "A newer version of sawyer-cz is available (installed=%s, latest=%s).",
                installed,
                latest,
            )

    def questions(self) -> list[CzQuestion]:
        return [
            {
                "type": "list",
                "name": "prefix",
                "message": "Select the type of change you are committing",
                "choices": [
                    {
                        "value": "fix",
                        "name": "fix: A bug fix. Correlates with PATCH in SemVer",
                        "key": "x",
                    },
                    {
                        "value": "feat",
                        "name": "feat: A new feature. Correlates with MINOR in SemVer",
                        "key": "f",
                    },
                    {
                        "value": "docs",
                        "name": "docs: Documentation only changes",
                        "key": "d",
                    },
                    {
                        "value": "style",
                        "name": (
                            "style: Changes that do not affect the "
                            "meaning of the code (white-space, formatting,"
                            " missing semi-colons, etc)"
                        ),
                        "key": "s",
                    },
                    {
                        "value": "refactor",
                        "name": (
                            "refactor: A code change that neither fixes "
                            "a bug nor adds a feature"
                        ),
                        "key": "r",
                    },
                    {
                        "value": "perf",
                        "name": "perf: A code change that improves performance",
                        "key": "p",
                    },
                    {
                        "value": "test",
                        "name": ("test: Adding missing or correcting existing tests"),
                        "key": "t",
                    },
                    {
                        "value": "build",
                        "name": (
                            "build: Changes that affect the build system or "
                            "external dependencies (example scopes: pip, docker, npm)"
                        ),
                        "key": "b",
                    },
                    {
                        "value": "ci",
                        "name": (
                            "ci: Changes to CI configuration files and "
                            "scripts (example scopes: GitLabCI)"
                        ),
                        "key": "c",
                    },
                    {
                        "value": "chore",
                        "name": "chore: Changes to the build process or auxiliary tools and libraries such as documentation generation",
                        "key": "h",
                    },
                ],
            },
            {
                "type": "input",
                "name": "scope",
                "message": (
                    "What is the scope of this change? (class or file name): (press [enter] to skip)\n"
                ),
                "filter": _parse_scope,
            },
            {
                "type": "input",
                "name": "subject",
                "filter": _parse_subject,
                "message": (
                    "Write a short and imperative summary of the code changes: (lower case and no period)\n"
                ),
            },
            {
                "type": "input",
                "name": "body",
                "message": (
                    "Provide additional contextual information about the code changes: (press [enter] to skip)\n"
                ),
                "filter": multiple_line_breaker,
            },
            {
                "type": "confirm",
                "name": "is_breaking_change",
                "message": "Is this a BREAKING CHANGE? Correlates with MAJOR in SemVer",
                "default": False,
            },
            {
                "type": "input",
                "name": "footer",
                "message": (
                    "Footer. Information about Breaking Changes and "
                    "reference issues that this commit closes: (press [enter] to skip)\n"
                ),
            },
        ]

    def message(self, answers: ConventionalCommitsAnswers) -> str:  # type: ignore[override]
        prefix = answers["prefix"]
        scope = answers["scope"]
        subject = answers["subject"]
        body = answers["body"]
        footer = answers["footer"]
        is_breaking_change = answers["is_breaking_change"]

        formatted_scope = f"({scope})" if scope else ""
        title = f"{prefix}{formatted_scope}"
        if is_breaking_change:
            if self.config.settings.get("breaking_change_exclamation_in_title", False):
                title = f"{title}!"
            footer = f"BREAKING CHANGE: {footer}"

        formatted_body = f"\n\n{body}" if body else ""
        formatted_footter = f"\n\n{footer}" if footer else ""

        return f"{title}: {subject}{formatted_body}{formatted_footter}"

    def schema(self) -> str:
        return (
            "<type>|<scope>: <subject>\n"
            "<BLANK LINE>\n"
            "<body>\n"
            "<BLANK LINE>\n"
            "(BREAKING CHANGE: )<footer>"
        )

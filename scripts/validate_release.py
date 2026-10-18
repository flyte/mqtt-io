"""Reject inconsistent GitHub release metadata before publishing packages."""

import ast
import configparser
import json
import os
from pathlib import Path

from packaging.version import InvalidVersion, Version


def validate_release(root: Path, event: dict) -> dict:
    """Return validated outputs for a published stable release or candidate."""
    if event.get("action") != "published":
        raise ValueError("Only release.published can publish packages")
    release = event["release"]
    if release.get("draft") is not False:
        raise ValueError("Draft releases cannot publish packages")

    config = configparser.ConfigParser()
    config.read(root / "setup.cfg")
    project = (root / "pyproject.toml").read_text()
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    package = ast.parse((root / "mqtt_io/__init__.py").read_text())
    runtime_version = next(
        ast.literal_eval(statement.value)
        for statement in package.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in statement.targets
        )
    )
    version = tomllib.loads(project)["tool"]["poetry"]["version"]
    if config["bumpversion"]["current_version"] != version or runtime_version != version:
        raise ValueError("Poetry, bumpversion and runtime versions must agree")
    if release["tag_name"] != version:
        raise ValueError("Release tag must exactly match the package version")
    try:
        parsed = Version(version)
    except InvalidVersion as error:
        raise ValueError("Package version must be a valid PEP 440 version") from error
    if str(parsed) != version or parsed.is_devrelease or parsed.is_postrelease or parsed.local or parsed.epoch:
        raise ValueError("Use a canonical stable or prerelease version without dev, post or local suffixes")
    if release.get("prerelease") is not parsed.is_prerelease:
        raise ValueError("GitHub prerelease flag must match the package version")
    return {"version": version, "stable": str(not parsed.is_prerelease).lower()}


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    outputs = validate_release(root, event)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for name, value in outputs.items():
            output.write(f"{name}={value}\n")
    print(f"Validated release {outputs['version']}; stable={outputs['stable']}")


if __name__ == "__main__":
    main()
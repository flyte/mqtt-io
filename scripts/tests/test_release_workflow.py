import configparser
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml
from packaging.version import Version


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = yaml.load(
    (ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader
)


class ReleaseWorkflowTest(unittest.TestCase):
    def test_release_trigger_and_dependencies(self):
        self.assertEqual(WORKFLOW["on"]["release"]["types"], ["published"])
        for job in ("publish", "build_docker_image"):
            self.assertIn("release_metadata", WORKFLOW["jobs"][job]["needs"])
            self.assertIn("test", WORKFLOW["jobs"][job]["needs"])
        condition = WORKFLOW["jobs"]["build_docker_image"]["if"]
        self.assertIn("always()", condition)
        self.assertIn("needs.test.result == 'success'", condition)
        self.assertIn("needs.release_metadata.result == 'success'", condition)
        self.assertIn("github.ref_type == 'branch'", condition)
        self.assertIn("github.ref_name != 'gh-pages'", condition)

    def test_docker_tags_without_running_docker(self):
        cases = (
            ("Publish release image", {"VERSION": "2.7.0rc1", "STABLE": "false"}, ["flyte/mqtt-io:2.7.0rc1"]),
            ("Publish release image", {"VERSION": "2.7.0", "STABLE": "true"}, ["flyte/mqtt-io:2.7.0", "flyte/mqtt-io:latest"]),
            ("Publish branch image", {"BRANCH_NAME": "release/2.7.0"}, ["flyte/mqtt-io:branch-release-2.7.0"]),
            ("Publish branch image", {"BRANCH_NAME": "latest"}, ["flyte/mqtt-io:branch-latest"]),
            ("Publish branch image", {"BRANCH_NAME": "2.7.0"}, ["flyte/mqtt-io:branch-2.7.0"]),
        )
        steps = WORKFLOW["jobs"]["build_docker_image"]["steps"]
        for name, environment, expected in cases:
            with self.subTest(environment=environment):
                script = next(step["run"] for step in steps if step.get("name") == name)
                result = subprocess.run(
                    ["bash", "-e", "-o", "pipefail", "-c", 'docker() { printf "%s\\n" "$@"; };\n' + script],
                    env={**os.environ, **environment},
                    check=True,
                    text=True,
                    capture_output=True,
                )
                arguments = result.stdout.splitlines()
                tags = [arguments[index + 1] for index, argument in enumerate(arguments) if argument == "-t"]
                self.assertEqual(tags, expected)

    def test_validator_cli_against_real_version_files(self):
        config = configparser.ConfigParser()
        config.read(ROOT / "setup.cfg")
        version = config["bumpversion"]["current_version"]
        prerelease = Version(version).is_prerelease
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            output = Path(directory) / "output"
            event.write_text(json.dumps({
                "action": "published",
                "release": {"tag_name": version, "prerelease": prerelease, "draft": False},
            }))
            result = subprocess.run(
                [os.sys.executable, str(ROOT / "scripts/validate_release.py")],
                env={**os.environ, "GITHUB_EVENT_PATH": str(event), "GITHUB_OUTPUT": str(output)},
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn(f"Validated release {version}", result.stdout)
            self.assertEqual(output.read_text(), f"version={version}\nstable={str(not prerelease).lower()}\n")


if __name__ == "__main__":
    unittest.main()
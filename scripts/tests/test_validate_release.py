import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "validate_release.py"
SPEC = importlib.util.spec_from_file_location("validate_release", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidateReleaseTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "mqtt_io").mkdir()

    def write_versions(self, version):
        (self.root / "pyproject.toml").write_text(
            f'[tool.poetry]\nversion = "{version}"\n'
        )
        (self.root / "setup.cfg").write_text(
            f"[bumpversion]\ncurrent_version = {version}\n"
        )
        (self.root / "mqtt_io/__init__.py").write_text(f'VERSION = "{version}"\n')

    def event(self, tag, prerelease, action="published", draft=False):
        return {
            "action": action,
            "release": {"tag_name": tag, "prerelease": prerelease, "draft": draft},
        }

    def test_candidate_and_stable_outputs(self):
        for version, prerelease in (("2.7.0rc1", True), ("2.7.0", False)):
            with self.subTest(version=version):
                self.write_versions(version)
                self.assertEqual(
                    MODULE.validate_release(self.root, self.event(version, prerelease)),
                    {"version": version, "stable": str(not prerelease).lower()},
                )

    def test_invalid_publication_events(self):
        self.write_versions("2.7.0rc1")
        events = (
            self.event("2.7.0rc1", False),
            self.event("2.7.0", True),
            self.event("v2.7.0rc1", True),
            self.event("2.7.0rc1", True, action="created"),
            self.event("2.7.0rc1", True, action="released"),
            self.event("2.7.0rc1", True, draft=True),
        )
        for event in events:
            with self.subTest(event=event), self.assertRaises(ValueError):
                MODULE.validate_release(self.root, event)

    def test_stable_version_cannot_be_marked_prerelease(self):
        self.write_versions("2.7.0")
        with self.assertRaisesRegex(ValueError, "prerelease flag"):
            MODULE.validate_release(self.root, self.event("2.7.0", True))

    def test_all_version_files_must_agree(self):
        for filename in ("setup.cfg", "mqtt_io/__init__.py"):
            with self.subTest(filename=filename):
                self.write_versions("2.7.0rc1")
                path = self.root / filename
                path.write_text(path.read_text().replace("2.7.0rc1", "2.7.0"))
                with self.assertRaisesRegex(ValueError, "versions must agree"):
                    MODULE.validate_release(self.root, self.event("2.7.0rc1", True))

    def test_non_release_versions_are_rejected(self):
        for version in ("2.7.0.dev1", "2.7.0.post1", "2.7.0+local", "1!2.7.0", "2.7.0-rc1", "not-a-version"):
            with self.subTest(version=version):
                self.write_versions(version)
                with self.assertRaises(ValueError):
                    MODULE.validate_release(self.root, self.event(version, True))


if __name__ == "__main__":
    unittest.main()
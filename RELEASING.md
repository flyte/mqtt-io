# Releasing MQTT IO

## Current Preparation

The local `release/2.7.0` branch is based on `develop` and prepares version
`2.7.0` after testing the published `2.7.0rc1` candidate. The minor version
includes the configurable SHT4x chip address as well as fixes since `2.6.0`.
The stable version change is prepared in this branch before merging into
`develop`. Local preparation does not commit, tag, push or publish. The existing
`2.7.0rc1` tag and release remain unchanged; stable needs its own reviewed tag.

## Versioning

[setup.cfg](setup.cfg) configures bumpversion. A version change updates:

- [pyproject.toml](pyproject.toml): package metadata.
- [mqtt_io/__init__.py](mqtt_io/__init__.py): runtime `VERSION`.
- [setup.cfg](setup.cfg): bumpversion's `current_version`.

The tag must exactly match the bare package version, for example `2.7.0rc1`
or `2.7.0`, without a `v` prefix. The previous `2.6.0` version change updated
these same three files. The GitHub prerelease checkbox must match the package
version: enabled for `2.7.0rc1`, disabled for `2.7.0`.

For candidates and the transition to stable, edit all three version files
together. The existing bumpversion configuration has only the default stable
version parser; do not run it against an `rc` version. For a future release
starting from a stable version, `bump2version` can prepare the next stable
version with automatic commit and tag creation disabled:

```sh
bump2version --no-commit --no-tag minor
```

Choose `patch`, `minor` or `major` according to the changes, then update
[CHANGELOG.md](CHANGELOG.md) and review all modified files. The defaults in
`setup.cfg` otherwise create both a commit and a tag.

## Local Checks

Use a virtual environment with Python 3.10 or 3.12 for development tools.
The package itself declares Python 3.9 or later. Never install project
dependencies into the Pi's system Python.

With Poetry installed, run the same checks used by CI:

```sh
poetry check
poetry install
poetry run pylint -d fixme mqtt_io
poetry run mypy --show-error-codes --strict --no-warn-unused-ignores mqtt_io
poetry run behave --tags '~fixme' mqtt_io/tests/features
poetry run pytest mqtt_io/tests/test_stream_reconnect.py
poetry run python -m unittest discover -s scripts/tests -v
poetry build
```

CI tests Python 3.10 and 3.12. Local success on a single Python version is
not a substitute for the full matrix or for testing the required hardware
modules. Inspect and test both the wheel and source archive from `dist/` before
deploying to another Pi. Finalize the changelog date only when releasing.

The prepared wheel was installed offline in an isolated Python 3.13 environment
on TestPi. Distribution/runtime versions and imports agree, `pip check` passes,
the stream-reconnect test passes, and Behave reports 27 scenarios passed with
16 skipped by the existing tags. These are runtime tests, not full Python 3.13
development-tool support: the older documentation dependencies require native
build prerequisites on that interpreter. GPIO and sensor hardware have not
been tested by these checks.

The TestPi runtime environment is `/home/benni/.venvs/mqtt-io-release`.
Its packages were transferred from the server and installed with `--no-index`;
no Pi firewall or proxy policy was changed. Build tools and the complete
Python 3.12 Poetry environment are on the server, not in system Python.

Local preparation checks on 2026-10-17:

- Python 3.12: full Poetry dependency installation, Pylint (10.00/10), strict
  Mypy (65 source files), stream reconnect and Behave all pass.
- The actual documentation renderer passes in a disposable repository copy,
  with only the Git version lookup and publication functions mocked.
- The original `2.7.0` preparation built a wheel and source archive; both passed
  `twine check`. Candidate builds must be rebuilt and tested after changing versions.
- Python 3.13 on ARM TestPi: the wheel installation and runtime tests above pass.
- Version consistency and the workflow YAML were checked on TestPi.

The subsequent `2.7.0rc1` workflow changes also pass eight release validation
and Docker-tag tests on Python 3.10, 3.12 and ARM Python 3.13. The actual Docker
shell steps are tested with a stub, without invoking Docker. The Actions
workflow passes `actionlint`. The rebuilt RC wheel and source archive pass
`twine check`; the RC wheel is installed and import-checked on TestPi, with
`pip check` and the stream-reconnect test passing. The Python 3.12 Pylint,
Mypy and Behave checks were repeated successfully for the RC preparation.

The candidate passed the Python 3.10 and 3.12 CI jobs and was published to PyPI.
On 2026-10-17, the published `2.7.0rc1` wheel and its dependencies were installed
directly from PyPI without cache in a separate Python 3.13.5 TestPi environment,
`/home/benni/.venvs/mqtt-io-pypi-2.7.0rc1.tHeNbh`. The wheel SHA256 matched PyPI,
package imports resolved inside that environment, and `pip check`, CLI help
and configuration validation passed. A temporary PyPI-only proxy was removed
after installation; the Pi's network isolation and read-only root remain intact.

The operator also confirmed MQTT messages arriving on Bennibus when running
the installed candidate with `python -I -m mqtt_io` and an absolute configuration
path. This avoids importing the local checkout. The configuration uses stdio
GPIO and a mock sensor, so this is an end-to-end MQTT test, not validation of
physical GPIO or sensors. Hardware-specific tests remain a separate requirement
for deployments using those modules. The stable commit must pass CI again
before merging and tagging; no stable publication is implied by these checks.

## Publication

The existing automation is in
[.github/workflows/ci.yml](.github/workflows/ci.yml):

- Pushes run tests; branch pushes other than `gh-pages` also publish branch
  Docker images after successful tests. Pushes other than `gh-pages` generate
  and publish documentation.
- Pull requests run tests without the Docker publication job.
- Branch pushes publish Docker images as `branch-<sanitized-full-branch-name>`,
  for example `branch-release-2.7.0`; they cannot overwrite versioned images or
  `latest`. Tag pushes do not publish Docker images. Docker publication and
  documentation regeneration are skipped for pushes to `gh-pages`.
- A GitHub release with action `published` works for both direct releases and
  releases published from drafts. Before publication,
  [scripts/validate_release.py](scripts/validate_release.py) checks that the tag,
  three version files and GitHub prerelease flag agree. Both publishing jobs
  require this validation and successful tests.
- Prereleases publish the candidate version (for example `2.7.0rc1`) to PyPI
  using `PYPI_API_TOKEN`, and only that version's Docker tag using
  `DOCKER_HUB_USERNAME` and `DOCKER_HUB_TOKEN`. They never update `latest`.
- Stable releases publish their stable PyPI version and both the versioned
  Docker tag and `latest`.

These publication steps require repository permissions and configured secrets.
Treat even a branch push as an external publication action, not just a backup.
For a fork, review or disable the publication jobs before pushing.

After review and successful tests, obtain explicit approval for the release
commit, push, version tag and GitHub release. Ensure the tag points to the exact
reviewed commit and that its version matches all three version files. Creating
and publishing a GitHub release is not a dry run. A prerelease publishes real
candidate packages to PyPI, not TestPyPI.

## Candidate To Stable

1. Commit and push `release/2.7.0`, then wait for its pipeline. The first candidate
  version in all three files is `2.7.0rc1`. Include the new `scripts/` files
  in the commit; both CI tests and release validation require them.
2. In GitHub, create tag `2.7.0rc1` on that exact candidate commit, enable
  "Set as a pre-release", then publish it. Creating a draft alone does not
  publish packages. Wait for tests, metadata validation, PyPI and Docker jobs.
3. Test the candidate on the required hardware. If fixes are needed, change all
  three version files to `2.7.0rc2`, commit the fixes, and create a new candidate
  tag and prerelease. Never move published tags or reuse PyPI versions.
4. After the candidate succeeds, prepare the stable commit in `release/2.7.0`
  before merging the pull request. Set all three versions to `2.7.0`, consolidate
  the candidate changelog entries into a dated stable release, rebuild and test,
  then commit and push only the release files. Keep local test configurations
  and credentials out of the commit. Wait for CI on the stable commit, review
  the changes, then merge the pull request into `develop`.
5. Verify that the resulting commit on `develop` contains the reviewed stable
  changes and passes CI. Create the new tag `2.7.0` on that exact commit and
  publish a new GitHub release without the prerelease checkbox. This publishes
  the stable package and updates Docker `latest`.

Do not promote the `2.7.0rc1` GitHub release to stable: its tag still contains
candidate package metadata. Editing or promoting a release does not use the
`published` creation path again; stable publication uses its own new tag and
release. A merge does not move an existing tag. Pipeline reruns may encounter
already uploaded PyPI files; investigate partial publication before retrying.

[Makefile](Makefile) also offers `make build` and `make publish`, which invoke
`poetry build` and `poetry publish`. Use the latter only as an explicitly chosen
manual alternative to the GitHub PyPI job, never in addition to it for the same
version. Never put publishing credentials into the repository.
import json
import os
from importlib.metadata import distribution
from pathlib import Path
from shutil import rmtree
from typing import Optional
from urllib.parse import urlparse

import pytest

from ewoksxrpd import pyfai_api


def pytest_addoption(parser):
    parser.addoption(
        "--skip-old-pyfai",
        action="store_true",
        default=False,
        help="Run only tests for latest pyFAI integration schema version",
    )
    parser.addoption(
        "--examples", action="store_true", default=False, help="generate example data"
    )


@pytest.fixture()
def ewoksxrpd_examples_path(request, tmp_path, ewoksxrpd_repo_dir) -> Path:
    if not request.config.option.examples or not ewoksxrpd_repo_dir:
        return tmp_path

    tmp_path = ewoksxrpd_repo_dir / "examples"
    rmtree(tmp_path / "data", ignore_errors=True)
    rmtree(tmp_path / "results", ignore_errors=True)
    rmtree(tmp_path / "transient", ignore_errors=True)

    return tmp_path


@pytest.fixture(scope="session")
def ewoksxrpd_repo_dir() -> Optional[Path]:
    dist = distribution("ewoksxrpd")

    # PEP 610: editable installs include direct_url.json
    try:
        data = dist.read_text("direct_url.json")
    except FileNotFoundError:
        return None

    if not data:
        return None

    info = json.loads(data)
    dir_info = info.get("dir_info", {})
    editable = bool(dir_info.get("editable"))
    if not editable:
        return None

    # Extract and resolve the filesystem path
    url = info.get("url")
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None

    path = Path(parsed.path)

    # Check that the directory exists and is writeable
    if path.is_dir() and os.access(path, os.W_OK):
        return path

    return None


_PYFAI_INTEGRATION_VERSIONS = [
    None,
    *range(
        pyfai_api.INTEGRATION_SCHEMA_VERSION_MIN,
        pyfai_api.INTEGRATION_SCHEMA_VERSION_MAX + 1,
    ),
]


@pytest.fixture(
    scope="session",
    params=_PYFAI_INTEGRATION_VERSIONS,
    ids=[f"v{v}" for v in _PYFAI_INTEGRATION_VERSIONS],
)
def pyfai_integration_version(request: pytest.FixtureRequest):
    """Fixture that provides all possible integration schema versions."""
    if request.config.getoption("--skip-old-pyfai") and request.param is not None:
        request.applymarker(
            pytest.mark.skip(
                reason="Skipping old pyFAI versions since --skip-old-pyfai was given"
            )
        )
    return request.param

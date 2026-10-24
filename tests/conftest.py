import pytest
from agp_remote_yam.dependency import runner_root

runner_root()


@pytest.fixture
def station():
    from agp_remote_yam.mock import MockStation
    return MockStation()


@pytest.fixture
def geometry(station, tmp_path):
    from agp_remote_yam.mock import MockBackend
    from agp_remote_yam.storage import Journal
    from types import SimpleNamespace
    return MockBackend(tmp_path, SimpleNamespace(), Journal(tmp_path)).geometry

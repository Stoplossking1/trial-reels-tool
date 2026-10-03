import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import fixture  # noqa: E402


@pytest.fixture(scope="session")
def clip(tmp_path_factory):
    """(video, transcript) of the synthetic talking head."""
    return fixture.make(tmp_path_factory.mktemp("clip"))


@pytest.fixture(scope="session")
def track(clip):
    from trialreels import face
    return face.track(clip[0])


@pytest.fixture(scope="session")
def transcript(clip):
    from trialreels.transcript import Transcript, finish
    return finish(Transcript.load(clip[1]), clip[0])

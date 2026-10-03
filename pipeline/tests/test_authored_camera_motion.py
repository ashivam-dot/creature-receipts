from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ytc.render import _plan
from ytc.spec import Beat, Visual


FALL = [1.12, 1.12, 0.5, 0.5, 0.08, 0.92]


def test_reused_archive_photo_can_follow_an_authored_event_direction():
    first = {"kind": "cover", "plate": object(), "move": (1.0, 1.08, 0.5, 0.5, 0.5, 0.5)}
    beat = Beat(text="The elevator fell.", visual=Visual(reuse=1, motion="pan_down", camera_move=FALL))

    shots = _plan(1, beat, SimpleNamespace(kind="image"), 100, 190, [], first)

    assert shots[0]["move"] == tuple(FALL)
    assert shots[0]["plate"] is first["plate"]


@pytest.mark.parametrize(
    "path",
    ([1.0, 1.1, 0.5], [0.99, 1.1, 0.5, 0.5, 0.5, 0.5], [1.0, 1.1, 0.5, 1.1, 0.5, 0.5]),
)
def test_authored_camera_path_stays_inside_the_render_plate(path):
    with pytest.raises(ValidationError):
        Visual(camera_move=path)

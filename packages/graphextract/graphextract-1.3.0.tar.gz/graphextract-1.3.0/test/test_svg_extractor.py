from pathlib import Path

import pytest
from graphextract.svg_extractor import extract_data

prj_dir = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def data():
    return extract_data(prj_dir / "test/fig.svg", x_formatter=int, y_formatter=int)


def test_extract_data_extracts_all_info_layers(data):
    for name in ("20", "25", "30", "35", "40", "extra"):
        assert name in data


def test_extract_data_extracts_correct_values(data):
    pts = sorted(data["20"])
    for i, pt_ref in enumerate(
        [
            (3, -1),
            (48, 1.5),
            (96, 4.5),
            (299, 7),
            (502, 8.5),
            (697, 8.6),
            (1001, 9.1),
            (1202, 9.1),
            (1506, 9.6),
            (1801, 9.5),
            (2003, 9.5),
        ]
    ):
        assert pts[i][0] == pytest.approx(pt_ref[0], abs=0.5)
        assert pts[i][1] == pytest.approx(pt_ref[1], abs=0.1)

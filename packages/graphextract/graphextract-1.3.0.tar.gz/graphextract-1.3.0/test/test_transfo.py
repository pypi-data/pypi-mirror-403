from pathlib import Path

from graphextract.transfo import Transfo
from svglib.svglib import svg2rlg

prj_dir = Path(__file__).parent.parent


def test_transfo_to_global_compares_to_inkscape():
    d = svg2rlg(prj_dir / "test/drawing.svg")

    (doc,) = d.contents
    layers = doc.contents

    # extract relevant layers
    lay1, lay2, lay3 = sorted([lay for lay in layers if lay.label.startswith("Layer")], key=lambda v: v.label)

    (shp1,) = lay1.contents
    (shp2,) = lay2.contents
    (gr,) = lay3.contents

    tr = Transfo(lay1.transform)
    gp = tr.to_global(shp1.x, shp1.y)
    assert gp == (-100, -50)

    tr = Transfo(lay2.transform)
    gp = tr.to_global(shp2.x, shp2.y)
    assert gp == (90, 0)

    ishp1, ishp2 = gr.contents
    tr = Transfo(lay2.transform)
    tr.compose(gr.transform)
    gp = tr.to_global(ishp1.x, ishp1.y)
    assert gp == (20, 120)
    gp = tr.to_global(ishp2.x, ishp2.y)
    assert gp == (90, 140)

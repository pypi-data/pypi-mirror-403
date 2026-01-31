"""
Main module that define function to extract positions in svg file
"""

import reportlab.graphics.shapes as shp
from svglib.svglib import svg2rlg

from .transfo import Transfo


def extract_tick(lay, svg_descr):
    tr_lay = Transfo(lay.transform)
    tr = Transfo(svg_descr.transform)

    pos_gr, label_gr = svg_descr.contents
    if isinstance(pos_gr.contents[0], shp.String):
        label_gr, pos_gr = pos_gr, label_gr

    assert pos_gr.transform == (1, 0, 0, 1, 0, 0)

    label = label_gr.contents[0].text
    path = pos_gr.contents[0].points
    gx0, gy0 = tr_lay.to_global(*tr.to_global(path[0], path[1]))
    gx1, gy1 = tr_lay.to_global(*tr.to_global(path[2], path[3]))
    return (gx0, gy0, gx1, gy1), label


def marker_pos(marker, single=True):
    """Local position of marker

    Raises: NotImplementedError if marker shape is unknown

    Args:
        marker (object): Shape to explore
        single (bool): whether to return single point (barycenter) or set of points

    Returns:
        List[(float, float)]: position of marker in local coordinates
    """
    tr = Transfo.identity()
    while isinstance(marker, shp.Group):  # groups are used to store transformations
        tr.compose(marker.transform)
        marker = marker.contents[0]

    if isinstance(marker, shp.Circle):
        return [tr.to_global(marker.cx, marker.cy)]

    if isinstance(marker, shp.Ellipse):
        return [tr.to_global(marker.cx, marker.cy)]

    if isinstance(marker, shp.Rect):
        return [tr.to_global(marker.x + marker.width / 2, marker.y + marker.height / 2)]

    if isinstance(marker, shp.Path):
        points = marker.points
        if single:
            nb = len(points) // 2
            return [tr.to_global(sum(points[::2]) / nb, sum(points[1::2]) / nb)]
        else:
            return [tr.to_global(lx, ly) for lx, ly in zip(points[::2], points[1::2])]

    raise NotImplementedError


def extract_markers(lay):
    """Extract position of markers from layer

    Args:
        lay (shp.Layer): layer to consider

    Returns:
        List[Tuple[float]]: list of (x,y) in global coordinates
    """
    tr = Transfo(lay.transform)

    # find markers
    pts = []
    if len(lay.contents) == 0:
        raise UserWarning(f"empty layer {lay.name}")
    elif len(lay.contents) == 1:  # either single point or curve
        (marker,) = lay.contents
        pts.extend([tr.to_global(lx, ly) for lx, ly in marker_pos(marker, single=False)])
    else:  # multiple markers, paths will be interpreted as shape of markers
        for marker in lay.contents:
            pts.extend([tr.to_global(lx, ly) for lx, ly in marker_pos(marker, single=True)])

    return pts


def extract_data(svg, x_formatter, y_formatter, x_type="linear", y_type="linear"):
    """Extract data from well formed svg file

    Args:
        svg (str|Path): path to svg file
        x_formatter (Callable): function to format x data
        y_formatter (Callable): function to format y data
        x_type (str): Type of axis (linear, log, bin)
        y_type (str): Type of axis (linear, log, bin)

    Returns:
        (dict): key is layer label, values are records of points
    """
    # read raw svg
    d = svg2rlg(str(svg))

    (doc,) = d.contents
    layers = doc.contents

    # extract relevant layers
    (lay_x_axis,) = [lay for lay in layers if lay.label == "x_axis"]
    (lay_y_axis,) = [lay for lay in layers if lay.label == "y_axis"]
    data_lays = [lay for lay in layers if lay.label not in ("figure", "x_axis", "y_axis")]

    # find reference system of coordinates
    assert lay_y_axis.transform == lay_x_axis.transform

    ticks_descr = [extract_tick(lay_x_axis, gr) for gr in lay_x_axis.contents if len(gr.contents) == 2]

    x_ticks = sorted([(pth[0], x_formatter(label)) for pth, label in ticks_descr])

    ticks_descr = [extract_tick(lay_y_axis, gr) for gr in lay_y_axis.contents if len(gr.contents) == 2]

    y_ticks = sorted([(pth[1], y_formatter(label)) for pth, label in ticks_descr])

    # convert svg data descr into values
    data = {}

    for lay in data_lays:
        markers = extract_markers(lay)

        records = []
        for cx, cy in markers:
            if x_type == "linear":
                x_rel_pos = (cx - x_ticks[0][0]) / (x_ticks[-1][0] - x_ticks[0][0])
                x = x_ticks[0][1] + (x_ticks[-1][1] - x_ticks[0][1]) * x_rel_pos
            elif x_type == "bin":
                dists = [(abs(cx - tx), lab) for tx, lab in x_ticks]
                x = min(dists)[1]
            else:
                raise UserWarning(f"unknown X axis type '{x_type}")

            if y_type == "linear":
                y_rel_pos = (cy - y_ticks[0][0]) / (y_ticks[-1][0] - y_ticks[0][0])
                y = y_ticks[0][1] + (y_ticks[-1][1] - y_ticks[0][1]) * y_rel_pos
            else:
                raise UserWarning(f"unknown Y axis type '{y_type}")

            records.append((x, y))

        data[lay.label] = records

    return data

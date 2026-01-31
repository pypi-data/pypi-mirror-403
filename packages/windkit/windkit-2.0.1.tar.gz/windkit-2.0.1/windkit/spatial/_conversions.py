from ._cuboid import to_cuboid
from ._point import to_point
from ._raster import to_raster
from ._point import to_stacked_point


def _to_spatial_struct(ds, struct=None):
    """
    Convert a stacked histogram dataset back to a target spatial structure.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset in any of the windkit spatial structures
    struct : {'point', 'stacked_point', 'cuboid', 'raster', None}
        Target spatial structure identifier. Supported:
        - 'point' : convert to point layout
        - 'stacked_point' : convert to stacked_point layout
        - 'cuboid' : convert to cuboid layout
        - 'raster' : convert to raster layout
        - None : no conversion, return input dataset unchanged

    Returns
    -------
    xr.Dataset
        Dataset converted to the requested spatial structure.

    Notes
    -----
    This function can be used in conjunction with get_spatial_struct to
    convert a dataset to a desired spatial structure.
    """
    if struct == "point":
        return to_point(ds)
    elif struct == "stacked_point":
        return to_stacked_point(ds)
    elif struct == "raster":
        return to_raster(ds)
    elif struct == "cuboid":
        return to_cuboid(ds)
    else:
        return ds

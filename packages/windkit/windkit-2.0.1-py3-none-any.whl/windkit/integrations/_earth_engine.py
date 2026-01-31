# (c) 2022 DTU Wind Energy
"""
Module that downloads elevation and roughness maps

Currently driven by the google earth engine, which is a cloud interface service to access
landcover and elevation data, among other things.

Installation & Setup
--------------------

The earth engine is an optional install, you can install with conda::

    conda install earthengine-api google-cloud-sdk

After installation you will have to do a one-time authentication
step from the command line: ``earthengine authenticate``

This will open a browser where you will have to allow google to use
you google account to retrieve data from the google servers. If you are on a machine
without the ability to use a browser (such as an HPC
cluster), you will have to use ``earthengine authenticate --quiet``, which requires you to
to manually copy the authentication code into the terminal.

In addition, you will have to `sign up
<https://signup.earthengine.google.com/#!/>`_ for the google earth engine and give
a reason why you want to use the program. Please pay particular attention to
their terms of service.

Automated Datasets
------------------

Currently, the databases that have been added are the Copernicus Global Land Cover
(CGLS-LC100), Copernicus CORINE land Cover (CORINE), MODIS Global Land Cover MCD12Q1
(MODIS), Globcover and WorldCover
(https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100) as landcover databases and
NASA SRTM Digital Elevation 30m(SRTM), ALOS DSM: Global 30 (ALOS) and NASADEM
(https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001?hl=en) as elevation databases.

The landcover databases have standard conversion tables that are included in
``windkit/data/landcover_tables``.

Google Earth Engine provides lists of
`elevation
<https://developers.google.com/earth-engine/datasets/tags/elevation>`_ and
`land cover
<https://developers.google.com/earth-engine/datasets/tags/landcover>`_
data sources, which provide additional details about the various datasources used
in this library.
"""

import logging
import math
import tempfile
import urllib.request
import warnings
from pathlib import Path

import rioxarray

from ..spatial import BBox, clip

CRS_GEOGRAPHIC = "EPSG:4326"

# Dataset configuration: maps datasource name to (url, band, is_collection)
_DATASET_CONFIG = {
    "CGLS-LC100": (
        "COPERNICUS/Landcover/100m/Proba-V/Global/2015",
        "discrete_classification",
        False,
    ),
    "CORINE": ("COPERNICUS/CORINE/V20/100m/2018", "landcover", False),
    "MODIS": ("MODIS/006/MCD12Q1/2018_01_01", "LC_Type1", False),
    "SRTM": ("USGS/SRTMGL1_003", "elevation", False),
    "NASADEM": ("NASA/NASADEM_HGT/001", "elevation", False),
    "ALOS": ("JAXA/ALOS/AW3D30/V2_2", "AVE_DSM", False),
    "Globcover": ("ESA/GLOBCOVER_L4_200901_200912_V2_3", "landcover", False),
    "WorldCover": ("ESA/WorldCover/v100", "Map", True),
}

ELEVATION_DATASETS = {"SRTM", "ALOS", "NASADEM"}
LIST_DATA_SOURCES = list(_DATASET_CONFIG.keys())

logger = logging.getLogger(__name__)

# Initialize Google Earth Engine
try:
    import ee as earth_engine

    try:
        credentials_path = Path.home() / "earth_engine.json"
        if credentials_path.exists():
            service_account = "windkit@windkit.iam.gserviceaccount.com"
            credentials = earth_engine.ServiceAccountCredentials(
                service_account, str(credentials_path)
            )
            earth_engine.Initialize(credentials)
        else:
            earth_engine.Initialize()
    except Exception:
        warnings.warn(
            "Could not initialize Google Earth Engine. Run 'earth_engine.Authenticate()' and try again."
        )

except ImportError:
    earth_engine = None


def _bbox_to_ee_geometry(bbox):
    return earth_engine.Geometry(bbox.__geo_interface__, bbox.crs.to_string())


def _get_image(datasource):
    """Get image from Google Earth Engine for the specified datasource.

    Parameters
    ----------
    datasource : str
        One of: 'CGLS-LC100', 'CORINE', 'MODIS', 'Globcover', 'WorldCover',
        'SRTM', 'ALOS', 'NASADEM'

    Returns
    -------
    image : ee.Image
        Google Earth Engine image for the specified band
    """
    if earth_engine is None:
        raise ValueError(
            "ee (earthengine-api) is required to get maps from Google Earth Engine"
        )

    if datasource not in _DATASET_CONFIG:
        valid_sources = ", ".join(LIST_DATA_SOURCES)
        raise ValueError(f"Please specify a valid data source from {valid_sources}")

    url, band, is_collection = _DATASET_CONFIG[datasource]

    if is_collection:
        dataset = earth_engine.ImageCollection(url).first()
    else:
        dataset = earth_engine.Image(url)

    return dataset.select(band)


def _get_ee_map(lat, lon, buffer_dist=20000, source="SRTM", vector=False):
    """Extract map from a given lat, lon

    Extract the smallest square which fits a cirle with radius buffer_dist
    around the coordinates lat,lon.

    Parameters
    ----------
    lat : float
        Center latitude from which we extract a map
    lon : float
        Center longitude from which we extract a map
    buffer_dist : int, optional
        Distance in meters from the given (lat,lon) where a map is extracted, by default 20000
    source : str {"CGLS-LC100", "CORINE", "MODIS", "Globcover", "WorldCover", "SRTM", "ALOS", "NASADEM"}, optional
        Landcover or elevation datasource, by default "SRTM"
    vector:
        If true, return the map in vector format else return a raster map
    """
    if vector:
        raise NotImplementedError("This feature is not yet available.")

    bbox = BBox.utm_bbox_from_geographic_coordinate(lon, lat, buffer_dist)
    ras = _get_raster_map_from_earth_engine(bbox, dataset=source)
    return ras


def _compute_aligned_origin(bbox_min, bbox_max, scale, origin):
    """Compute a new origin aligned to the native grid but near the bbox.

    This prevents Earth Engine from computing pixels from a distant origin
    (e.g., -180 degrees) to the bbox by finding the nearest grid-aligned
    point just outside the bbox.

    Parameters
    ----------
    bbox_min : float
        Minimum bound of bbox in this dimension (west or south)
    bbox_max : float
        Maximum bound of bbox in this dimension (east or north)
    scale : float
        Pixel scale (positive or negative)
    origin : float
        Native grid origin

    Returns
    -------
    float
        New origin aligned to native grid, positioned just outside the bbox
    """
    # Choose reference bound based on scale direction
    # Positive scale: origin at min side, negative scale: origin at max side
    reference_bound = bbox_min if scale > 0 else bbox_max
    n_pixels = math.floor((reference_bound - origin) / scale)
    return origin + n_pixels * scale


def _create_aligned_transform(native_transform, bbox):
    """Create an adjusted transform aligned to the native grid near the bbox.

    Parameters
    ----------
    native_transform : list
        Earth Engine transform: [xScale, xShear, xOrigin, yShear, yScale, yOrigin]
    bbox : BBox
        Bounding box for the download

    Returns
    -------
    list or None
        Adjusted transform, or None if transform cannot be computed
    """
    x_scale, x_shear, x_origin, y_shear, y_scale, y_origin = native_transform

    if x_scale == 0 or y_scale == 0:
        return None

    west, south, east, north = bbox.bounds()

    new_x_origin = _compute_aligned_origin(west, east, x_scale, x_origin)
    new_y_origin = _compute_aligned_origin(south, north, y_scale, y_origin)

    return [x_scale, x_shear, new_x_origin, y_shear, y_scale, new_y_origin]


def _get_download_url(ee_image, download_params, dataset):
    """Get download URL, falling back to scale if crs_transform fails.

    Some datasets (e.g., NASADEM) may not respect the adjusted transform origin
    and fail with grid dimension errors.

    Parameters
    ----------
    ee_image : ee.Image
        Earth Engine image
    download_params : dict
        Download parameters (may be modified in place)
    dataset : str
        Dataset name for logging

    Returns
    -------
    str
        Download URL
    """
    try:
        return ee_image.getDownloadURL(download_params)
    except Exception as e:
        if "crs_transform" in download_params and "grid dimensions" in str(e).lower():
            logger.debug(
                f"crs_transform failed for {dataset}, falling back to scale: {e}"
            )
            del download_params["crs_transform"]
            download_params["scale"] = ee_image.projection().nominalScale().getInfo()
            return ee_image.getDownloadURL(download_params)
        raise


def _get_raster_map_from_earth_engine(bbox, dataset="NASADEM", band=None):
    """
    Get map from Google Earth Engine.

    Parameters
    ----------
    bbox : windkit.spatial.BBox
        Bounding box of the map to download.

    dataset : str, optional
        Dataset to retrieve, by default "NASADEM"

    band : str, optional
        Band to retrieve, by default None

    Returns
    -------
    da : xarray.DataArray
        DataArray with the map

    Notes
    -----
    When the requested CRS matches the dataset's native CRS, the download uses
    `crs_transform` to preserve exact pixel alignment with the source data.
    When the CRS differs, `scale` is used which may result in slight pixel
    misalignment (typically sub-pixel shifts).
    """
    if earth_engine is None:
        raise ValueError(
            "ee (earthengine-api) is required to get maps from Google Earth Engine"
        )

    if not isinstance(bbox, BBox):
        raise ValueError("bbox must be a BBox object or a windkit.spatial.BBox object.")

    ee_image = _get_image(dataset)
    projection_info = ee_image.projection().getInfo()
    native_crs = projection_info.get("crs")
    native_transform = projection_info.get("transform")
    requested_crs = f"EPSG:{bbox.crs.to_epsg()}"

    download_params = {
        "region": _bbox_to_ee_geometry(bbox.reproject(CRS_GEOGRAPHIC)),
        "format": "GEO_TIFF",
        "crs": requested_crs,
    }

    # Use crs_transform for precise alignment when CRS matches
    crs_matches = native_crs == requested_crs and native_transform is not None
    adjusted_transform = (
        _create_aligned_transform(native_transform, bbox) if crs_matches else None
    )

    if adjusted_transform is not None:
        download_params["crs_transform"] = adjusted_transform
    else:
        download_params["scale"] = ee_image.projection().nominalScale().getInfo()

    download_url = _get_download_url(ee_image, download_params, dataset)

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    try:
        logger.debug(f"Downloading file {tmpfile.name}")
        urllib.request.urlretrieve(download_url, tmpfile.name)

        da = rioxarray.open_rasterio(tmpfile.name)
        da = da.rename({"spatial_ref": "crs", "x": "west_east", "y": "south_north"})
        da = da.drop_vars("band", errors="i")
        da.name = "elevation" if dataset in ELEVATION_DATASETS else "landcover"
        da = clip(da, bbox)
        da = da.sortby(["south_north", "west_east"])
        return da
    finally:
        tmpfile.close()
        Path(tmpfile.name).unlink()

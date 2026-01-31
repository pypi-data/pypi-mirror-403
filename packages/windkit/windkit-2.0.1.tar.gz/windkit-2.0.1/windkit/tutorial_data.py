"""Download and load tutorial datasets for windkit examples.

This module provides functions to download tutorial data from Zenodo,
cache it locally, and load it into memory as windkit-compatible objects.
"""

import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import requests
import xarray as xr
from platformdirs import user_data_dir

# Constants duplicated from config to avoid loading pydantic on import
_APPNAME = "windkit"
_APPAUTHOR = "DTU Wind Energy"

_ZENODO_BASE_URL = "https://zenodo.org/records/18269314/files/"

_TUTORIAL_DATASETS = {
    "serra_santa_luzia": "SerraSantaLuzia.zip",
}


def _check_internet_connection():
    """Check if internet connection is available."""
    try:
        requests.get("https://www.google.com", timeout=5)
    except requests.ConnectionError:
        raise ConnectionError(
            "No internet connection. Cannot download tutorial data."
        ) from None


def _download_file(url, destination):
    """Download a file from URL to destination path."""
    response = requests.get(url)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download from {url}. Status code: {response.status_code}"
        )
    with open(destination, "wb") as f:
        f.write(response.content)


def _download_tutorial_data(zip_path):
    """Download tutorial data zip from Zenodo."""
    _check_internet_connection()

    filename = zip_path.name
    url = f"{_ZENODO_BASE_URL}{filename}?download=1"

    print(f"Downloading {filename} from Zenodo...")
    _download_file(url, zip_path)
    print(f"Downloaded {filename} to {zip_path}")


def _extract_zip(zip_path, extract_dir):
    """Extract a zip file to the specified directory."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)


def _load_serra_santa_luzia(path):
    """Load the Serra Santa Luzia tutorial dataset."""
    return SimpleNamespace(
        bwc=xr.load_dataset(path / "bwc.nc"),
        wtg=xr.load_dataset(path / "wtg.nc"),
        turbines=xr.load_dataset(path / "turbines.nc"),
        elev=gpd.read_file(path / "elev.gpkg", engine="pyogrio"),
        rgh=gpd.read_file(path / "rgh.gpkg", engine="pyogrio"),
    )


# Registry mapping dataset names to their loader functions
_DATASET_LOADERS = {
    "serra_santa_luzia": _load_serra_santa_luzia,
}


def _validate_dataset_name(name):
    """Validate that the dataset name is known."""
    if name not in _TUTORIAL_DATASETS:
        available = ", ".join(_TUTORIAL_DATASETS)
        raise ValueError(
            f"Invalid dataset name '{name}'. Available datasets: {available}"
        )


def _get_dataset_paths(name):
    """Get the paths for a dataset's cache directory, zip file, and extract dir."""
    base_dir = Path(user_data_dir(_APPNAME, _APPAUTHOR, roaming=True))
    tutorial_dir = base_dir / "tutorial_data" / name
    zip_path = tutorial_dir / _TUTORIAL_DATASETS[name]
    extract_dir = tutorial_dir / "extracted"
    return tutorial_dir, zip_path, extract_dir


def get_tutorial_data(name, force_download=False):
    r"""Download and extract tutorial data, returning the path to the folder.

    Downloads tutorial data from Zenodo if not already cached, extracts it,
    and returns the path to the extracted folder. Use ``load_tutorial_data``
    to load the files into memory as windkit objects.

    The local cache is stored in the user data directory under the name "windkit".
    On Windows, this is typically located at:

    ``C:\Users\<username>\AppData\Roaming\windkit\tutorial_data``

    On Linux, it is typically located at:

    ``/home/<username>/.local/share/windkit/tutorial_data``

    You can check the location of the user data directory using the ``user_data_dir``
    function from the ``platformdirs`` package.

    Available Datasets
    ------------------

    **serra_santa_luzia**

    A wind farm site in Portugal with 15 turbines. Contains the following files:

    - ``bwc.nc`` - Binned Wind Climate (xarray.Dataset)
        Single-point observed wind climate with 12 sectors and 32 wind speed bins.
        Use with ``xr.load_dataset()`` or ``wk.read_bwc()``.

    - ``wtg.nc`` - Wind Turbine Generator (xarray.Dataset)
        Bonus 1 MW turbine with power curve and thrust coefficient.
        Use with ``xr.load_dataset()`` or ``wk.read_wtg()``.

    - ``turbines.nc`` - Wind Turbines (xarray.Dataset)
        15 turbine positions with coordinates and WTG assignments.
        Use with ``xr.load_dataset()`` or ``wk.read_wind_turbines()``.

    - ``elev.gpkg`` - Elevation Map (geopandas.GeoDataFrame)
        Elevation contour lines for the site terrain.
        Use with ``gpd.read_file()`` or ``wk.read_elevation_map()``.

    - ``rgh.gpkg`` - Roughness Map (geopandas.GeoDataFrame)
        Land cover roughness polygons for the site.
        Use with ``gpd.read_file()`` or ``wk.read_roughness_map()``.

    - ``bwc.omwc`` - Observed Wind Climate (WAsP OMWC format)
        Use with ``wk.read_bwc()``.

    - ``Bonus1MW.wtg`` - Wind Turbine Generator (WAsP WTG format)
        Use with ``wk.read_wtg()``.

    - ``SerraSantaLuzia.map`` - Combined Map (WAsP MAP format)
        Elevation and roughness data in WAsP vector format.
        Use with ``wk.read_elevation_map()`` or ``wk.read_roughness_map()``.

    - ``turbines.csv`` - Turbine positions (CSV format)
        Use with ``wk.read_wind_turbines()``.

    Parameters
    ----------
    name : str
        Name of the dataset to download. Currently available: "serra_santa_luzia".
    force_download : bool, optional
        If True, forces re-download and re-extraction even if data already exists.
        Default is False.

    Returns
    -------
    Path
        Path to the folder containing the extracted tutorial data files.

    Raises
    ------
    ValueError
        If the name is not a valid dataset name.
    ConnectionError
        If there is no internet connection when trying to download the data.
    RuntimeError
        If the download fails or the status code is not 200.

    Examples
    --------
    >>> import windkit as wk
    >>> path = get_tutorial_data("serra_santa_luzia")
    >>> path
    PosixPath('/home/user/.local/share/windkit/tutorial_data/serra_santa_luzia/extracted')
    >>> bwc = wk.read_bwc(path / "bwc.omwc")
    >>> bwc
    <xarray.Dataset> Size: 4kB
    Dimensions:       (point: 1, sector: 12, wsbin: 32)
    ...

    See Also
    --------
    load_tutorial_data : Load tutorial data files directly into memory.
    """
    _validate_dataset_name(name)

    tutorial_dir, zip_path, extract_dir = _get_dataset_paths(name)
    tutorial_dir.mkdir(parents=True, exist_ok=True)

    if force_download and extract_dir.exists():
        shutil.rmtree(extract_dir)

    if not zip_path.exists() or force_download:
        _download_tutorial_data(zip_path)

    if not extract_dir.exists() or force_download:
        _extract_zip(zip_path, extract_dir)

    return extract_dir


def load_tutorial_data(name, force_download=False):
    r"""Download, extract, and load tutorial data into memory.

    Convenience function that downloads the tutorial data, extracts it,
    and loads all files into memory as windkit-compatible objects.

    The local cache is stored in the user data directory under the name "windkit".
    On Windows, this is typically located at:

    ``C:\Users\<username>\AppData\Roaming\windkit\tutorial_data``

    On Linux, it is typically located at:

    ``/home/<username>/.local/share/windkit/tutorial_data``

    Parameters
    ----------
    name : str
        Name of the dataset to download. Currently available: "serra_santa_luzia".
    force_download : bool, optional
        If True, forces re-download and re-extraction even if data already exists.
        Default is False.

    Returns
    -------
    SimpleNamespace
        Object with loaded datasets as attributes. For "serra_santa_luzia":

        - ``bwc`` - Binned Wind Climate (xarray.Dataset)
        - ``wtg`` - Wind Turbine Generator (xarray.Dataset)
        - ``turbines`` - Wind Turbines (xarray.Dataset)
        - ``elev`` - Elevation Map (geopandas.GeoDataFrame)
        - ``rgh`` - Roughness Map (geopandas.GeoDataFrame)

    Raises
    ------
    ValueError
        If the name is not a valid dataset name.
    ConnectionError
        If there is no internet connection when trying to download the data.
    RuntimeError
        If the download fails or the status code is not 200.

    Examples
    --------
    >>> data = load_tutorial_data("serra_santa_luzia")
    >>> data.bwc
    <xarray.Dataset> Size: 4kB
    Dimensions:       (point: 1, sector: 12, wsbin: 32)
    ...
    >>> data.turbines
    <xarray.Dataset> Size: 1kB
    Dimensions:      (point: 15)
    ...

    See Also
    --------
    get_tutorial_data : Get the path to tutorial data without loading into memory.
    """
    path = get_tutorial_data(name, force_download)
    return _DATASET_LOADERS[name](path)

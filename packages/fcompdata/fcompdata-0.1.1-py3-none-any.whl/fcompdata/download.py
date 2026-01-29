"""
Download utilities for large M-competition datasets.

This module handles downloading and caching of datasets that are too large
to bundle with the package (e.g., M4 with 100,000 series).
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

# Zenodo URLs for M4 dataset by frequency
M4_URLS = {
    "yearly": "https://zenodo.org/api/records/4656379/files/m4_yearly_dataset.zip/content",
    "quarterly": "https://zenodo.org/api/records/4656410/files/m4_quarterly_dataset.zip/content",
    "monthly": "https://zenodo.org/api/records/4656480/files/m4_monthly_dataset.zip/content",
    "weekly": "https://zenodo.org/api/records/4656522/files/m4_weekly_dataset.zip/content",
    "daily": "https://zenodo.org/api/records/4656548/files/m4_daily_dataset.zip/content",
    "hourly": "https://zenodo.org/api/records/4656589/files/m4_hourly_dataset.zip/content",
}

M4_FILENAMES = {
    "yearly": "m4_yearly_dataset.tsf",
    "quarterly": "m4_quarterly_dataset.tsf",
    "monthly": "m4_monthly_dataset.tsf",
    "weekly": "m4_weekly_dataset.tsf",
    "daily": "m4_daily_dataset.tsf",
    "hourly": "m4_hourly_dataset.tsf",
}


def get_data_home() -> Path:
    """
    Get the path to the fcompdata data directory.

    Returns ~/.fcompdata by default. Creates the directory if it doesn't exist.

    Returns
    -------
    Path
        Path to data directory
    """
    data_home = Path.home() / ".fcompdata"
    data_home.mkdir(parents=True, exist_ok=True)
    return data_home


def _download_and_extract_zip(url: str, filename: str, dest_dir: Path) -> Path:
    """
    Download a zip file and extract the specified file.

    Parameters
    ----------
    url : str
        URL to download from
    filename : str
        Name of file to extract from zip
    dest_dir : Path
        Directory to save extracted file

    Returns
    -------
    Path
        Path to extracted file
    """
    dest_path = dest_dir / filename

    print(f"Downloading {filename}...")
    with urlopen(url) as response:
        zip_data = io.BytesIO(response.read())

    print(f"Extracting {filename}...")
    with zipfile.ZipFile(zip_data) as zf:
        # Find the .tsf file in the archive
        tsf_files = [n for n in zf.namelist() if n.endswith(".tsf")]
        if not tsf_files:
            raise ValueError(f"No .tsf file found in archive from {url}")
        with zf.open(tsf_files[0]) as src, open(dest_path, "wb") as dst:
            dst.write(src.read())

    print(f"Saved to {dest_path}")
    return dest_path


def download_m4(frequency: str | None = None, force: bool = False) -> dict[str, Path]:
    """
    Download M4 competition dataset from Zenodo.

    The M4 dataset contains 100,000 time series across 6 frequencies.
    Data is cached in ~/.fcompdata/ for subsequent use.

    Parameters
    ----------
    frequency : str, optional
        Specific frequency to download: 'yearly', 'quarterly', 'monthly',
        'weekly', 'daily', or 'hourly'. If None, downloads all frequencies.
    force : bool, default False
        If True, re-download even if files exist locally.

    Returns
    -------
    dict[str, Path]
        Dictionary mapping frequency names to local file paths.

    Examples
    --------
    >>> from fcompdata.download import download_m4
    >>> # Download all M4 data
    >>> paths = download_m4()
    >>> # Download only yearly data
    >>> paths = download_m4(frequency='yearly')
    """
    data_home = get_data_home()
    m4_dir = data_home / "m4"
    m4_dir.mkdir(parents=True, exist_ok=True)

    if frequency is not None:
        if frequency not in M4_URLS:
            raise ValueError(
                f"Unknown frequency '{frequency}'. "
                f"Must be one of: {list(M4_URLS.keys())}"
            )
        frequencies = [frequency]
    else:
        frequencies = list(M4_URLS.keys())

    paths = {}
    for freq in frequencies:
        dest_path = m4_dir / M4_FILENAMES[freq]

        if dest_path.exists() and not force:
            print(f"{freq}: Already downloaded ({dest_path})")
            paths[freq] = dest_path
        else:
            paths[freq] = _download_and_extract_zip(
                M4_URLS[freq], M4_FILENAMES[freq], m4_dir
            )

    return paths


def get_m4_path(frequency: str) -> Path | None:
    """
    Get path to locally cached M4 data file.

    Parameters
    ----------
    frequency : str
        Frequency: 'yearly', 'quarterly', 'monthly', 'weekly', 'daily', 'hourly'

    Returns
    -------
    Path or None
        Path to local file if it exists, None otherwise.
    """
    if frequency not in M4_FILENAMES:
        raise ValueError(
            f"Unknown frequency '{frequency}'. "
            f"Must be one of: {list(M4_FILENAMES.keys())}"
        )

    path = get_data_home() / "m4" / M4_FILENAMES[frequency]
    return path if path.exists() else None


def clear_cache(dataset: str | None = None) -> None:
    """
    Clear downloaded data cache.

    Parameters
    ----------
    dataset : str, optional
        Dataset to clear ('m4'). If None, clears entire cache.
    """
    import shutil

    data_home = get_data_home()

    if dataset is None:
        if data_home.exists():
            shutil.rmtree(data_home)
            print(f"Cleared cache: {data_home}")
    elif dataset == "m4":
        m4_dir = data_home / "m4"
        if m4_dir.exists():
            shutil.rmtree(m4_dir)
            print(f"Cleared M4 cache: {m4_dir}")
    else:
        raise ValueError(f"Unknown dataset: {dataset}")

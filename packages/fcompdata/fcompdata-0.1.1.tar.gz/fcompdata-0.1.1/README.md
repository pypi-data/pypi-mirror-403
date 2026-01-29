# fcompdata

Forecasting Competitions Datasets - a Python library for loading M and tourism competitions time series datasets (M1, M3, M4, Tourism) with an interface similar to R's `Mcomp` and `Tcomp` packages.

## Installation

```bash
pip install fcompdata
```

or from github:

```
pip install git+https://github.com/config-i1/fcompdata
```

## Usage

```python
from fcompdata import M1, M3, Tourism

# Access series by 1-based index (R-style)
series = M3[1]
print(series['x'])    # Training data (numpy array)
print(series['xx'])   # Test data (numpy array)
print(series['h'])    # Forecast horizon
print(series['n'])    # Training data length
print(series['type']) # Series type (yearly, quarterly, monthly, other)

# Attribute access also works
print(series.sn)          # Series name
print(series.description) # Series description

# Filter by frequency type
yearly = M3.subset('yearly')
monthly = M1.subset('monthly')

# Iterate over all series
for series in M3:
    print(series.sn, len(series.x))

# Get series count
print(len(M3))  # 3003
```

## M4 Dataset

The M4 competition dataset contains 100,000 time series and is too large to bundle with the package. It must be downloaded separately before use. The data is sourced from the [Monash Time Series Forecasting Repository](https://forecastingdata.org/) hosted on Zenodo.

### Downloading M4 Data

```python
from fcompdata.download import download_m4

# Download all M4 frequencies (~50MB total, saved to ~/.fcompdata/m4/)
download_m4()

# Or download specific frequencies
download_m4('yearly')     # 23,000 series
download_m4('quarterly')  # 24,000 series
download_m4('monthly')    # 48,000 series
download_m4('weekly')     # 359 series
download_m4('daily')      # 4,227 series
download_m4('hourly')     # 414 series
```

The data is downloaded once and cached locally in `~/.fcompdata/m4/`. Subsequent calls will use the cached files.

### Using M4 Data

```python
from fcompdata import M4, load_m4

# Load all M4 series (requires all frequencies to be downloaded)
series = M4[1]

# Load a specific frequency
yearly = load_m4('yearly')
monthly = load_m4('monthly')

# Same interface as other datasets
print(series.x)       # Training data
print(series.xx)      # Test data
print(series.h)       # Forecast horizon
print(series.type)    # 'yearly', 'quarterly', etc.

# Filter and iterate
for s in yearly:
    print(s.sn, len(s.x))
```

### M4 Download Sources

The M4 data files are downloaded from the Monash Time Series Forecasting Repository on Zenodo:

| Frequency | Zenodo Record | Horizon |
|-----------|---------------|---------|
| Yearly    | [zenodo.org/record/4656379](https://zenodo.org/record/4656379) | 6 |
| Quarterly | [zenodo.org/record/4656410](https://zenodo.org/record/4656410) | 8 |
| Monthly   | [zenodo.org/record/4656480](https://zenodo.org/record/4656480) | 18 |
| Weekly    | [zenodo.org/record/4656522](https://zenodo.org/record/4656522) | 13 |
| Daily     | [zenodo.org/record/4656548](https://zenodo.org/record/4656548) | 14 |
| Hourly    | [zenodo.org/record/4656589](https://zenodo.org/record/4656589) | 48 |

### Cache Management

```python
from fcompdata.download import clear_cache, get_m4_path

# Check if a frequency is downloaded
path = get_m4_path('yearly')  # Returns Path or None

# Clear all downloaded data
clear_cache()

# Clear only M4 data
clear_cache('m4')
```

## Datasets

### Bundled Datasets

These datasets are included with the package and available immediately:

| Dataset | Series | Yearly | Quarterly | Monthly | Other |
|---------|--------|--------|-----------|---------|-------|
| M1      | 1,001  | 181    | 203       | 617     | -     |
| M3      | 3,003  | 645    | 756       | 1,428   | 174   |
| Tourism | 1,311  | 518    | 427       | 366     | -     |

### Downloadable Datasets

These datasets require downloading before use:

| Dataset | Series  | Yearly | Quarterly | Monthly | Weekly | Daily | Hourly |
|---------|---------|--------|-----------|---------|--------|-------|--------|
| M4      | 100,000 | 23,000 | 24,000    | 48,000  | 359    | 4,227 | 414    |

## Series Attributes

Each `MCompSeries` object has the following attributes:

| Attribute     | Type         | Description                              |
|---------------|--------------|------------------------------------------|
| `sn`          | str          | Series name/identifier                   |
| `x`           | numpy.ndarray| Training data (in-sample)                |
| `xx`          | numpy.ndarray| Test data (out-of-sample)                |
| `h`           | int          | Forecast horizon                         |
| `n`           | int          | Length of training data                  |
| `period`      | int          | Seasonal period (1, 4, or 12)            |
| `type`        | str          | Series type (yearly/quarterly/monthly/other) |
| `description` | str          | Series description                       |

## Data Sources

The time series data in this package was imported from the following sources:

- **Mcomp** (M1 and M3 data): Hyndman, R.J. (2024). *Mcomp: Data from the M-Competitions*. R package. [CRAN](https://cran.r-project.org/package=Mcomp), [GitHub](https://github.com/robjhyndman/Mcomp)
- **Tcomp** (Tourism data): Hyndman, R.J. (2016). *Tcomp: Data from the 2010 Tourism Forecasting Competition*. R package. [CRAN](https://cran.r-project.org/package=Tcomp), [GitHub](https://github.com/ellisp/Tcomp-r-package)
- **Monash Time Series Forecasting Repository** (M4 data): [forecastingdata.org](https://forecastingdata.org/), hosted on [Zenodo](https://zenodo.org/communities/forecasting)

## References

The datasets were used in the following forecasting competitions:

**M1 Competition:**
> Makridakis, S., Andersen, A., Carbone, R., Fildes, R., Hibon, M., Lewandowski, R., Newton, J., Parzen, E., & Winkler, R. (1982). The accuracy of extrapolation (time series) methods: Results of a forecasting competition. *Journal of Forecasting*, 1(2), 111–153. [doi:10.1002/for.3980010202](https://doi.org/10.1002/for.3980010202)

**M3 Competition:**
> Makridakis, S., & Hibon, M. (2000). The M3-Competition: Results, conclusions and implications. *International Journal of Forecasting*, 16(4), 451–476. [doi:10.1016/S0169-2070(00)00057-1](https://doi.org/10.1016/S0169-2070(00)00057-1)

**M4 Competition:**
> Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). The M4 Competition: 100,000 time series and 61 forecasting methods. *International Journal of Forecasting*, 36(1), 54–74. [doi:10.1016/j.ijforecast.2019.04.014](https://doi.org/10.1016/j.ijforecast.2019.04.014)

**Tourism Forecasting Competition:**
> Athanasopoulos, G., Hyndman, R.J., Song, H., & Wu, D.C. (2011). The tourism forecasting competition. *International Journal of Forecasting*, 27(3), 822–844. [doi:10.1016/j.ijforecast.2010.11.005](https://doi.org/10.1016/j.ijforecast.2010.11.005)

**Monash Time Series Forecasting Archive:**
> Godahewa, R., Bergmeir, C., Webb, G.I., Hyndman, R.J., & Montero-Manso, P. (2021). Monash Time Series Forecasting Archive. *Proceedings of the Neural Information Processing Systems Track on Datasets and Benchmarks* (NeurIPS Datasets and Benchmarks 2021). [arXiv:2105.06643](https://arxiv.org/abs/2105.06643)

## License

LGPL-3.0-or-later

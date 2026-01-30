[![PyPI version fury.io](https://badge.fury.io/py/pyregeon.svg)](https://pypi.python.org/pypi/pyregeon/)
[![Documentation Status](https://readthedocs.org/projects/pyregeon/badge/?version=latest)](https://pyregeon.readthedocs.io/en/latest/?badge=latest)
[![CI/CD](https://github.com/martibosch/pyregeon/actions/workflows/tests.yml/badge.svg)](https://github.com/martibosch/pyregeon/blob/main/.github/workflows/tests.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/martibosch/pyregeon/main.svg)](https://results.pre-commit.ci/latest/github/martibosch/pyregeon/main)
[![codecov](https://codecov.io/gh/martibosch/pyregeon/branch/main/graph/badge.svg?token=hKoSSRn58a)](https://codecov.io/gh/martibosch/pyregeon)
[![GitHub license](https://img.shields.io/github/license/martibosch/pyregeon.svg)](https://github.com/martibosch/pyregeon/blob/main/LICENSE)

# pyregeon

Reusable Python utilities to work with geospatial regions.

> *pyregeon* stands for Python Region Geospatial utilities

## Usage

The main idea of pyregeon is to make it as easy as possible to associate any Python object to a geospatial region. The first approach is with the object-oriented `RegionMixin`. We can set the `region` [property attribute](https://docs.python.org/3/library/functions.html#property) to any object that inherits from `RegionMixin`, e.g.:

```python
from pyregeon import RegionMixin


class MyAnalysisCase(..., RegionMixin):
    # optionally define a `crs` or `CRS` attribute
    pass


analysis = MyAnalysisCase(...)
analysis.region = "Lausanne, Switzerland"
```

The `region` [property setter](https://docs.python.org/3/library/functions.html#property.setter) accepts the following values:

- A string with a place name (Nominatim query) to geocode (requires [osmnx](https://github.com/gboeing/osmnx)).
- A sequence with the west, south, east and north bounds.
- A geometric object, e.g., shapely geometry, or a sequence of geometric objects (polygon or multi-polygon). In such a case, the value is passed as the `data` argument of the GeoSeries constructor, and needs to be in the same CRS as the one provided through the `crs` argument.
- A geopandas geo-series or geo-data frame.
- A filename or URL, a file-like object opened in binary ('rb') mode, or a Path object that will be passed to `geopandas.read_file`.

Then, the processed `region` attribute can be accessed as a geo-data frame:

```python
analysis.region
```

<div>
<!-- see https://github.com/hukkin/mdformat/issues/53 -->
<!-- <style scoped> -->
<!--     .dataframe tbody tr th:only-of-type { -->
<!--         vertical-align: middle; -->
<!--     } -->

<!-- 	.dataframe tbody tr th { -->

<!-- 		vertical-align: top; -->

<!-- 	} -->

<!-- 	.dataframe thead th { -->

<!-- 		text-align: right; -->

<!-- 	} -->

<!-- </style> -->

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>geometry</th>
      <th>bbox_west</th>
      <th>bbox_south</th>
      <th>bbox_east</th>
      <th>bbox_north</th>
      <th>place_id</th>
      <th>osm_type</th>
      <th>osm_id</th>
      <th>lat</th>
      <th>lon</th>
      <th>class</th>
      <th>type</th>
      <th>place_rank</th>
      <th>importance</th>
      <th>addresstype</th>
      <th>name</th>
      <th>display_name</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>MULTIPOLYGON (((6.58387 46.55187, 6.58632 46.5...</td>
      <td>6.583868</td>
      <td>46.454873</td>
      <td>6.720814</td>
      <td>46.602577</td>
      <td>83952532</td>
      <td>relation</td>
      <td>1685018</td>
      <td>46.521827</td>
      <td>6.632702</td>
      <td>boundary</td>
      <td>administrative</td>
      <td>16</td>
      <td>0.6941</td>
      <td>city</td>
      <td>Lausanne</td>
      <td>Lausanne, District de Lausanne, Vaud, Switzerland</td>
    </tr>
  </tbody>
</table>
</div>

Note that *when setting `region` to a naive geometry*, i.e, without associated coordinate reference system (CRS), the setter will try to retrieve a CRS by looking whether the object has a `crs` or `CRS` attribute (in that order). In absence of these, a `ValueError` will be raised.

With the `region` attribute properly set, we can also generate regular grids using the `generate_regular_grid_gser` method:

```python
import contextily as cx

res = 0.05
ax = analysis.generate_regular_grid_gser(res).plot(alpha=0.5, edgecolor="black")
cx.add_basemap(ax, crs=analysis.region.crs, attribution=False)
```

![lausanne-grid](https://github.com/martibosch/pyregeon/raw/main/figures/lausanne-grid.png)

Alternatively, it is possible to use [the standalone `pyregeon.generate_regular_grid_gser` function](https://pyregeon.readthedocs.io/en/latest/api.html#pyregeon.generate_regular_grid_gser) without any class by prepending a geo-series with the region as first positional argument (and optionally providing the `crs` keyword argument if the provided geo-series is naive).

See the [API documentation](https://pyregeon.readthedocs.io/en/latest/api.html) for more details or the [multiurbanpy](https://github.com/martibosch/multiurbanpy) library for an example use case of pyregeon.

## Installation

```bash
pip install pyregeon
```

## Acknowledgements

- This package was created with the [martibosch/cookiecutter-geopy-package](https://github.com/martibosch/cookiecutter-geopy-package) project template.

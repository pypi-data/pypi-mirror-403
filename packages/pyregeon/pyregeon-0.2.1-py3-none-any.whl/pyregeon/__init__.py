"""Reusable Python region geospatial utilities."""

import os
from collections.abc import Sequence
from typing import IO

import geopandas as gpd
import numpy as np
import pandas as pd
from pyogrio.errors import DataSourceError
from pyproj.crs import CRS
from shapely import geometry

from pyregeon import settings

try:
    import osmnx as ox
except ImportError:
    ox = None

__all__ = ["generate_regular_grid_gser", "RegionMixin"]

CRSType = str | dict | CRS
RegionGeometryType = geometry.Polygon | geometry.MultiPolygon
RegionType = (
    str
    | Sequence
    | RegionGeometryType
    | gpd.GeoSeries
    | gpd.GeoDataFrame
    | os.PathLike
    | IO
)

_generate_regular_grid_gser_doc = """
Get a regular grid within a region.

Parameters
----------%s
res : float or tuple of floats.
    The grid resolution in units of the region's CRS. A scalar value will be interpreted
    as the same resolution in both x and y directions, whereas a tuple will be
    interpreted as the resolution in the x and y directions, respectively.
crs : CRS-like, optional
    The CRS of the grid, required if the region is a naive geometry (without a CRS set),
    ignored otherwise.
offset : {"center", "top-left"}, optional
    If set to "center" and the region dimensions and target resolution do not divide
    evenly, the grid is offsetted so that the region bounds are in the center of the
    grid. If set to "top-left", the grid starts at the top-left corner of the region.
    If None, the default value set in `settings.GRID_OFFSET` will be used. Ignored if
    the region dimensions and the desired resolution divide evenly.
geometry_type : {"point", "polygon"}, optional
    The type of geometry to return. If "point", the grid will be returned as a GeoSeries
    of points. If "polygon", the grid will be returned as a GeoSeries of polygons. If
    None, the default value set in `settings.GRID_GEOMETRY_TYPE` will be used.
grid_index_name : str, optional
    The name of the index of the grid GeoSeries. If None, the default value set in
    `settings.GRID_INDEX_NAME` will be used.

Returns
-------
grid_gser: gpd.GeoSeries
    A geo-series representing the generated grid.
"""


def generate_regular_grid_gser(  # noqa: D103
    region_gser: gpd.GeoSeries,
    res: float | tuple[float, float],
    *,
    crs: CRSType | None = None,
    offset: str | None = None,
    geometry_type: str | None = None,
    grid_index_name: str | None = None,
) -> gpd.GeoSeries:
    # TODO: DRY crs processing with `_process_region_arg`?
    # we cannot use the `getattr` default because the crs attribute may actually be set,
    # but to None
    # _crs = getattr(region_gser, "crs", crs)
    _crs = getattr(region_gser, "crs")
    if _crs is None:
        if crs is None:
            raise ValueError("If providing a naive geometry, the CRS must be provided.")
    else:
        # ignore the crs provided by the user if the region is a GeoSeries with a crs
        crs = _crs

    if isinstance(res, tuple):
        res_x, res_y = res
    else:
        res_x = res_y = res

    if geometry_type is None:
        geometry_type = settings.GRID_GEOMETRY_TYPE
    if geometry_type == "point":

        def _grid_from_flat_xy(flat_grid_x, flat_grid_y, region_geom):
            grid_gser = gpd.GeoSeries(
                gpd.points_from_xy(flat_grid_x, flat_grid_y), crs=crs
            )
            # filter out points that are outside the region extent
            return grid_gser[grid_gser.within(region_geom)]
    elif geometry_type == "polygon":

        def _grid_from_flat_xy(flat_grid_x, flat_grid_y, region_geom):
            grid_gser = gpd.GeoSeries(
                pd.DataFrame(
                    {
                        "xmin": flat_grid_x,
                        "ymin": flat_grid_y - res_y,
                        "xmax": flat_grid_x + res_x,
                        "ymax": flat_grid_y,
                    }
                ).apply(lambda row: geometry.box(*row), axis="columns"),
                crs=crs,
            )
            # filter out boxes that do not intersect with the region extent
            return grid_gser[grid_gser.intersects(region_geom)]

    # define the function here so that the `crs`, `res_x` and `res_y` are available.
    def _grid_from_geom(region_geom):
        left = region_geom.bounds[0]

        top = region_geom.bounds[3]
        width = region_geom.bounds[2] - left
        height = top - region_geom.bounds[1]
        num_cols = int(np.ceil(width / res_x))
        num_rows = int(np.ceil(height / res_y))
        # once we have the number of zone rows/columns and the zone width/height, we can
        # compute the grid
        if offset == "center":
            # center the grid on the raster bounds
            left = left - (num_cols * res_x - width) / 2
            top = top + (num_rows * res_y - height) / 2

        # generate a grid of size using numpy meshgrid
        grid_x, grid_y = np.meshgrid(
            np.arange(num_cols) * res_x + left,
            top - np.arange(num_rows) * res_y,
            indexing="xy",
        )

        # vectorize the grid as a geo series
        return _grid_from_flat_xy(grid_x.flatten(), grid_y.flatten(), region_geom)

    # TODO: set series name too?
    if grid_index_name is None:
        grid_index_name = settings.GRID_INDEX_NAME
    return pd.concat(
        [_grid_from_geom(region_geom) for region_geom in region_gser], ignore_index=True
    ).rename_axis(grid_index_name)


region_arg = "\nregion : region-like\n    The region for which to generate the grid."
generate_regular_grid_gser.__doc__ = _generate_regular_grid_gser_doc % region_arg


class RegionMixin:
    """Mixin class to add a `region` attribute to a class.

    The `region` property setter accepts the following values:

    - A string with a place name (Nominatim query) to geocode (requires osmnx).
    - A sequence with the west, south, east and north bounds.
    - A geometric object, e.g., shapely geometry, or a sequence of geometric objects
      (polygon or multi-polygon). In such a case, the value is passed as the `data`
      argument of the GeoSeries constructor, and needs to be in the same CRS as the one
      provided through the `crs` argument.
    - A geopandas geo-series or geo-data frame.
    - A filename or URL, a file-like object opened in binary ('rb') mode, or a Path
      object that will be passed to `geopandas.read_file`.
    """

    @property
    def region(self) -> gpd.GeoDataFrame | None:
        """The region as a GeoDataFrame."""
        return self._region

    @region.setter
    def region(
        self,
        region: RegionType,
    ):
        self._region = self._process_region_arg(
            region, crs=getattr(self, "crs", getattr(self, "CRS", None))
        )

    @staticmethod
    def _process_region_arg(
        region: RegionType,
        *,
        crs: CRSType | None = None,
        **geocode_to_gdf_kwargs,
    ) -> gpd.GeoDataFrame | None:
        """Process the region argument.

        Parameters
        ----------
        region : str, Sequence, GeoSeries, GeoDataFrame, PathLike, or IO
            The region to process. This can be either:
            -  A string with a place name (Nominatim query) to geocode.
            -  A sequence with the west, south, east and north bounds. In such a case,
               a CRS must be provided.
            -  A geometric object, e.g., shapely geometry, or a sequence of geometric
               objects (polygon or multi-polygon). In such a case, the value is passed
               as the `data` argument of the GeoSeries constructor, and needs to be in
               the same CRS as the one provided through the `crs` argument.
            -  A geopandas geo-series or geo-data frame.
            -  A filename or URL, a file-like object opened in binary ('rb') mode, or a
               Path object that will be passed to `geopandas.read_file`.
        crs : str, dict or pyproj.CRS, optional
            The coordinate reference system (CRS) of the provided region. It can be any
            CRS-like object accepted by geopandas. Ignored if `region` is a string
            corresponding to a place name, a geopandas geo-series or geo-data frame with
            its CRS attribute set or a filename, URL or file-like object.
        geocode_to_gdf_kwargs : dict, optional
            Keyword arguments to pass to `geocode_to_gdf` if `region` is a string
            corresponding to a place name (Nominatim query).

        Returns
        -------
        gdf : GeoDataFrame
            The processed region as a GeoDataFrame, in the CRS used by the client's
            class. A value of None is returned when passing a place name (Nominatim
            query) but osmnx is not installed.
        """
        if isinstance(region, gpd.GeoSeries):
            # convert it to a GeoDataFrame
            region = gpd.GeoDataFrame(geometry=region)
        if isinstance(region, gpd.GeoDataFrame):
            # TODO: DRY crs processing with `generate_regular_grid_gser`?
            # we cannot use the `getattr` default because the crs attribute may actually
            # be set, but to None
            # _crs = getattr(region, "crs", crs)
            _crs = getattr(region, "crs")
            if _crs is None:
                if crs is None:
                    # there is no way to infer a CRS and we need to raise an error
                    raise ValueError(
                        "The `region` argument must have a `crs` attribute or a CRS "
                        "must be provided explicitly."
                    )
                else:
                    # set the CRS to the one provided
                    # there is no need to set `allow_override` to True here, because we
                    # are certainly dealing with a naive geo-data frame
                    return region.set_crs(crs)
            else:
                # there is no need to do anything
                return region

        # here we can already discard geo-series and geo-data frames
        if isinstance(region, RegionGeometryType):
            # if region is a polygon or multi-polygon, convert it to list to enter the
            # `if` statement below
            region = [region]
        if hasattr(region, "__iter__") and not isinstance(region, str):
            # if region is a sequence (other than a string)
            # use the hasattr to avoid AttributeError when region is a BaseGeometry
            if hasattr(region, "__len__"):
                if len(region) == 4 and isinstance(region[0], (int, float)):
                    # if region is a sequence of 4 numbers, assume it's a bounding
                    # box
                    region = [geometry.box(*region)]
            # otherwise, assume it's a sequence of geometries that can be passed as the
            # `data` argument of the `GeoDataFrame` constructor
            if crs is None:
                raise ValueError(
                    "The `region` argument must have a `crs` attribute or a CRS "
                    "must be provided explicitly."
                )
            region = gpd.GeoDataFrame(geometry=region, crs=crs)
        else:
            # at this point, we assume that this is either file-like or a Nominatim
            # query
            try:
                region = gpd.read_file(region)
            except (DataSourceError, AttributeError):
                #             if ox is None:
                #                 lg.warning(
                #                     """
                # Using a Nominatim query as `region` argument requires osmnx.
                # You can install it using conda or pip.
                # """
                #                 )
                #                 return

                if geocode_to_gdf_kwargs is None:
                    geocode_to_gdf_kwargs = {}
                try:
                    region = ox.geocode_to_gdf(region, **geocode_to_gdf_kwargs).iloc[:1]
                except AttributeError:
                    raise ValueError(
                        "Passing a Nominatim query as the `region` argument requires "
                        "the osmnx package."
                    )

            # if a CRS has been provided, set it (instead of OSM default)
            if crs is not None:
                region = region.to_crs(crs)
        return region

    def generate_regular_grid_gser(  # noqa: D102
        self,
        res: float | tuple[float, float],
        *,
        offset: str | None = None,
        geometry_type: str | None = None,
        grid_index_name: str | None = None,
    ) -> gpd.GeoSeries:
        return generate_regular_grid_gser(
            self.region["geometry"],
            res,
            crs=self.region.crs,  # or self.crs, should be the same
            offset=offset,
            geometry_type=geometry_type,
            grid_index_name=grid_index_name,
        )

    generate_regular_grid_gser.__doc__ = _generate_regular_grid_gser_doc % ""

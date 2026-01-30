# -*- coding: utf-8 -*-
"""
Created on Thu Okt 7 13:39:13 2025

This module implements general plotting functions for SIR 3S applications. TODO: AGSN, Time Curves, Network Color Diagram

@author: Jablonski

"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from collections import OrderedDict


import re
from typing import Dict, Tuple, Optional

import logging

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

from sir3stoolkit.core.wrapper import SIR3S_Model

class SIR3S_Model_Plotting(SIR3S_Model):
    
    def plot_pipe_layer(
        self,
        ax=None,
        gdf=None,
        *,
        width_scaling_col: str | None = None,
        color_mixing_col: str | None = None,
        attribute: str | None = None,
        # visual params
        colors=('darkgreen', 'magenta'),
        legend_fmt: str | None = None,
        legend_values: list[float] | None = None,
        # independent norms
        width_vmin: float | None = None,
        width_vmax: float | None = None,
        color_vmin: float | None = None,
        color_vmax: float | None = None,
        # filtering & styling
        query: str | None = None,
        line_width_factor: float = 10.0,
        zorder: float | None = None,
    ):
        """
        Plot line geometries with separate width and color scaling.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axis to plot into. If None, uses current axes (plt.gca()).
        gdf : pandas.DataFrame or geopandas.GeoDataFrame
            Input with a 'geometry' column of shapely LineString/MultiLineString.
        width_scaling_col : str, optional
            Column used to scale line widths (numeric). If None, uses `attribute`
            if provided; otherwise constant width.
        color_mixing_col : str, optional
            Column used to color lines (numeric). If None, uses `attribute`
            if provided; otherwise a constant color.
        attribute : str, optional
            Legacy single column used for both width and color if the specific
            columns are not provided.
        colors : tuple[str, str], optional
            Two colors to build a linear segmented colormap.
        legend_fmt : str, optional
            Legend label format, default: f"{color_col} {{:.4f}}".
        legend_values : list[float], optional
            Explicit legend tick values; default: 5 linear steps.
        width_vmin, width_vmin : float, optional
            Bounds for width normalization; defaults to data min/max.
        color_vmin, color_vmax : float, optional
            Bounds for color normalization; defaults to data min/max.
        query : str, optional
            Pandas query string to filter rows before plotting.
        line_width_factor : float, optional
            Factor applied after width normalization, default 10.0.
        zorder : float, optional
            Z-order for drawing.

        Returns
        -------
        list[matplotlib.patches.Patch] or None
            Legend patches based on the color scaling column; None if constant color.
        """
        logger.info(f"[plot] Plotting pipes (width='{width_scaling_col}', color='{color_mixing_col}', attr='{attribute}')")

        ax = ax or plt.gca()
        if gdf is None or getattr(gdf, 'empty', True) or 'geometry' not in gdf.columns:
            logger.warning("[plot] Pipes: missing data or geometry column.")
            return None

        df = gdf.query(query) if query else gdf
        if df.empty:
            logger.warning("[plot] Pipes: filtered dataframe is empty.")
            return None

        # --- WIDTH SCALING ---
        width_col = width_scaling_col or attribute
        if width_col is not None:
            try:
                a_w = df[width_col].astype(float).to_numpy()
            except Exception as e:
                logger.error(f"[plot] Pipes: width column '{width_col}' not numeric or missing. {e}")
                return None
            vmin_w = float(width_vmin) if width_vmin is not None else float(np.nanmin(a_w))
            vmax_w = float(width_vmax) if width_vmax is not None else float(np.nanmax(a_w))
            if not np.isfinite(vmin_w) or not np.isfinite(vmax_w) or vmin_w == vmax_w:
                vmax_w = vmin_w + 1e-12
            norm_w = plt.Normalize(vmin=vmin_w, vmax=vmax_w)
            widths_full = norm_w(a_w) * float(line_width_factor)
        else:
            widths_full = None  # will use constant width later

        # --- COLOR SCALING ---
        color_col = color_mixing_col or attribute
        cmap = mcolors.LinearSegmentedColormap.from_list('cmap', list(colors), N=256)
        patches = None
        if color_col is not None:
            try:
                a_c = df[color_col].astype(float).to_numpy()
            except Exception as e:
                logger.error(f"[plot] Pipes: color column '{color_col}' not numeric or missing. {e}")
                return None
            vmin_c = float(color_vmin) if color_vmin is not None else float(np.nanmin(a_c))
            vmax_c = float(color_vmax) if color_vmax is not None else float(np.nanmax(a_c))
            if not np.isfinite(vmin_c) or not np.isfinite(vmax_c) or vmin_c == vmax_c:
                vmax_c = vmin_c + 1e-12
            norm_c = plt.Normalize(vmin=vmin_c, vmax=vmax_c)
            colors_full = cmap(norm_c(a_c))
            legend_fmt = legend_fmt or f"{color_col} {{:.4f}}"
            vals = legend_values if legend_values is not None else np.linspace(vmin_c, vmax_c, 5)
            patches = [mpatches.Patch(color=cmap(norm_c(float(v))), label=legend_fmt.format(float(v))) for v in vals]
        else:
            colors_full = None  # will use constant color later

        # --- BUILD SEGMENTS ---
        segs, cols, lw = [], [], []
        count = 0
        for i, geom in enumerate(df['geometry']):
            if geom is None:
                continue
            gt = getattr(geom, 'geom_type', None)
            col = colors_full[i] if colors_full is not None else mcolors.to_rgba(colors[0])
            w = widths_full[i] if widths_full is not None else float(line_width_factor) * 0.5
            if gt == 'LineString':
                segs.append(np.asarray(geom.coords)); cols.append(col); lw.append(w); count += 1
            elif gt == 'MultiLineString':
                for part in getattr(geom, 'geoms', []):
                    segs.append(np.asarray(part.coords)); cols.append(col); lw.append(w); count += 1

        if not segs:
            logger.warning("[plot] Pipes: no line geometries found.")
            return None

        lc = LineCollection(segs, colors=cols, linewidths=lw, zorder=zorder)
        ax.add_collection(lc); ax.autoscale_view()

        logger.info(f"[plot] Pipes: plotted {count} segments.")
        return patches

    def plot_node_layer(
        self,
        ax=None,
        gdf=None,
        *,
        size_scaling_col: str | None = None,
        color_mixing_col: str | None = None,
        attribute: str | None = None,
        # visual params
        colors=('darkgreen', 'magenta'),
        legend_fmt: str | None = None,
        legend_values: list[float] | None = None,
        # independent norms
        size_vmin: float | None = None,
        size_vmax: float | None = None,
        color_vmin: float | None = None,
        color_vmax: float | None = None,
        # filtering & styling
        query: str | None = None,
        marker_style: str = 'o',
        marker_size_factor: float = 1000.0,
        zorder: float | None = None,
    ):
        """
        Plot point nodes with separate size and color scaling.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axis to plot into. If None, uses current axes (plt.gca()).
        gdf : pandas.DataFrame or geopandas.GeoDataFrame
            Input with a 'geometry' column of shapely geometries.
        size_scaling_col : str, optional
            Column used to scale marker sizes (numeric). If None, uses `attribute`
            if provided; otherwise constant size.
        color_mixing_col : str, optional
            Column used to color markers (numeric). If None, uses `attribute`
            if provided; otherwise a constant color.
        attribute : str, optional
            Legacy single column used for both size and color if the specific
            columns are not provided.
        colors : tuple[str, str], optional
            Two colors to build a linear segmented colormap.
        legend_fmt : str, optional
            Legend label format, default: f"{color_col} {{:.4f}}".
        legend_values : list[float], optional
            Explicit legend tick values; default: 5 linear steps.
        size_vmin, size_vmax : float, optional
            Bounds for size normalization; defaults to data min/max.
        color_vmin, color_vmax : float, optional
            Bounds for color normalization; defaults to data min/max.
        query : str, optional
            Pandas query string to filter rows before plotting.
        marker_style : str, optional
            Matplotlib marker style, default 'o'.
        marker_size_factor : float, optional
            Factor applied after size normalization, default 1000.0.
        zorder : float, optional
            Z-order for drawing.

        Returns
        -------
        list[matplotlib.patches.Patch] or None
            Legend patches based on the color scaling column; None if constant color.
        """
        logger.info(f"[plot] Plotting nodes (size='{size_scaling_col}', color='{color_mixing_col}', attr='{attribute}')")

        ax = ax or plt.gca()
        if gdf is None or getattr(gdf, 'empty', True) or 'geometry' not in gdf.columns:
            logger.warning("[plot] Nodes: missing data or geometry column.")
            return None

        df = gdf.query(query) if query else gdf
        if df.empty:
            logger.warning("[plot] Nodes: filtered dataframe is empty.")
            return None

        geoms = df['geometry']
        is_point = geoms.apply(lambda g: getattr(g, 'geom_type', None) == 'Point')
        if not is_point.any():
            logger.warning("[plot] Nodes: no Point geometries found.")
            return None

        # --- SIZE SCALING ---
        size_col = size_scaling_col or attribute
        if size_col is not None:
            try:
                a_size = df.loc[is_point, size_col].astype(float).to_numpy()
            except Exception as e:
                logger.error(f"[plot] Nodes: size column '{size_col}' not numeric or missing. {e}")
                return None
            vmin_s = float(size_vmin) if size_vmin is not None else float(np.nanmin(a_size))
            vmax_s = float(size_vmax) if size_vmax is not None else float(np.nanmax(a_size))
            if not np.isfinite(vmin_s) or not np.isfinite(vmax_s) or vmin_s == vmax_s:
                vmax_s = vmin_s + 1e-12
            norm_s = plt.Normalize(vmin=vmin_s, vmax=vmax_s)
            sizes = norm_s(a_size) * float(marker_size_factor)
        else:
            sizes = np.full(is_point.sum(), float(marker_size_factor) * 0.5)

        # --- COLOR SCALING ---
        color_col = color_mixing_col or attribute
        cmap = mcolors.LinearSegmentedColormap.from_list('cmap', list(colors), N=256)
        patches = None
        if color_col is not None:
            try:
                a_col = df.loc[is_point, color_col].astype(float).to_numpy()
            except Exception as e:
                logger.error(f"[plot] Nodes: color column '{color_col}' not numeric or missing. {e}")
                return None
            vmin_c = float(color_vmin) if color_vmin is not None else float(np.nanmin(a_col))
            vmax_c = float(color_vmax) if color_vmax is not None else float(np.nanmax(a_col))
            if not np.isfinite(vmin_c) or not np.isfinite(vmax_c) or vmin_c == vmax_c:
                vmax_c = vmin_c + 1e-12
            norm_c = plt.Normalize(vmin=vmin_c, vmax=vmax_c)
            colors_arr = cmap(norm_c(a_col))
            # Legend only for color scaling
            legend_fmt = legend_fmt or f"{color_col} {{:.4f}}"
            vals = legend_values if legend_values is not None else np.linspace(vmin_c, vmax_c, 5)
            patches = [mpatches.Patch(color=cmap(norm_c(float(v))), label=legend_fmt.format(float(v))) for v in vals]
        else:
            # Constant color (first color provided)
            colors_arr = np.tile(mcolors.to_rgba(colors[0]), (is_point.sum(), 1))

        # --- PLOT ---
        coords = np.array([(g.x, g.y) for g in geoms[is_point]])
        ax.scatter(coords[:, 0], coords[:, 1], s=sizes, c=colors_arr, marker=marker_style, zorder=zorder)

        logger.info(f"[plot] Nodes: plotted {is_point.sum()} points.")
        return patches


    def plot_time_curves(
        self,
        df: pd.DataFrame,
        start=None,
        end=None,
        properties=None,
        axis_labels=None,
        ylims=None,
        tks_per_property=None,
        y_label_ticks=None,
        y_grid_ticks=None,
        x_label_ticks=None,
        x_grid_ticks=None,
        figsize=(20, 14),
        axis_offset=60,
        linestyles=None,
        legend=True,
        legend_fontsize=8,
        legend_loc="upper left",
        legend_coords=(0.67, 0.33),
        legend_in_figure=True,
        missing="skip",
        normalize=str.upper,
        aliases=None,
        title_prefix="",
        show_title=True,
        rotate_xticks=0,
        grid=True,
        grid_style="--",
        grid_alpha=0.3,
        logger=None,
    ):
        """
        Plot multiple properties using multiple y-axes (all on the left).
        Optionally restrict which TKs are plotted for each property.

        Legend labels are "PROPERTY NAME".

        Tick/grid separation:
        - Labeled ticks come from major ticks (x_label_ticks, y_label_ticks)
        - Grid lines come from minor ticks (x_grid_ticks, y_grid_ticks)
        - Horizontal grid is based on the first y-axis (axis 0)

        :param df: Input DataFrame with MultiIndex columns (from s3s.generate_element_results_dataframe()). Level 0 must represent TK/group; last level must represent property.
                A column level named "name" is used for legend labels if present.
        :type df: pandas.DataFrame
        :param start: Start timestamp (inclusive) for slicing and x-axis limits. If None, uses first timestamp in df.
        :type start: Any
        :param end: End timestamp (inclusive) for slicing and x-axis limits. If None, uses last timestamp in df.
        :type end: Any
        :param properties: List of property names to plot (matched against the last MultiIndex level). If None, plots all properties found.
        :type properties: list[str] | None
        :param axis_labels: List of y-axis labels corresponding to properties. If None, uses "property=<name>".
        :type axis_labels: list[str] | None
        :param ylims: List of y-limits tuples per property axis, e.g. [(0, 12), (0, 40), (0, 60)]. Use None entries to keep autoscale.
        :type ylims: list[tuple[float, float] | None] | None
        :param tks_per_property: List of lists/sets of TKs allowed per property. If an entry is None or empty, all TKs are allowed.
        :type tks_per_property: list[list[str] | set[str] | None] | None
        :param y_label_ticks: Number of labeled y-ticks per axis (one int per property/axis). If None, leaves default tick behavior.
        :type y_label_ticks: list[int] | None
        :param y_grid_ticks: Number of horizontal grid lines (minor y-ticks) based on the first y-axis. If None, no minor y-grid control.
        :type y_grid_ticks: int | None
        :param x_label_ticks: Number of labeled x-ticks (major ticks). If None, uses AutoDateLocator for major ticks.
        :type x_label_ticks: int | None
        :param x_grid_ticks: Number of vertical grid lines (minor x-ticks). If None, no minor x-grid control.
        :type x_grid_ticks: int | None
        :param figsize: Matplotlib figure size.
        :type figsize: tuple[int, int]
        :param axis_offset: Outward offset (in points) between stacked left-side y-axes.
        :type axis_offset: int
        :param linestyles: List of linestyles used per property (cycled if shorter than properties). Default cycles ["-","--",":","-."].
        :type linestyles: list[str] | None
        :param legend: Whether to draw a legend.
        :type legend: bool
        :param legend_fontsize: Legend font size.
        :type legend_fontsize: int | float
        :param legend_loc: Legend location argument passed to matplotlib (e.g. "upper left").
        :type legend_loc: str
        :param legend_coords: Legend anchor coordinates passed as bbox_to_anchor.
        :type legend_coords: tuple[float, float]
        :param legend_in_figure: If True, uses fig.legend(...) (more robust for multiple twinx axes). If False, uses ax0.legend(...).
        :type legend_in_figure: bool
        :param missing: Policy if a requested property yields no plotted lines after filtering: "skip", "warn", or "error".
        :type missing: str
        :param normalize: Function applied to property strings for robust matching (e.g. str.upper).
        :type normalize: callable
        :param aliases: Mapping applied after normalization to unify names (e.g. {"PHI": "PH"}). Keys/values must be normalized form.
        :type aliases: dict[str, str] | None
        :param title_prefix: Optional text prepended to the timeframe title.
        :type title_prefix: str
        :param show_title: If True, sets a title containing the selected timeframe.
        :type show_title: bool
        :param rotate_xticks: Rotation angle (degrees) for x tick labels.
        :type rotate_xticks: int | float
        :param grid: Whether to draw grid lines (on base axis).
        :type grid: bool
        :param grid_style: Line style for grid.
        :type grid_style: str
        :param grid_alpha: Alpha for grid lines.
        :type grid_alpha: float
        :param logger: Optional logger with .info/.warning methods. If provided, logs are prefixed with "[time curves]".
        :type logger: Any
        :return: (fig, axes, used_properties) where axes is a list of axes (one per property), and used_properties are normalized properties used.
        :rtype: tuple[matplotlib.figure.Figure, list[matplotlib.axes.Axes], list[str]]
        """

        # -------------------------------------------------------------------------
        # Logging helpers
        # -------------------------------------------------------------------------
        def _log_info(msg: str) -> None:
            if logger is not None:
                logger.info(f"[time curves] {msg}")

        def _log_warn(msg: str) -> None:
            if logger is not None and hasattr(logger, "warning"):
                logger.warning(f"[time curves] {msg}")
            elif logger is not None:
                logger.info(f"[time curves] {msg}")

        # -------------------------------------------------------------------------
        # Input validation + index normalization
        # -------------------------------------------------------------------------
        if not isinstance(df.columns, pd.MultiIndex):
            raise ValueError("DataFrame must have MultiIndex columns.")

        df = df.copy()

        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                raise ValueError("Index must be convertible to DateTimeIndex.") from e

        # -------------------------------------------------------------------------
        # Time-window slicing and exact x-limits
        # -------------------------------------------------------------------------
        start_ts = pd.to_datetime(start) if start is not None else None
        end_ts = pd.to_datetime(end) if end is not None else None

        if start_ts is not None or end_ts is not None:
            df = df.loc[start_ts:end_ts]

        if df.empty:
            raise ValueError("No data available in the requested start/end window.")

        x_start = start_ts if start_ts is not None else df.index.min()
        x_end = end_ts if end_ts is not None else df.index.max()
        if x_start > x_end:
            raise ValueError("start must be <= end.")

        _log_info(f"Plot window: {x_start} .. {x_end} (rows={len(df)})")

        # -------------------------------------------------------------------------
        # Column level names and property normalization
        # -------------------------------------------------------------------------
        top_level_name = df.columns.names[0] or "TK"
        last_level_name = df.columns.names[-1] or "property"
        index_label = df.index.name or "time"

        def norm_prop(s: str) -> str:
            s2 = normalize(str(s)).strip()
            if aliases:
                s2 = aliases.get(s2, s2)
            return s2

        raw_last = df.columns.get_level_values(-1).astype(str)
        df_last_norm = raw_last.map(norm_prop)

        if properties is None:
            used_properties = sorted(set(df_last_norm))
        else:
            used_properties = [norm_prop(p) for p in properties]

        n_props = len(used_properties)
        if n_props == 0:
            raise ValueError("No properties to plot.")

        # -------------------------------------------------------------------------
        # Axis labels and limits
        # -------------------------------------------------------------------------
        if axis_labels is None:
            used_axis_labels = [f"{last_level_name}={p}" for p in used_properties]
        else:
            if len(axis_labels) != n_props:
                raise ValueError("axis_labels must have same length as properties.")
            used_axis_labels = list(axis_labels)

        if ylims is not None:
            if len(ylims) != n_props:
                raise ValueError("ylims must have same length as properties (or be None).")
            for lim in ylims:
                if lim is not None and (not isinstance(lim, (tuple, list)) or len(lim) != 2):
                    raise ValueError("Each ylims entry must be (ymin, ymax) or None.")

        # -------------------------------------------------------------------------
        # Per-property TK allow-lists
        # -------------------------------------------------------------------------
        if tks_per_property is not None:
            if len(tks_per_property) != n_props:
                raise ValueError("tks_per_property must have same length as properties (or be None).")
            allowed_tks_sets = []
            for allow in tks_per_property:
                if allow is None:
                    allowed_tks_sets.append(None)
                else:
                    allow_list = [str(x).strip() for x in allow]
                    allowed_tks_sets.append(set(allow_list) if len(allow_list) > 0 else None)
        else:
            allowed_tks_sets = [None] * n_props

        # -------------------------------------------------------------------------
        # Tick parameters validation
        # -------------------------------------------------------------------------
        if y_label_ticks is not None:
            if len(y_label_ticks) != n_props:
                raise ValueError("y_label_ticks must have same length as properties (or be None).")
            if any((not isinstance(n, int) or n < 2) for n in y_label_ticks):
                raise ValueError("Each y_label_ticks entry must be an int >= 2.")

        if y_grid_ticks is not None and (not isinstance(y_grid_ticks, int) or y_grid_ticks < 2):
            raise ValueError("y_grid_ticks must be an int >= 2 (or None).")

        if x_label_ticks is not None and (not isinstance(x_label_ticks, int) or x_label_ticks < 2):
            raise ValueError("x_label_ticks must be an int >= 2 (or None).")

        if x_grid_ticks is not None and (not isinstance(x_grid_ticks, int) or x_grid_ticks < 2):
            raise ValueError("x_grid_ticks must be an int >= 2 (or None).")

        # -------------------------------------------------------------------------
        # Line styling per property
        # -------------------------------------------------------------------------
        if linestyles is None:
            linestyles = ["-", "--", ":", "-."]
        prop_linestyle = {p: linestyles[i % len(linestyles)] for i, p in enumerate(used_properties)}

        # -------------------------------------------------------------------------
        # Create figure and stacked left-side y-axes
        # -------------------------------------------------------------------------
        fig, ax0 = plt.subplots(figsize=figsize)
        axes = [ax0]
        for i in range(1, n_props):
            ax = ax0.twinx()
            ax.yaxis.set_label_position("left")
            ax.yaxis.tick_left()
            ax.spines["left"].set_position(("outward", axis_offset * i))
            ax.spines["right"].set_visible(False)
            axes.append(ax)

        # Exact x-limits, no padding, for all axes
        for ax in axes:
            ax.set_xlim(x_start, x_end)
            ax.margins(x=0)
            ax.autoscale(enable=False, axis="x")

        # -------------------------------------------------------------------------
        # X tick formatting (show time for short spans) + label/grid tick placement
        # -------------------------------------------------------------------------
        span = pd.Timestamp(x_end) - pd.Timestamp(x_start)
        if span <= pd.Timedelta("1D"):
            x_fmt = "%H:%M:%S"
        elif span <= pd.Timedelta("7D"):
            x_fmt = "%m-%d %H:%M"
        else:
            x_fmt = "%Y-%m-%d"

        ax0.xaxis.set_major_formatter(mdates.DateFormatter(x_fmt))

        x0_num = mdates.date2num(pd.Timestamp(x_start).to_pydatetime())
        x1_num = mdates.date2num(pd.Timestamp(x_end).to_pydatetime())

        # Major x ticks determine labels
        if x_label_ticks is not None:
            major_xticks = np.linspace(x0_num, x1_num, x_label_ticks)
            ax0.xaxis.set_major_locator(mticker.FixedLocator(major_xticks))
        else:
            locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
            ax0.xaxis.set_major_locator(locator)
            # ensure x_start is labeled
            current = list(ax0.get_xticks())
            ax0.set_xticks(sorted(set(current + [x0_num])))

        # Minor x ticks determine vertical grid lines
        if x_grid_ticks is not None:
            minor_xticks = np.linspace(x0_num, x1_num, x_grid_ticks)
            ax0.xaxis.set_minor_locator(mticker.FixedLocator(minor_xticks))

        if rotate_xticks:
            for lbl in ax0.get_xticklabels():
                lbl.set_rotation(rotate_xticks)
                lbl.set_ha("right")

        # -------------------------------------------------------------------------
        # Determine TK groups (level 0), colors per TK, and find "name" level index
        # -------------------------------------------------------------------------
        lvl0_str = df.columns.get_level_values(0).astype(str).map(str.strip)
        top_groups = lvl0_str.unique().tolist()

        colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
        if not colors:
            colors = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]
        group_color = {g: colors[i % len(colors)] for i, g in enumerate(top_groups)}

        col_names = list(df.columns.names)
        name_level_idx = col_names.index("name") if "name" in col_names else None

        # Strict: each (TK, property) must resolve to exactly one column
        def pick_single_series(frame: pd.DataFrame) -> pd.Series:
            if frame.shape[1] == 1:
                return frame.iloc[:, 0]
            raise ValueError(
                f"Expected exactly 1 column for a given (TK, property), but got {frame.shape[1]}. "
                f"Columns: {list(frame.columns)}"
            )

        # -------------------------------------------------------------------------
        # Plot lines: only if property exists AND TK is allowed for that property
        # Legend label: "PROPERTY NAME" (no TK)
        # -------------------------------------------------------------------------
        all_lines = []
        plotted_any_for_property = {p: False for p in used_properties}

        for prop_idx, prop in enumerate(used_properties):
            ax = axes[prop_idx]
            ls = prop_linestyle[prop]
            allowed_tks = allowed_tks_sets[prop_idx]

            for g in top_groups:
                if allowed_tks is not None and g not in allowed_tks:
                    continue

                mask = (lvl0_str == g) & (df_last_norm == prop)
                cols = df.columns[mask]
                if len(cols) == 0:
                    continue

                series = pick_single_series(df.loc[:, cols])

                # Extract element name from "name" level (fallback to TK if missing)
                if name_level_idx is not None:
                    name_vals = df.columns.get_level_values(name_level_idx)[mask]
                    name_val = str(pd.unique(name_vals)[0]) if len(name_vals) else str(g)
                else:
                    name_val = str(g)

                line_label = f"{prop} {name_val}".strip()

                (ln,) = ax.plot(
                    df.index,
                    series,
                    linestyle=ls,
                    color=group_color[g],
                    label=line_label,
                )

                all_lines.append(ln)
                plotted_any_for_property[prop] = True

            ax.set_ylabel(used_axis_labels[prop_idx])

            if ylims is not None and ylims[prop_idx] is not None:
                ax.set_ylim(*ylims[prop_idx])

        # -------------------------------------------------------------------------
        # Missing property handling (property yields no plotted lines)
        # -------------------------------------------------------------------------
        missing_props = [p for p, ok in plotted_any_for_property.items() if not ok]
        if missing_props:
            msg = f"Requested properties produced no plotted lines (missing or filtered out): {missing_props}"
            if missing == "error":
                raise ValueError(msg)
            elif missing == "warn":
                _log_warn(msg)

        # -------------------------------------------------------------------------
        # Y tick labels per axis (major ticks) and y-grid ticks (minor ticks on axis 0)
        # -------------------------------------------------------------------------
        for prop_idx, ax in enumerate(axes):
            if y_label_ticks is not None:
                y0, y1 = ax.get_ylim()
                major_yticks = np.linspace(y0, y1, y_label_ticks[prop_idx])
                ax.set_yticks(major_yticks)

        if y_grid_ticks is not None:
            y0, y1 = ax0.get_ylim()
            minor_yticks = np.linspace(y0, y1, y_grid_ticks)
            ax0.yaxis.set_minor_locator(mticker.FixedLocator(minor_yticks))

        # -------------------------------------------------------------------------
        # Labels, grid, title, legend
        # -------------------------------------------------------------------------
        ax0.set_xlabel(index_label)
        ax0.set_axisbelow(True)

        if grid:
            ax0.grid(True, which="major", axis="both", linestyle=grid_style, alpha=grid_alpha)
            if x_grid_ticks is not None:
                ax0.grid(True, which="minor", axis="x", linestyle=grid_style, alpha=grid_alpha)
            if y_grid_ticks is not None:
                ax0.grid(True, which="minor", axis="y", linestyle=grid_style, alpha=grid_alpha)

        if show_title:
            s = pd.Timestamp(x_start)
            e = pd.Timestamp(x_end)
            if s.date() == e.date():
                title = f"{title_prefix}{s:%Y-%m-%d}  {s:%H:%M:%S} - {e:%H:%M:%S}"
            else:
                title = f"{title_prefix}{s:%Y-%m-%d %H:%M:%S} - {e:%Y-%m-%d %H:%M:%S}"
            ax0.set_title(title)

        if legend and all_lines:
            # De-duplicate while preserving order (helps when multiple lines would match same label)
            by_label = OrderedDict()
            for ln in all_lines:
                lab = ln.get_label()
                if lab not in by_label:
                    by_label[lab] = ln

            handles = list(by_label.values())
            labels = list(by_label.keys())

            if legend_in_figure:
                fig.legend(handles, labels, loc=legend_loc, bbox_to_anchor=legend_coords, fontsize=legend_fontsize)
            else:
                ax0.legend(handles, labels, loc=legend_loc, bbox_to_anchor=legend_coords, fontsize=legend_fontsize)

        fig.tight_layout()
        _log_info(f"Plotted {len(all_lines)} lines for {n_props} properties.")
        return fig, axes, used_properties

import logging
import seaborn.matrix as sm
import matplotlib.pyplot as plt
import numpy as np
from seaborn.utils import despine, axis_ticklabels_overlap, _draw_figure, relative_luminance

logger = logging.getLogger(__name__)

# Store original methods
_orig_HeatMapper_plot = sm._HeatMapper.plot
_orig_ClusterGrid_plot_matrix = sm.ClusterGrid.plot_matrix
_orig_ClusterGrid_plot_colors = sm.ClusterGrid.plot_colors
_orig_heatmap = sm.heatmap


def _annotate_heatmap(mapper, ax, img):
    """
    Add textual labels with the value in each cell.
    Adapted from seaborn.matrix._HeatMapper._annotate_heatmap to work with AxesImage (imshow).
    """
    height, width = mapper.annot_data.shape
    xpos, ypos = np.meshgrid(np.arange(width) + .5, np.arange(height) + .5)

    data = img.get_array()
    # img.to_rgba returns (rows, cols, 4)
    rgba = img.to_rgba(data, bytes=False)

    for x, y, m, color, val in zip(xpos.flat, ypos.flat,
                                   data.flat, rgba.reshape(-1, 4),
                                   mapper.annot_data.flat):
        if np.ma.is_masked(m):
            continue

        lum = relative_luminance(color)
        text_color = ".15" if lum > .408 else "w"
        annotation = ("{:" + mapper.fmt + "}").format(val)
        text_kwargs = dict(color=text_color, ha="center", va="center")
        text_kwargs.update(mapper.annot_kws)
        ax.text(x, y, annotation, **text_kwargs)


def imshow_plot(self, ax, cax, kws):
    """
    Custom replacement for HeatMapper.plot using imshow for performance.
    """
    # Only use imshow if explicitly enabled for this axis
    if not getattr(ax, '_use_imshow', False):
        return _orig_HeatMapper_plot(self, ax, cax, kws)

    # Remove all the Axes spines
    despine(ax=ax, left=True, bottom=True)

    # setting vmin/vmax in addition to norm is deprecated
    # so avoid setting if norm is set
    if kws.get("norm") is None:
        kws.setdefault("vmin", self.vmin)
        kws.setdefault("vmax", self.vmax)

    # Filter kws for imshow
    # imshow doesn't support linewidths/edgecolor which are added by heatmap
    kws_imshow = kws.copy()
    kws_imshow.pop("linewidths", None)
    kws_imshow.pop("edgecolor", None)

    # Set defaults for imshow
    kws_imshow.setdefault("interpolation", "none")

    # Handle aspect ratio
    if ax.get_aspect() == 'auto':
        kws_imshow.setdefault("aspect", "auto")

    # 1. Extract the data.
    data = self.plot_data

    # 2. Use imshow
    img = ax.imshow(
        data,
        origin='lower',
        extent=[0, data.shape[1], 0, data.shape[0]],
        cmap=self.cmap,
        **kws_imshow
    )

    # 3. Handle the colorbar if it exists
    if self.cbar:
        cb = ax.figure.colorbar(img, cax, ax, **self.cbar_kws)
        cb.outline.set_linewidth(0)
        if kws.get('rasterized', False):
            cb.solids.set_rasterized(True)

    # 4. Set the limits
    ax.set(xlim=(0, self.data.shape[1]), ylim=(0, self.data.shape[0]))

    # Invert the y axis to show the plot in matrix form
    ax.invert_yaxis()

    # Add row and column labels
    if isinstance(self.xticks, str) and self.xticks == "auto":
        xticks, xticklabels = self._auto_ticks(ax, self.xticklabels, 0)
    else:
        xticks, xticklabels = self.xticks, self.xticklabels

    if isinstance(self.yticks, str) and self.yticks == "auto":
        yticks, yticklabels = self._auto_ticks(ax, self.yticklabels, 1)
    else:
        yticks, yticklabels = self.yticks, self.yticklabels

    ax.set(xticks=xticks, yticks=yticks)
    xtl = ax.set_xticklabels(xticklabels)
    ytl = ax.set_yticklabels(yticklabels, rotation="vertical")
    plt.setp(ytl, va="center")

    # Possibly rotate them if they overlap
    _draw_figure(ax.figure)

    if axis_ticklabels_overlap(xtl):
        plt.setp(xtl, rotation="vertical")
    if axis_ticklabels_overlap(ytl):
        plt.setp(ytl, rotation="horizontal")

    # Add the axis labels
    ax.set(xlabel=self.xlabel, ylabel=self.ylabel)

    # Annotate the cells with the formatted values
    if self.annot:
        _annotate_heatmap(self, ax, img)

    return img


def patched_plot_matrix(self, colorbar_kws, xind, yind, **kws):
    """
    Patched version of ClusterGrid.plot_matrix that marks the main heatmap
    axes to use imshow.
    """
    self.ax_heatmap._use_imshow = True
    return _orig_ClusterGrid_plot_matrix(self, colorbar_kws, xind, yind, **kws)


def patched_plot_colors(self, xind, yind, **kws):
    """
    Patched version of ClusterGrid.plot_colors that explicitly disables
    imshow for side color axes.
    """
    if self.ax_row_colors is not None:
        self.ax_row_colors._use_imshow = False
    if self.ax_col_colors is not None:
        self.ax_col_colors._use_imshow = False
    return _orig_ClusterGrid_plot_colors(self, xind, yind, **kws)


def patched_heatmap(data, **kwargs):
    """
    Patched version of sns.heatmap that enables imshow by default.
    """
    ax = kwargs.get("ax") or plt.gca()
    # Enable imshow if not already explicitly set (e.g. by ClusterGrid)
    if getattr(ax, "_use_imshow", None) is None:
        ax._use_imshow = True
    return _orig_heatmap(data, **kwargs)


def apply_patch():
    """Applies the monkey patch to seaborn."""
    if sm._HeatMapper.plot == imshow_plot:
        logger.debug("Seaborn HeatMapper already patched.")
        return

    sm._HeatMapper.plot = imshow_plot
    sm.ClusterGrid.plot_matrix = patched_plot_matrix
    sm.ClusterGrid.plot_colors = patched_plot_colors
    sm.heatmap = patched_heatmap
    logger.info("✅ Seaborn HeatMapper successfully patched with imshow rendering (opt-in via _use_imshow).")

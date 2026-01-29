import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import io
from matplotlib.colors import Normalize, LinearSegmentedColormap

matplotlib.use("Agg")  # Use non-interactive backend

CLOUD_MASK_ALPHA = 0.9
SHADOW_MASK_ALPHA = 0.9


def calculate_class_break_values(
    raster_array: np.ndarray, num_classes: int = 5, decimal_places: int = 4
) -> list[float]:
    valid_data = raster_array[~np.isnan(raster_array)]
    class_break_values = np.percentile(valid_data, np.linspace(0, 100, num_classes + 1))
    return np.round(class_break_values, decimal_places).tolist()


def generate_figure_save_and_show(
    index: np.ndarray, 
    colormap_norm: tuple, 
    show: bool = False,
    cloud_mask: np.ndarray = None,
    shadow_mask: np.ndarray = None
) -> io.BytesIO:
    colormap, norm = colormap_norm

    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)

    # 1. Plot the Vegetation Index
    ax.imshow(index, cmap=colormap, norm=norm, interpolation="nearest")
    
    # 2. Overlay Shadows (Black)
    if shadow_mask is not None:
        # Create a masked array where only shadow pixels are visible
        shadow_overlay = np.ma.masked_where(shadow_mask == 0, shadow_mask)
        # Use a black colormap
        cmap_shadow = matplotlib.colors.ListedColormap(['black'])
        ax.imshow(shadow_overlay, cmap=cmap_shadow, interpolation="nearest", alpha=SHADOW_MASK_ALPHA)

    # 3. Overlay Clouds (White)
    if cloud_mask is not None:
        # Create a masked array where only cloud pixels are visible
        cloud_overlay = np.ma.masked_where(cloud_mask == 0, cloud_mask)
        # Use a white colormap
        cmap_cloud = matplotlib.colors.ListedColormap(['white'])
        ax.imshow(cloud_overlay, cmap=cmap_cloud, interpolation="nearest", alpha=CLOUD_MASK_ALPHA)

    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", pad_inches=0, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)

    if show:
        plt.imshow(index, cmap=colormap, norm=norm)
        plt.show()

    return buf


def generate_figure_save_and_show_5_normalized(
    index: np.ndarray, 
    colormap: LinearSegmentedColormap, 
    show: bool = False,
    cloud_mask: np.ndarray = None,
    shadow_mask: np.ndarray = None
) -> io.BytesIO:
    min_val, max_val = np.nanmin(index), np.nanmax(index)
    norm = Normalize(vmin=min_val, vmax=max_val)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
    
    # 1. Plot the Vegetation Index
    ax.imshow(index, cmap=colormap, norm=norm, interpolation="nearest")
    
    # 2. Overlay Shadows (Black)
    if shadow_mask is not None:
        shadow_overlay = np.ma.masked_where(shadow_mask == 0, shadow_mask)
        cmap_shadow = matplotlib.colors.ListedColormap(['black'])
        ax.imshow(shadow_overlay, cmap=cmap_shadow, interpolation="nearest", alpha=SHADOW_MASK_ALPHA)

    # 3. Overlay Clouds (White)
    if cloud_mask is not None:
        cloud_overlay = np.ma.masked_where(cloud_mask == 0, cloud_mask)
        cmap_cloud = matplotlib.colors.ListedColormap(['white'])
        ax.imshow(cloud_overlay, cmap=cmap_cloud, interpolation="nearest", alpha=CLOUD_MASK_ALPHA)

    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(
        buf, format="png", pad_inches=0, bbox_inches="tight", transparent=True
    )
    plt.close(fig)
    buf.seek(0)

    if show:
        plt.imshow(index, cmap=colormap, norm=norm)
        plt.show()

    return buf

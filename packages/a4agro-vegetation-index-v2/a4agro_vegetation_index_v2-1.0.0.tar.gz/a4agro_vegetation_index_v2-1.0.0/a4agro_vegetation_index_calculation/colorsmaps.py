import numpy as np
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm


def create_colormap(
    colors: list, boundaries: list = None
) -> tuple[LinearSegmentedColormap, BoundaryNorm]:

    colors = np.array(colors) / 255.0
    cmap = LinearSegmentedColormap.from_list("dynamic_clolor", colors)

    if not boundaries:
        boundaries = np.arange(0.00, 1.00, 0.05)

    norm = BoundaryNorm(boundaries, cmap.N, clip=True)

    return cmap, norm


def create_cgi_colormap() -> LinearSegmentedColormap:
    """
    # Summary:
        Define NDWI colors and their positions

    # Colors
        0 %: R:247 , G:252 , B:245
        25 %: R:199 , G:233 , B:192
        50 %: R:116 , G:196 , B:118
        75 %: R:35 , G:139 , B:69
        100 %: R:0 , G:68 , B:27

    # Returns:
        LinearSegmentedColormap: Class for creating a colormap
    """

    cgi_colors = {
        0.0: [247, 252, 245],  # Position 0%
        0.25: [199, 233, 192],  # Position 25%
        0.5: [116, 196, 118],  # Position 50%
        0.75: [35, 139, 69],  # Position 75%
        1.0: [0, 68, 27],  # Position 100%
    }

    # Convert colors to normalized [0, 1] range
    rgb_colors = {pos: np.array(color) / 255.0 for pos, color in cgi_colors.items()}

    # Extract positions and corresponding RGB colors
    positions = sorted(rgb_colors.keys())
    colors = [rgb_colors[pos] for pos in positions]

    # Create a custom colormap
    cmap = LinearSegmentedColormap.from_list(
        "ndwi_colormap", list(zip(positions, colors))
    )

    return cmap

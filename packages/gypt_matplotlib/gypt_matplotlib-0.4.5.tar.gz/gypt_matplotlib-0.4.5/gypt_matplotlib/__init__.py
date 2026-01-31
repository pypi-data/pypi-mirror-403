"""A small addon for matplotlib that can be used for the GYPT."""

__version__ = "0.4.5"
__description__ = __doc__
__license__ = "MIT"
__authors__ = [
    "Keenan Noack <gypt-matplotlib@albertunruh.de>",
]
__repository__ = "https://codeberg.org/AlbertUnruh/gypt-matplotlib/"


# local
from . import constants, context_managers, errors, utils
from .context_managers import au_plot, auto_close, auto_save, auto_save_and_show, auto_show
from .utils import apply_gypt_style, axes_label, tex

__all__ = (
    "au_plot",
    "auto_close",
    "auto_save",
    "auto_save_and_show",
    "auto_show",
    "axes_label",
    "constants",
    "context_managers",
    "errors",
    "tex",
    "utils",
)


# automatically apply the GYPT style
apply_gypt_style()

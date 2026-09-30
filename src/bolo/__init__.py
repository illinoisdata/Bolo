"""BoloPipe: a lightweight registry for verified HuggingFace inference pipelines."""

from ._version import __version__
from .api import list_params, pipeline, fetch_templates

__all__ = [
    "__version__",
    "list_params",
    "pipeline",
    "fetch_templates",
]

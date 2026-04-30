"""BoloPipe: a lightweight registry for verified HuggingFace inference pipelines."""

from ._version import __version__
from .api import list_params, create_a_venv, pipeline, remove_venv, fetch_templates

__all__ = [
    "__version__",
    "list_params",
    "create_a_venv",
    "pipeline",
    "remove_venv",
    "fetch_templates",
]

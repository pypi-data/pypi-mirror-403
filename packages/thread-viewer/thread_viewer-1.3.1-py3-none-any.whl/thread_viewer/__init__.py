from importlib import metadata as _metadata
import importlib
from os import getenv

__all__ = [
    'ThreadRowView',
    'ThreadViewer',
    '__version__']

def __getattr__(name):
    if name == 'ThreadRowView':
        from .thread_viewer import ThreadRowView
        return ThreadRowView
    if name == 'ThreadViewer':
        from .thread_viewer import ThreadViewer
        return ThreadViewer
    # If the requested attribute isn't one of the known top-level symbols,
    # try to lazily import a submodule so
    # attribute lookups such as those used by mocking/patching succeed.
    try:
        return importlib.import_module(f"{__name__}.{name}")
    except Exception:
        raise AttributeError(name)

try:
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError:
    __version__ = '1.3.1'

if getenv('DEV'):
    __version__ = f'{__version__}+dev'

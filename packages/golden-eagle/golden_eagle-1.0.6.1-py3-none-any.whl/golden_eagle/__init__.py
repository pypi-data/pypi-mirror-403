from importlib.metadata import version

from .main import compare_before_after
from .main import security
from .main import recognition

# function call
__all__ = ['compare_before_after', 'security', 'recognition']

# version
__version__ = version(__package__)

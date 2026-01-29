from importlib.metadata import version

from .main import compare_before_after
from .main import security

# function call
__all__ = ['compare_before_after', 'security']

# version
__version__ = version(__package__)

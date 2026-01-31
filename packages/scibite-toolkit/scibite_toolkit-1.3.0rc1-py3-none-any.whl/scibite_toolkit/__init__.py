# __init__.py

# Submodules available for import:
#   from scibite_toolkit import termite7
#   client = termite7.Termite7RequestBuilder()
#
# Or import classes directly:
#   from scibite_toolkit.termite7 import Termite7RequestBuilder
#   client = Termite7RequestBuilder()

from . import centree_clients
from . import exceptions
from . import workbench
from . import termite
from . import termite7
from . import scibite_search
from . import utilities

# Package metadata
from .__version__ import __version__, __author__, __copyright__, __license__, __email__

def toolkit_version():
    return f"SciBite-Toolkit {__version__}\n Author: {__author__}\n Copyright: {__copyright__}\n License: {__license__}"
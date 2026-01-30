"""
Module to edit, load, and save following the `NXtomo application definition <https://manual.nexusformat.org/classes/applications/NXtomo.html>`_.
"""

from nxtomo.version import version as __version__  # noqa F401

from .application.nxtomo import NXtomo  # noqa F401

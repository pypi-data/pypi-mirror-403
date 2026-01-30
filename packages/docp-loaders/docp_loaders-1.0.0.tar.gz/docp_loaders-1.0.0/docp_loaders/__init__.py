#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the project initilisation logic.

:Platform:  Linux/Windows | Python 3.10+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

# Bring entry-points to the surface.
try:
    from ._version import __version__
    from .loaders.chromapdfloader import ChromaPDFLoader
    from .loaders.chromapptxloader import ChromaPPTXLoader
except ImportError as err:
    from docp_loaders._version import __version__
    from docp_loaders.loaders.chromapdfloader import ChromaPDFLoader
    from docp_loaders.loaders.chromapptxloader import ChromaPPTXLoader


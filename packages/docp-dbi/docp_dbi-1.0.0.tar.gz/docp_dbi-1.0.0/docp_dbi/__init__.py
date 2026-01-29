#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the project initilisation logic.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  n/a

"""

# locals
try:
    from .databases.chroma import ChromaDB 
    from ._version import __version__
except ImportError:
    from docp_dbi.databases.chroma import ChromaDB 
    from docp_dbi._version import __version__


"""
fmus_vox.api - RESTful API server for fmus-vox

This module provides a FastAPI-based REST API for interacting with fmus-vox
functionality over HTTP.
"""

from fmus_vox.api.app import app, serve

__all__ = ["app", "serve"]

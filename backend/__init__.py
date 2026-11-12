"""Backend package initialization."""
from .flask_app import create_app
from .config import Config

__all__ = ["create_app", "Config"]


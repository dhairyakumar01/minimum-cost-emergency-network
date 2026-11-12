"""Route blueprints package initialization."""
from .health import health_bp
from .facilities import facilities_bp
from .network import network_bp
from .scenarios_bp import scenarios_bp

__all__ = ["health_bp", "facilities_bp", "network_bp", "scenarios_bp"]


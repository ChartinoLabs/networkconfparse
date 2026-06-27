"""networkconfparse: parse hierarchical network device configs into a tree."""

from .config import Config
from .node import ConfigNode
from .parser import ConfigSource, parse

__all__ = ["Config", "ConfigNode", "ConfigSource", "parse"]

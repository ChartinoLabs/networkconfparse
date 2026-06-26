"""networkconfparse: parse hierarchical network device configs into a tree."""

from .node import ConfigNode
from .parser import parse

__all__ = ["ConfigNode", "parse"]

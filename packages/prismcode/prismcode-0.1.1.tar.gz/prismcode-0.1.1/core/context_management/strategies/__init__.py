"""
Memory consolidation strategies for context management.

Strategies determine when and how to compress conversation history
to stay within context budget while preserving important information.

Available strategies:
- RollingGist: Simple rolling compression - compress oldest 20% when hitting budget
- ContextAwareGist: Like RollingGist but consolidator sees agent's working memory
"""

from .base import ConsolidationStrategy, ConsolidationResult
from .rolling_gist import RollingGist
from .context_aware_gist import ContextAwareGist

__all__ = [
    "ConsolidationStrategy",
    "ConsolidationResult",
    "RollingGist",
    "ContextAwareGist",
]

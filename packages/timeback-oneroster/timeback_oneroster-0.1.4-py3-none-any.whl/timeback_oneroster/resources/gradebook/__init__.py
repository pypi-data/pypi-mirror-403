"""
Gradebook Resources
"""

from .categories import CategoriesResource, ScopedCategoryResource
from .line_items import LineItemsResource, ScopedLineItemResource
from .results import ResultsResource, ScopedResultResource
from .score_scales import ScopedScoreScaleResource, ScoreScalesResource

__all__ = [
    "CategoriesResource",
    "LineItemsResource",
    "ResultsResource",
    "ScopedCategoryResource",
    "ScopedLineItemResource",
    "ScopedResultResource",
    "ScopedScoreScaleResource",
    "ScoreScalesResource",
]

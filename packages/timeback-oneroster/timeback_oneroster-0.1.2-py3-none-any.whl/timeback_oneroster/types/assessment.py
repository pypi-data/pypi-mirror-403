"""
OneRoster Assessment Types

Types for assessment entities: assessment line items and results.
"""

from typing import Literal

from pydantic import ConfigDict, Field

from .base import Base, Ref

ScoreStatus = Literal[
    "exempt",
    "fully graded",
    "not submitted",
    "partially graded",
    "submitted",
]


# ═══════════════════════════════════════════════════════════════════════════════
# ASSESSMENT LINE ITEM
# ═══════════════════════════════════════════════════════════════════════════════


class AssessmentLineItem(Base):
    """
    An assessment line item for standardized or formal assessments.

    Assessment line items are similar to line items but designed for
    formal assessments with more detailed tracking capabilities.
    """

    title: str
    description: str | None = None
    class_: Ref | None = Field(default=None, alias="class")
    parent_assessment_line_item: Ref | None = Field(default=None, alias="parentAssessmentLineItem")
    score_scale: Ref | None = Field(default=None, alias="scoreScale")
    result_value_min: float | None = Field(default=None, alias="resultValueMin")
    result_value_max: float | None = Field(default=None, alias="resultValueMax")
    component: Ref | None = None
    component_resource: Ref | None = Field(default=None, alias="componentResource")
    course: Ref | None = None

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ASSESSMENT RESULT
# ═══════════════════════════════════════════════════════════════════════════════


class AssessmentResult(Base):
    """
    A result for an assessment line item.

    Assessment results record scores for formal assessments.
    """

    assessment_line_item: Ref = Field(alias="assessmentLineItem")
    student: Ref
    score: float | None = None
    text_score: str | None = Field(default=None, alias="textScore")
    score_date: str = Field(alias="scoreDate")
    score_scale: Ref | None = Field(default=None, alias="scoreScale")
    score_percentile: float | None = Field(default=None, alias="scorePercentile")
    score_status: ScoreStatus = Field(alias="scoreStatus")
    comment: str | None = None
    in_progress: str | None = Field(default=None, alias="inProgress")
    incomplete: str | None = None
    late: str | None = None
    missing: str | None = None

    model_config = ConfigDict(populate_by_name=True)

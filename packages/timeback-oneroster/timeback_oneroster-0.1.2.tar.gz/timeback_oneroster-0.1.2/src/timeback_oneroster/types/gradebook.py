"""
OneRoster Gradebook Types

Types for gradebook entities: line items, results, categories, score scales.
"""

from typing import Literal

from pydantic import ConfigDict, Field

from .base import Base, RefWithHref

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS / LITERALS
# ═══════════════════════════════════════════════════════════════════════════════

ResultStatus = Literal["exempt", "fully graded", "not submitted", "partially graded", "submitted"]

ScoreStatus = Literal[
    "exempt",
    "fully graded",
    "not submitted",
    "partially graded",
    "submitted",
]


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY
# ═══════════════════════════════════════════════════════════════════════════════


class Category(Base):
    """
    A category for organizing line items (assignments/grades).

    Categories like "Homework", "Tests", "Quizzes" help organize gradebook items.
    """

    title: str


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE SCALE
# ═══════════════════════════════════════════════════════════════════════════════


class ScoreScaleValue(Base):
    """A single value in a score scale (e.g., "A", "B", "Pass")."""

    value: str
    description: str | None = None


class ScoreScale(Base):
    """
    A scale for scoring (e.g., letter grades, pass/fail).

    Score scales define the possible values for results.
    """

    title: str
    description: str | None = None
    score_scale_values: list[ScoreScaleValue] | None = Field(default=None, alias="scoreScaleValues")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LINE ITEM
# ═══════════════════════════════════════════════════════════════════════════════


class LineItem(Base):
    """
    A gradebook line item (assignment, test, quiz, etc.).

    Line items represent gradable activities in a class.
    """

    title: str
    description: str | None = None
    assign_date: str | None = Field(default=None, alias="assignDate")
    due_date: str | None = Field(default=None, alias="dueDate")
    class_: RefWithHref = Field(alias="class")
    school: RefWithHref | None = None
    category: RefWithHref | None = None
    grading_period: RefWithHref | None = Field(default=None, alias="gradingPeriod")
    score_scale: RefWithHref | None = Field(default=None, alias="scoreScale")
    result_value_min: float | None = Field(default=None, alias="resultValueMin")
    result_value_max: float | None = Field(default=None, alias="resultValueMax")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# RESULT
# ═══════════════════════════════════════════════════════════════════════════════


class Result(Base):
    """
    A student's result (grade) for a line item.

    Results link students to line items with their scores.
    """

    line_item: RefWithHref = Field(alias="lineItem")
    student: RefWithHref
    score_status: ScoreStatus | None = Field(default=None, alias="scoreStatus")
    score: float | None = None
    text_score: str | None = Field(default=None, alias="textScore")
    score_date: str | None = Field(default=None, alias="scoreDate")
    comment: str | None = None

    model_config = ConfigDict(populate_by_name=True)

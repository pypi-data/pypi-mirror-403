"""
Categories Resource

Access and manage grade categories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import CategoryCreateInput
from ...types.gradebook import Category
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED CATEGORY RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedCategoryResource:
    """
    Scoped resource for operations on a specific category.

    Access via `client.categories(category_id)`.

    Example:
        ```python
        category = await client.categories(category_id).get()
        ```
    """

    def __init__(self, transport: Transport, category_id: str) -> None:
        self._transport = transport
        self._category_id = category_id
        self._base_path = f"{transport.paths.gradebook}/categories/{category_id}"

    async def get(self) -> Category:
        """Get the category details."""
        response = await self._transport.get(self._base_path)
        return Category(**response["category"])

    async def delete(self) -> None:
        """Delete this category."""
        await self._transport.delete(self._base_path)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORIES RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class CategoriesResource(CRUDResourceNoSearch[Category]):
    """
    Resource for grade categories.

    Categories organize line items (e.g., "Homework", "Tests", "Quizzes").

    Example:
        ```python
        # List all categories
        categories = await client.categories.list()

        # Get specific category
        category = await client.categories.get("category-id")

        # Create a category
        await client.categories.create({
            "title": "Homework",
        })
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "gradebook", "/categories")

    @property
    def _unwrap_key(self) -> str:
        return "categories"

    @property
    def _wrap_key(self) -> str:
        return "category"

    @property
    def _model_class(self) -> type[Category]:
        return Category

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating category create input."""
        return CategoryCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating category update input."""
        return CategoryCreateInput

    def __call__(self, category_id: str) -> ScopedCategoryResource:
        """Get scoped resource for a specific category."""
        return ScopedCategoryResource(self._transport, category_id)

"""Integration tests for example_products services.

These tests verify the service layer logic using mocked database sessions.
For full end-to-end tests with a real database, see the e2e/ directory.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.exceptions import NotFoundError
from features.example_products.schemas import ProductCreate
from features.example_products.services import create_product, get_product


class TestCreateProduct:
    """Integration tests for create_product service."""

    @pytest.mark.asyncio
    async def test_create_product_adds_to_session(self):
        """create_product adds the product to the database session."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # add() is synchronous in SQLAlchemy

        product_data = ProductCreate(
            name="New Product",
            price=Decimal("29.99"),
            sku="NEW-001",
            stock=10,
        )

        result = await create_product(mock_db, product_data)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        assert result.name == "New Product"
        assert result.sku == "NEW-001"

    @pytest.mark.asyncio
    async def test_create_product_uses_provided_values(self):
        """create_product creates a product with all provided values."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # add() is synchronous in SQLAlchemy

        product_data = ProductCreate(
            name="Custom Product",
            description="A custom product",
            price=Decimal("99.99"),
            sku="CUSTOM-001",
            stock=50,
            is_active=False,
        )

        result = await create_product(mock_db, product_data)

        assert result.name == "Custom Product"
        assert result.description == "A custom product"
        assert result.price == Decimal("99.99")
        assert result.stock == 50
        assert result.is_active is False


class TestGetProduct:
    """Integration tests for get_product service."""

    @pytest.mark.asyncio
    async def test_get_product_raises_not_found(self):
        """get_product raises NotFoundError for non-existent product."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundError) as exc_info:
            await get_product(mock_db, product_id=999)

        assert "999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_product_returns_found_product(self):
        """get_product returns the product when found."""
        mock_db = AsyncMock()
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.name = "Found Product"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_product
        mock_db.execute.return_value = mock_result

        result = await get_product(mock_db, product_id=1)

        assert result == mock_product

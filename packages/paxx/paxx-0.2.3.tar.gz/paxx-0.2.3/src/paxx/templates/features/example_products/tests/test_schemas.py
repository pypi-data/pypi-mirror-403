"""Unit tests for example_products schemas.

These tests validate Pydantic schema validation logic without
any database or external dependencies.
"""

from decimal import Decimal

import pytest
from features.example_products.schemas import ProductCreate, ProductUpdate
from pydantic import ValidationError


class TestProductCreateSchema:
    """Unit tests for ProductCreate schema validation."""

    def test_valid_product_create(self):
        """ProductCreate accepts valid data with all required fields."""
        product = ProductCreate(
            name="Test Product",
            price=Decimal("19.99"),
            sku="TEST-001",
        )

        assert product.name == "Test Product"
        assert product.price == Decimal("19.99")
        assert product.sku == "TEST-001"
        assert product.stock == 0  # default
        assert product.is_active is True  # default

    def test_product_create_rejects_negative_price(self):
        """ProductCreate rejects negative prices."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                name="Test Product",
                price=Decimal("-10.00"),
                sku="TEST-002",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("price",) for e in errors)


class TestProductUpdateSchema:
    """Unit tests for ProductUpdate schema validation."""

    def test_product_update_allows_partial_updates(self):
        """ProductUpdate allows updating only specific fields."""
        update = ProductUpdate(name="Updated Name")

        assert update.name == "Updated Name"
        assert update.price is None
        assert update.sku is None

    def test_product_update_rejects_negative_stock(self):
        """ProductUpdate rejects negative stock values."""
        with pytest.raises(ValidationError) as exc_info:
            ProductUpdate(stock=-5)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("stock",) for e in errors)

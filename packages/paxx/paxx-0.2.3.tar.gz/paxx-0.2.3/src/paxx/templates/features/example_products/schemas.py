"""Example Products schemas for request/response validation."""

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Base schema with common product fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., ge=0, decimal_places=2)
    sku: str = Field(..., min_length=1, max_length=100)
    stock: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product. All fields are optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductPublic(ProductBase):
    """Schema for public API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

"""Example Products models."""

from decimal import Decimal

from db.database import BaseModel
from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

__all__ = ["Product"]


class Product(BaseModel):
    """Product model for the example catalog.

    Attributes:
        name: Product name (unique).
        description: Optional product description.
        price: Product price as a decimal (precision 10, scale 2).
        sku: Stock keeping unit (unique identifier).
        stock: Current stock quantity.
        is_active: Whether the product is available for sale.
    """

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    stock: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

"""Example Products business logic."""

import uuid

from core.dependencies import PaginationParams
from core.exceptions import NotFoundError
from features.example_products.models import Product
from features.example_products.schemas import ProductCreate, ProductUpdate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def list_products(
    db: AsyncSession,
    pagination: PaginationParams,
    *,
    active_only: bool = False,
) -> tuple[list[Product], int]:
    """List all products with pagination.

    Args:
        db: Database session.
        pagination: Pagination parameters.
        active_only: If True, only return active products.

    Returns:
        Tuple of (list of products, total count).
    """
    query = select(Product)
    count_query = select(func.count(Product.id))

    if active_only:
        query = query.where(Product.is_active == True)  # noqa: E712
        count_query = count_query.where(Product.is_active == True)  # noqa: E712

    total = await db.scalar(count_query) or 0

    result = await db.execute(
        query.offset(pagination.offset).limit(pagination.limit).order_by(Product.id)
    )
    return list(result.scalars().all()), total


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    """Get a product by ID.

    Args:
        db: Database session.
        product_id: The product ID.

    Returns:
        The product object.

    Raises:
        NotFoundError: If the product is not found.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError(f"Product with id {product_id} not found")
    return product


async def get_product_by_sku(db: AsyncSession, sku: str) -> Product | None:
    """Get a product by SKU.

    Args:
        db: Database session.
        sku: The product SKU.

    Returns:
        The product object or None if not found.
    """
    result = await db.execute(select(Product).where(Product.sku == sku))
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    """Create a new product.

    Args:
        db: Database session.
        data: The product data.

    Returns:
        The created product object.
    """
    product = Product(**data.model_dump())
    db.add(product)
    await db.flush()
    return product


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate
) -> Product:
    """Update an existing product.

    Args:
        db: Database session.
        product_id: The product ID.
        data: The update data.

    Returns:
        The updated product object.

    Raises:
        NotFoundError: If the product is not found.
    """
    product = await get_product(db, product_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.flush()
    return product


async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> None:
    """Delete a product.

    Args:
        db: Database session.
        product_id: The product ID.

    Raises:
        NotFoundError: If the product is not found.
    """
    product = await get_product(db, product_id)
    await db.delete(product)
    await db.flush()

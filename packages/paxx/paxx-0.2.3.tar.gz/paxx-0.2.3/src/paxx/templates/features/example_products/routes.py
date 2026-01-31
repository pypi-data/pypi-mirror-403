"""Example Products API routes."""

import uuid
from typing import Annotated

from core.dependencies import PaginationParams, get_pagination
from core.schemas import ListResponse, PaginationMeta, SuccessResponse
from db.database import get_db
from fastapi import APIRouter, Depends, Query
from features.example_products import services
from features.example_products.schemas import (
    ProductCreate,
    ProductPublic,
    ProductUpdate,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=ListResponse[ProductPublic])
async def list_products(
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: Annotated[
        bool, Query(description="Filter to active products only")
    ] = False,
):
    """List all products with pagination.

    Returns a paginated list of products. Use `active_only=true` to filter
    to only products that are currently active/available.
    """
    items, total = await services.list_products(db, pagination, active_only=active_only)
    return ListResponse(
        items=items,
        meta=PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        ),
    )


@router.get("/{product_id}", response_model=ProductPublic)
async def get_product(
    product_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a product by ID."""
    return await services.get_product(db, product_id)


@router.post("", response_model=ProductPublic, status_code=201)
async def create_product(
    data: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new product.

    The SKU and name must be unique across all products.
    """
    return await services.create_product(db, data)


@router.put("/{product_id}", response_model=ProductPublic)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a product.

    Only the fields provided in the request body will be updated.
    """
    return await services.update_product(db, product_id, data)


@router.delete("/{product_id}", response_model=SuccessResponse)
async def delete_product(
    product_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a product."""
    await services.delete_product(db, product_id)
    return SuccessResponse(message="Product deleted successfully")

# Tutorial: Building a Products Feature

This tutorial walks through creating a complete CRUD feature for managing products.

## Prerequisites

- A paxx project created with `paxx bootstrap`
- Development environment running (`docker compose up` or local setup)

## Step 1: Create the Feature

```bash
uv run paxx feature create products --description "Product catalog management"
```

This creates `features/products/` with all the necessary files.

## Step 2: Define the Model

Edit `features/products/models.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float]
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=datetime.utcnow)
```

## Step 3: Create the Schemas

Edit `features/products/schemas.py`:

```python
from datetime import datetime

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: float = Field(..., gt=0)
    sku: str = Field(..., min_length=1, max_length=50)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = Field(None, gt=0)


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
```

## Step 4: Implement the Services

Edit `features/products/services.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Product
from .schemas import ProductCreate, ProductUpdate


async def get_products(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[Product]:
    result = await db.execute(
        select(Product).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def get_product_by_sku(db: AsyncSession, sku: str) -> Product | None:
    result = await db.execute(
        select(Product).where(Product.sku == sku)
    )
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession,
    product: Product,
    data: ProductUpdate,
) -> Product:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
    await db.commit()
```

## Step 5: Create the Routes

Edit `features/products/routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db

from . import services
from .schemas import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all products."""
    return await services.get_products(db, skip=skip, limit=limit)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new product."""
    existing = await services.get_product_by_sku(db, data.sku)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists",
        )
    return await services.create_product(db, data)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a product by ID."""
    product = await services.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a product."""
    product = await services.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return await services.update_product(db, product, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a product."""
    product = await services.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    await services.delete_product(db, product)
```

## Step 6: Update the Config

Edit `features/products/config.py`:

```python
from dataclasses import dataclass, field


@dataclass
class FeatureConfig:
    prefix: str = "/products"
    tags: list[str] = field(default_factory=lambda: ["Products"])
```

## Step 7: Register the Router

Add to `main.py`:

```python
from features.products.routes import router as products_router
from features.products.config import FeatureConfig as ProductsConfig

def create_app() -> FastAPI:
    app = FastAPI(...)

    # ... existing code ...

    # Register products router
    products_config = ProductsConfig()
    app.include_router(
        products_router,
        prefix=products_config.prefix,
        tags=products_config.tags,
    )

    return app
```

## Step 8: Create and Apply Migrations

```bash
# Create the migration
uv run paxx db migrate "add products table"

# Apply it
uv run paxx db upgrade
```

## Step 9: Test Your API

Start the server:

```bash
uv run paxx start
```

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to test your endpoints:

1. **POST /products/** - Create a product
2. **GET /products/** - List all products
3. **GET /products/{id}** - Get a specific product
4. **PATCH /products/{id}** - Update a product
5. **DELETE /products/{id}** - Delete a product

## Example Requests

### Create a Product

```bash
curl -X POST http://127.0.0.1:8000/products/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "price": 29.99, "sku": "WDG-001"}'
```

### List Products

```bash
curl http://127.0.0.1:8000/products/
```

### Get a Product

```bash
curl http://127.0.0.1:8000/products/1
```

### Update a Product

```bash
curl -X PATCH http://127.0.0.1:8000/products/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 24.99}'
```

### Delete a Product

```bash
curl -X DELETE http://127.0.0.1:8000/products/1
```

## Writing Tests

Create `e2e/test_products.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    response = await client.post(
        "/products/",
        json={"name": "Test Product", "price": 19.99, "sku": "TEST-001"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["sku"] == "TEST-001"


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient):
    # First create a product
    create_response = await client.post(
        "/products/",
        json={"name": "Test Product", "price": 19.99, "sku": "TEST-002"},
    )
    product_id = create_response.json()["id"]

    # Then fetch it
    response = await client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["id"] == product_id


@pytest.mark.asyncio
async def test_product_not_found(client: AsyncClient):
    response = await client.get("/products/99999")
    assert response.status_code == 404
```

Run tests:

```bash
uv run pytest e2e/test_products.py -v
```

## Next Steps

- Add additional [Infrastructure](infrastructure.md) like storage, caching, etc.
- [Extend](extensions.md) exisitng app with websockets support, postGIS and more

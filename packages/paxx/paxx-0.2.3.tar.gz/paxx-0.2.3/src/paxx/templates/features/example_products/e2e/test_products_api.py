"""E2E tests for the Products API.

Tests CRUD operations against a live API server.
"""

import uuid

import httpx
import pytest

# A valid UUID that doesn't exist in the database
NONEXISTENT_UUID = "00000000-0000-0000-0000-000000000000"


def unique_sku() -> str:
    """Generate a unique SKU for test isolation."""
    return f"TEST-{uuid.uuid4().hex[:8].upper()}"


class TestListProducts:
    """Tests for GET /products endpoint."""

    def test_list_products_returns_200(self, client: httpx.Client):
        """List products endpoint should return 200."""
        response = client.get("/products")
        assert response.status_code == 200

    def test_list_products_returns_paginated_response(self, client: httpx.Client):
        """List products should return paginated response structure."""
        response = client.get("/products")
        data = response.json()

        assert "items" in data
        assert "meta" in data
        assert isinstance(data["items"], list)
        assert "page" in data["meta"]
        assert "page_size" in data["meta"]
        assert "total_items" in data["meta"]
        assert "total_pages" in data["meta"]

    def test_list_products_respects_page_size(self, client: httpx.Client):
        """List products should respect page_size parameter."""
        response = client.get("/products", params={"page_size": 5})
        data = response.json()

        assert data["meta"]["page_size"] == 5

    def test_list_products_active_only_filter(self, client: httpx.Client):
        """List products should filter by active_only when specified."""
        response = client.get("/products", params={"active_only": True})
        assert response.status_code == 200

        data = response.json()
        for product in data["items"]:
            assert product["is_active"] is True


class TestCreateProduct:
    """Tests for POST /products endpoint."""

    def test_create_product_returns_201(self, client: httpx.Client):
        """Create product should return 201 status."""
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": "19.99",
            "sku": unique_sku(),
            "stock": 100,
            "is_active": True,
        }

        response = client.post("/products", json=product_data)
        assert response.status_code == 201

        # Cleanup
        product_id = response.json()["id"]
        client.delete(f"/products/{product_id}")

    def test_create_product_returns_created_data(self, client: httpx.Client):
        """Create product should return the created product data."""
        sku = unique_sku()
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": "29.99",
            "sku": sku,
            "stock": 50,
            "is_active": True,
        }

        response = client.post("/products", json=product_data)
        data = response.json()

        assert data["name"] == "Test Product"
        assert data["description"] == "A test product"
        assert data["sku"] == sku
        assert data["stock"] == 50
        assert data["is_active"] is True
        assert "id" in data

        # Cleanup
        client.delete(f"/products/{data['id']}")

    def test_create_product_without_optional_fields(self, client: httpx.Client):
        """Create product should work with only required fields."""
        product_data = {
            "name": "Minimal Product",
            "price": "9.99",
            "sku": unique_sku(),
        }

        response = client.post("/products", json=product_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Minimal Product"
        assert data["stock"] == 0  # default value
        assert data["is_active"] is True  # default value

        # Cleanup
        client.delete(f"/products/{data['id']}")

    def test_create_product_missing_required_field_returns_422(
        self, client: httpx.Client
    ):
        """Create product without required fields should return 422."""
        product_data = {
            "name": "Missing Price Product",
            "sku": unique_sku(),
            # missing price
        }

        response = client.post("/products", json=product_data)
        assert response.status_code == 422


class TestGetProduct:
    """Tests for GET /products/{product_id} endpoint."""

    @pytest.fixture
    def created_product(self, client: httpx.Client):
        """Create a product for testing and cleanup after."""
        product_data = {
            "name": "Get Test Product",
            "description": "Product for get tests",
            "price": "15.00",
            "sku": unique_sku(),
            "stock": 25,
            "is_active": True,
        }
        response = client.post("/products", json=product_data)
        product = response.json()
        yield product
        client.delete(f"/products/{product['id']}")

    def test_get_product_returns_200(
        self, client: httpx.Client, created_product: dict
    ):
        """Get product should return 200 for existing product."""
        response = client.get(f"/products/{created_product['id']}")
        assert response.status_code == 200

    def test_get_product_returns_correct_data(
        self, client: httpx.Client, created_product: dict
    ):
        """Get product should return the correct product data."""
        response = client.get(f"/products/{created_product['id']}")
        data = response.json()

        assert data["id"] == created_product["id"]
        assert data["name"] == created_product["name"]
        assert data["sku"] == created_product["sku"]

    def test_get_nonexistent_product_returns_404(self, client: httpx.Client):
        """Get product should return 404 for non-existent product."""
        response = client.get(f"/products/{NONEXISTENT_UUID}")
        assert response.status_code == 404


class TestUpdateProduct:
    """Tests for PUT /products/{product_id} endpoint."""

    @pytest.fixture
    def product_to_update(self, client: httpx.Client):
        """Create a product for update testing and cleanup after."""
        product_data = {
            "name": "Update Test Product",
            "description": "Product for update tests",
            "price": "20.00",
            "sku": unique_sku(),
            "stock": 30,
            "is_active": True,
        }
        response = client.post("/products", json=product_data)
        product = response.json()
        yield product
        # Try to cleanup (might already be deleted)
        client.delete(f"/products/{product['id']}")

    def test_update_product_returns_200(
        self, client: httpx.Client, product_to_update: dict
    ):
        """Update product should return 200."""
        update_data = {"name": "Updated Product Name"}
        response = client.put(
            f"/products/{product_to_update['id']}", json=update_data
        )
        assert response.status_code == 200

    def test_update_product_changes_data(
        self, client: httpx.Client, product_to_update: dict
    ):
        """Update product should change the specified fields."""
        update_data = {
            "name": "Completely Updated",
            "price": "99.99",
            "stock": 999,
        }
        response = client.put(
            f"/products/{product_to_update['id']}", json=update_data
        )
        data = response.json()

        assert data["name"] == "Completely Updated"
        assert float(data["price"]) == 99.99
        assert data["stock"] == 999
        # Unchanged fields should remain the same
        assert data["sku"] == product_to_update["sku"]

    def test_update_product_partial_update(
        self, client: httpx.Client, product_to_update: dict
    ):
        """Update product should allow partial updates."""
        update_data = {"is_active": False}
        response = client.put(
            f"/products/{product_to_update['id']}", json=update_data
        )
        data = response.json()

        assert data["is_active"] is False
        assert data["name"] == product_to_update["name"]

    def test_update_nonexistent_product_returns_404(self, client: httpx.Client):
        """Update product should return 404 for non-existent product."""
        update_data = {"name": "Nonexistent"}
        response = client.put(f"/products/{NONEXISTENT_UUID}", json=update_data)
        assert response.status_code == 404


class TestDeleteProduct:
    """Tests for DELETE /products/{product_id} endpoint."""

    def test_delete_product_returns_200(self, client: httpx.Client):
        """Delete product should return 200."""
        # First create a product to delete
        product_data = {
            "name": "Product to Delete",
            "price": "10.00",
            "sku": unique_sku(),
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 200

    def test_delete_product_returns_success_message(self, client: httpx.Client):
        """Delete product should return success message."""
        # First create a product to delete
        product_data = {
            "name": "Product to Delete",
            "price": "10.00",
            "sku": unique_sku(),
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/products/{product_id}")
        data = response.json()
        assert data["message"] == "Product deleted successfully"

    def test_delete_product_actually_removes_product(self, client: httpx.Client):
        """Delete product should actually remove the product."""
        # First create a product to delete
        product_data = {
            "name": "Product to Delete",
            "price": "10.00",
            "sku": unique_sku(),
        }
        create_response = client.post("/products", json=product_data)
        product_id = create_response.json()["id"]

        # Delete it
        client.delete(f"/products/{product_id}")

        # Verify it's gone
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_product_returns_404(self, client: httpx.Client):
        """Delete product should return 404 for non-existent product."""
        response = client.delete(f"/products/{NONEXISTENT_UUID}")
        assert response.status_code == 404

import pytest
from fastapi import status

def test_create_product(client, sample_product_data):
    response = client.post("/api/products/", json=sample_product_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    return data

def test_get_product(client):
    # Test intégré qui crée puis récupère un produit
    product_data = {
        "name": "Test Get Product",
        "description": "Test Description",
        "stock": 5,
        "prices": [{"amount": 15.99}]
    }
    create_response = client.post("/api/products/", json=product_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    
    product_id = create_response.json()["id"]
    get_response = client.get(f"/api/products/{product_id}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["id"] == product_id

def test_get_all_products(client):
    # Créer deux produits pour tester la liste
    client.post("/products/", json={
        "name": "Product 1",
        "description": "Desc 1",
        "stock": 1,
        "prices": [{"amount": 10.00}]
    })
    client.post("/products/", json={
        "name": "Product 2", 
        "description": "Desc 2",
        "stock": 2,
        "prices": [{"amount": 20.00}]
    })
    
    response = client.get("/api/products/")
    assert response.status_code == status.HTTP_200_OK
    products = response.json()
    assert len(products) >= 2

def test_update_product(client):
    # Créer puis mettre à jour un produit
    create_response = client.post("/api/products/", json={
        "name": "Original",
        "description": "Original",
        "stock": 1,
        "prices": [{"amount": 1.00}]
    })
    product_id = create_response.json()["id"]
    
    update_response = client.put(f"/api/products/{product_id}", json={
        "name": "Updated",
        "prices": [{"amount": 2.00}]
    })
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["name"] == "Updated"

def test_delete_product(client):
    create_response = client.post("/api/products/", json={
        "name": "To Delete",
        "description": "Delete me",
        "stock": 1,
        "prices": [{"amount": 1.00}]
    })
    product_id = create_response.json()["id"]
    
    delete_response = client.delete(f"/api/products/{product_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    
    get_response = client.get(f"/api/products/{product_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
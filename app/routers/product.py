from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session, joinedload
from ..config.database import SessionLocal
from ..models.product import Product as ProductModel
from ..models.price import Price as PriceModel
from typing import List
from ..config.schemas import ProductCreate, Product as ProductSchema, Price as PriceSchema, ProductUpdate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/products", response_model=ProductSchema)
def create_product(product_data: ProductCreate = Body(...), db: Session = Depends(get_db)):
    try:
        db_product = ProductModel(
            name=product_data.name,
            description=product_data.description,
            stock=product_data.stock
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        # Ajouter les prix associés
        for price_data in product_data.prices:
            db_price = PriceModel(amount=price_data.amount, product_id=db_product.id)
            db.add(db_price)

        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(ProductModel).options(joinedload(ProductModel.prices)).filter(ProductModel.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products", response_model=List[ProductSchema])
def get_all_products(db: Session = Depends(get_db)):
    try:
        products = db.query(ProductModel).options(joinedload(ProductModel.prices)).all()
        if not products:
            raise HTTPException(status_code=404, detail="Aucun produit trouvé")
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/products/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int,
    updated_product: ProductUpdate = Body(...),
    db: Session = Depends(get_db)
):
    try:
        product = db.query(ProductModel).options(joinedload(ProductModel.prices)).filter(ProductModel.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        # Mise à jour des champs simples
        update_data = updated_product.dict(exclude_unset=True)

        # Gérer les prix séparément
        prices_data = update_data.pop("prices", None)

        for key, value in update_data.items():
            setattr(product, key, value)

        # Si une nouvelle liste de prix est fournie, on remplace
        if prices_data is not None:
            # Supprimer les anciens prix
            for old_price in product.prices:
                db.delete(old_price)
            db.commit()

            # Ajouter les nouveaux prix
            for price in prices_data:
                new_price = PriceModel(amount=price["amount"], product_id=product.id)
                db.add(new_price)

        db.commit()
        db.refresh(product)
        return product

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/products/{product_id}", response_model=dict)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        db.delete(product)
        db.commit()
        return {"detail": f"Produit avec l'id {product_id} supprimé avec succès."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
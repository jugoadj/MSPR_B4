from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session, joinedload
from config.database import SessionLocal
from models.product import Product as ProductModel
from models.price import Price as PriceModel
from typing import List
from config.schemas import ProductCreate, Product as ProductSchema, Price as PriceSchema

router = APIRouter()

# Utilisation d'un gestionnaire de contexte pour la session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/products", response_model=ProductSchema)
def create_product(product_data: ProductCreate = Body(...), db: Session = Depends(get_db)):
    try:
        # Créer le produit sans les prix pour commencer
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

        db.commit()  # Commiter après avoir ajouté les prix
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        # Utilisation de joinedload pour charger les prix en même temps que le produit
        product = db.query(ProductModel).options(joinedload(ProductModel.prices)).filter(ProductModel.id == product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products", response_model=List[ProductSchema])
def get_all_products(db: Session = Depends(get_db)):
    try:
        # Utilisation de joinedload pour charger les prix en même temps que les produits
        products = db.query(ProductModel).options(joinedload(ProductModel.prices)).all()

        if not products:
            raise HTTPException(status_code=404, detail="Aucun produit trouvé")

        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

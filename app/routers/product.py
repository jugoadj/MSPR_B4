from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..config.database import get_db
from ..models.product import Product as ProductModel
from ..models.price import Price as PriceModel
from ..config.schemas import ProductCreate, ProductResponse, PriceCreate, ProductUpdate
from ..middleware.auth import verify_token

router = APIRouter(
    prefix="/api/products",
    tags=["products"],
    dependencies=[Depends(verify_token)]
)

NO_PRODUCT_FOUND = "Produit non trouvé"

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau produit avec ses prix associés
    """
    try:
        # Création du produit
        db_product = ProductModel(
            name=product_data.name,
            description=product_data.description,
            stock=product_data.stock
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        # Ajout des prix
        for price in product_data.prices:
            db_price = PriceModel(
                amount=price.amount,
                product_id=db_product.id
            )
            db.add(db_price)
        
        db.commit()
        db.refresh(db_product)
        return db_product

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la création: {str(e)}"
        )

@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un produit spécifique par son ID
    """
    product = db.query(ProductModel)\
        .options(joinedload(ProductModel.prices))\
        .filter(ProductModel.id == product_id)\
        .first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NO_PRODUCT_FOUND
        )
    return product

@router.get(
    "/",
    response_model=List[ProductResponse]
)
def get_all_products(db: Session = Depends(get_db)):
    """
    Récupère tous les produits avec leurs prix
    """
    products = db.query(ProductModel)\
        .options(joinedload(ProductModel.prices))\
        .all()
    return products

@router.put(
    "/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour un produit et ses prix
    """
    try:
        product = db.query(ProductModel)\
            .options(joinedload(ProductModel.prices))\
            .filter(ProductModel.id == product_id)\
            .first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NO_PRODUCT_FOUND
            )

        # Mise à jour des champs de base
        update_data = product_data.dict(exclude_unset=True, exclude={"prices"})
        for field, value in update_data.items():
            setattr(product, field, value)

        # Mise à jour des prix si fournis
        if product_data.prices is not None:
            # Suppression des anciens prix
            db.query(PriceModel)\
                .filter(PriceModel.product_id == product_id)\
                .delete()
            
            # Ajout des nouveaux prix
            for price in product_data.prices:
                db_price = PriceModel(
                    amount=price.amount,
                    product_id=product.id
                )
                db.add(db_price)

        db.commit()
        db.refresh(product)
        return product

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un produit spécifique
    """
    product = db.query(ProductModel)\
        .filter(ProductModel.id == product_id)\
        .first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NO_PRODUCT_FOUND
        )

    try:
        db.delete(product)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )
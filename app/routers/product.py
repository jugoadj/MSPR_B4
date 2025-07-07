from fastapi import APIRouter, HTTPException, Depends, status, Body, Path, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..config.database import get_db
from ..models.product import Product as ProductModel
from ..models.price import Price as PriceModel
from ..config.schemas import ProductCreate, ProductResponse, PriceCreate, ProductUpdate
from sqlalchemy.exc import SQLAlchemyError
from .rabbitmq import publish_product




router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={
        404: {"description": "Produit non trouvé"},
        401: {"description": "Non autorisé"},
        403: {"description": "Opération non permise"}
    }
)



@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Produit créé avec succès"},
        400: {"description": "Données invalides"},
        422: {"description": "Erreur de validation"}
    }
)
def create_product(
    product_data: ProductCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau produit avec ses prix associés.
    """
    try:
        if not product_data.prices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Au moins un prix doit être fourni"
            )

        if any(price.amount <= 0 for price in product_data.prices):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tous les prix doivent être supérieurs à 0"
            )

        db_product = ProductModel(
            name=product_data.name,
            description=product_data.description,
            stock=product_data.stock
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        # Crée les prix
        for price in product_data.prices:
            db_price = PriceModel(
                amount=price.amount,
                product_id=db_product.id
            )
            db.add(db_price)

        db.commit()
        db.refresh(db_product)

        # On recharge le produit avec les prix
        db.refresh(db_product)
        product_with_prices = db.query(ProductModel).options(joinedload(ProductModel.prices)).filter(ProductModel.id == db_product.id).first()

        # Envoie le message à RabbitMQ
        publish_product(ProductResponse.model_validate(product_with_prices).model_dump())

        return ProductResponse.model_validate(product_with_prices)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de base de données : {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur inattendue : {str(e)}"
        )

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    responses={
        200: {"description": "Détails du produit"},
        404: {"description": "Produit non trouvé"}
    }
)
def get_product(
    product_id: int = Path(..., description="ID du produit à récupérer"),
    db: Session = Depends(get_db)
):
    """
    Récupère un produit spécifique par son ID avec tous ses prix.
    """
    product = db.query(ProductModel)\
        .options(joinedload(ProductModel.prices))\
        .filter(ProductModel.id == product_id)\
        .first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produit non trouvé"
        )

    return ProductResponse.model_validate(product)

@router.get(
    "/",
    response_model=List[ProductResponse],
    response_description="Liste de tous les produits avec leurs prix"
)
def get_all_products(
    skip: int = Query(0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, description="Nombre maximum d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les produits avec leurs prix (pagination disponible).
    """
    products = db.query(ProductModel)\
        .options(joinedload(ProductModel.prices))\
        .offset(skip)\
        .limit(limit)\
        .all()

    return [ProductResponse.model_validate(p) for p in products]

@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    responses={
        200: {"description": "Produit mis à jour"},
        400: {"description": "Données invalides"},
        404: {"description": "Produit non trouvé"}
    }
)
def update_product(
    product_id: int = Path(..., description="ID du produit à mettre à jour"),
    product_data: ProductUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Met à jour un produit et/ou ses prix. Tous les anciens prix sont remplacés.
    """
    try:
        product = db.query(ProductModel)\
            .options(joinedload(ProductModel.prices))\
            .filter(ProductModel.id == product_id)\
            .first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produit non trouvé"
            )

        update_data = product_data.dict(exclude_unset=True, exclude={"prices"})
        for field, value in update_data.items():
            setattr(product, field, value)

        if product_data.prices is not None:
            if any(price.amount <= 0 for price in product_data.prices):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tous les prix doivent être supérieurs à 0"
                )

            db.query(PriceModel).filter(PriceModel.product_id == product_id).delete()

            for price in product_data.prices:
                db_price = PriceModel(
                    amount=price.amount,
                    product_id=product.id
                )
                db.add(db_price)

        db.commit()
        db.refresh(product)
        # Recharge avec les prix mis à jour
        product = db.query(ProductModel).options(joinedload(ProductModel.prices)).filter(ProductModel.id == product_id).first()

        # Envoie à RabbitMQ
        publish_product(ProductResponse.model_validate(product).model_dump())

        return ProductResponse.model_validate(product)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de base de données : {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur inattendue : {str(e)}"
        )

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Produit supprimé avec succès"},
        404: {"description": "Produit non trouvé"},
        400: {"description": "Erreur lors de la suppression"}
    }
)
def delete_product(
    product_id: int = Path(..., description="ID du produit à supprimer"),
    db: Session = Depends(get_db)
):
    """
    Supprime un produit spécifique et tous ses prix associés.
    """
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produit non trouvé"
        )

    try:
        db.query(PriceModel).filter(PriceModel.product_id == product_id).delete()
        db.delete(product)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la suppression : {str(e)}"
        )
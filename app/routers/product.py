from fastapi import APIRouter, HTTPException, Depends, status, Body, Path, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
import json
from ..config.database import get_db
from ..models.product import Product as ProductModel
from ..models.price import Price as PriceModel
from ..config.schemas import ProductCreate, ProductResponse, PriceCreate, ProductUpdate
from sqlalchemy.exc import SQLAlchemyError
from ..services.rabbitmq_service import rabbitmq_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={
        404: {"description": "Produit non trouvé"},
        401: {"description": "Non autorisé"},
        403: {"description": "Opération non permise"}
    }
)

async def publish_product_event(event_type: str, product_data: dict, routing_key_suffix: str):
    """Helper function to publish product events to RabbitMQ"""
    try:
        event_message = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **product_data
        }
        routing_key = f"product.{routing_key_suffix}"
        await rabbitmq_service.publish_message(routing_key, event_message)
    except Exception as e:
        logger.error(f"Failed to publish {event_type} event: {str(e)}")

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
async def create_product(
    product_data: ProductCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau produit avec ses prix associés et publie un événement RabbitMQ.
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

        for price in product_data.prices:
            db_price = PriceModel(
                amount=price.amount,
                product_id=db_product.id
            )
            db.add(db_price)

        db.commit()
        db.refresh(db_product)

        # Publier l'événement de création
        await publish_product_event(
            event_type="product_created",
            product_data={
                "product_id": db_product.id,
                "product_name": db_product.name,
                "prices": [price.amount for price in product_data.prices]
            },
            routing_key_suffix="created"
        )

        return ProductResponse.model_validate(db_product)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during product creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de base de données : {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during product creation: {str(e)}")
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
        logger.warning(f"Product not found with ID: {product_id}")
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
async def update_product(
    product_id: int = Path(..., description="ID du produit à mettre à jour"),
    product_data: ProductUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Met à jour un produit et/ou ses prix. Tous les anciens prix sont remplacés.
    Publie un événement RabbitMQ avec les modifications.
    """
    try:
        product = db.query(ProductModel)\
            .options(joinedload(ProductModel.prices))\
            .filter(ProductModel.id == product_id)\
            .first()

        if not product:
            logger.warning(f"Product not found for update with ID: {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produit non trouvé"
            )

        # Sauvegarder l'ancien état pour le message d'événement
        old_state = {
            "name": product.name,
            "description": product.description,
            "stock": product.stock,
            "prices": [price.amount for price in product.prices]
        }

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

        # Préparer les données de l'événement
        event_data = {
            "product_id": product.id,
            "product_name": product.name,
            "old_state": old_state,
            "new_state": {
                "name": product.name,
                "description": product.description,
                "stock": product.stock
            }
        }

        if product_data.prices is not None:
            event_data["new_state"]["prices"] = [price.amount for price in product_data.prices]

        # Publier l'événement de mise à jour
        await publish_product_event(
            event_type="product_updated",
            product_data=event_data,
            routing_key_suffix="updated"
        )

        return ProductResponse.model_validate(product)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during product update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de base de données : {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during product update: {str(e)}")
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
async def delete_product(
    product_id: int = Path(..., description="ID du produit à supprimer"),
    db: Session = Depends(get_db)
):
    """
    Supprime un produit spécifique et tous ses prix associés.
    Publie un événement RabbitMQ avant la suppression.
    """
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()

    if not product:
        logger.warning(f"Product not found for deletion with ID: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produit non trouvé"
        )

    try:
        # Publier l'événement avant la suppression
        await publish_product_event(
            event_type="product_deleted",
            product_data={
                "product_id": product.id,
                "product_name": product.name,
                "prices": [price.amount for price in product.prices]
            },
            routing_key_suffix="deleted"
        )

        db.query(PriceModel).filter(PriceModel.product_id == product_id).delete()
        db.delete(product)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during product deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la suppression : {str(e)}"
        )
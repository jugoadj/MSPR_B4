from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..config.database import get_db
from ..models.product import Product as ProductModel
from ..models.price import Price as PriceModel
from ..schemas import ProductCreate, ProductResponse, PriceCreate, ProductUpdate
from ..middleware.auth import verify_token
from pydantic import Field
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

router = APIRouter(
    prefix="/api/products",
    tags=["products"],
    dependencies=[Depends(verify_token)],
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
    product_data: ProductCreate = Body(
        ...,
        example={
            "name": "Nouveau produit",
            "description": "Description du produit",
            "stock": 100,
            "prices": [{"amount": 19.99}]
        }
    ),
    db: Session = Depends(get_db)
):
    """
    Crée un nouveau produit avec ses prix associés
    
    - **name**: Nom du produit (requis)
    - **description**: Description du produit
    - **stock**: Quantité en stock (doit être ≥ 0)
    - **prices**: Liste des prix associés (au moins un prix requis)
    """
    try:
        # Validation supplémentaire
        if not product_data.prices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Au moins un prix doit être fourni"
            )

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
            if price.amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Le prix doit être supérieur à 0"
                )
            db_price = PriceModel(
                amount=price.amount,
                product_id=db_product.id
            )
            db.add(db_price)
        
        db.commit()
        db.refresh(db_product)
        return ProductResponse.model_validate(db_product)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de base de données: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur inattendue: {str(e)}"
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
    Récupère un produit spécifique par son ID avec tous ses prix
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
    Récupère tous les produits avec leurs prix (pagination disponible)
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
    product_data: ProductUpdate = Body(..., description="Nouvelles données du produit"),
    db: Session = Depends(get_db)
):
    """
    Met à jour un produit et/ou ses prix
    
    - Seuls les champs fournis seront mis à jour
    - Pour les prix, toute la liste doit être fournie (remplacement complet)
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

        # Mise à jour des champs de base (uniquement ceux fournis)
        update_data = product_data.dict(exclude_unset=True, exclude={"prices"})
        for field, value in update_data.items():
            setattr(product, field, value)

        # Mise à jour des prix si fournis
        if product_data.prices is not None:
            # Validation des prix
            if any(price.amount <= 0 for price in product_data.prices):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tous les prix doivent être supérieurs à 0"
                )
            
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
        return ProductResponse.model_validate(product)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erreur de base de données: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur inattendue: {str(e)}"
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
    Supprime un produit spécifique et tous ses prix associés
    
    - Suppression permanente
    - Retourne un code 204 sans contenu si réussi
    """
    product = db.query(ProductModel)\
        .filter(ProductModel.id == product_id)\
        .first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produit non trouvé"
        )

    try:
        # Suppression en cascade des prix
        db.query(PriceModel)\
            .filter(PriceModel.product_id == product_id)\
            .delete()
        
        # Suppression du produit
        db.delete(product)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )
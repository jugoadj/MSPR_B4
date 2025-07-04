from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class PriceCreate(BaseModel):
    amount: float

class Price(BaseModel):
    id: int
    amount: float
    created_at: datetime
    product_id: int

    model_config = ConfigDict(from_attributes=True)  # Remplace orm_mode

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    stock: int

class ProductCreate(ProductBase):
    prices: List[PriceCreate]

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    prices: Optional[List[PriceCreate]] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    prices: List[Price]

    model_config = ConfigDict(from_attributes=True)

# Alias pour la réponse (peut être identique à Product)
ProductResponse = Product
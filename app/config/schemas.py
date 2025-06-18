from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class PriceCreate(BaseModel):
    amount: float

class Price(BaseModel):
    id: int
    amount: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    stock: int
    prices: List[PriceCreate]

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    prices: Optional[List[PriceCreate]] = None  # prix optionnels

class Product(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    stock: int
    created_at: datetime
    prices: List[Price]

    model_config = ConfigDict(from_attributes=True)

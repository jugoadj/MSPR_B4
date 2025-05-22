from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PriceCreate(BaseModel):
    amount: float

class Price(BaseModel):
    id: int
    amount: float
    created_at: datetime

    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    stock: int
    prices: List[PriceCreate]  

class Product(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    stock: int
    created_at: datetime
    prices: List[Price]

    class Config:
        orm_mode = True

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from ..config.database import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    stock = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship(
        "Price",
        back_populates="product",
        cascade="all, delete-orphan"
    )

from sqlalchemy import Column, Integer, String, Float, DateTime ,UniqueConstraint

from sqlalchemy.orm import relationship
from ..config.database import Base
from datetime import datetime, timezone

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    stock = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    prices = relationship(
        "Price",
        back_populates="product",
        cascade="all, delete-orphan"
    )


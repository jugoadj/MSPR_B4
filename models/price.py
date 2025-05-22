from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from config.database import Base
from datetime import datetime

class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="prices")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
import os

# Utilise la variable d'environnement ou SQLite en mémoire par défaut
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(engine)  # Crée les tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Annule les changements
        db.close()
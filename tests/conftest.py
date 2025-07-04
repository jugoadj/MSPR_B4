import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
import os

# Configuration spéciale pour les tests
DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    """Engine SQLAlchemy pour les tests"""
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Session de base de données isolée"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Client FastAPI de test"""
    from app.main import app
    from app.config.database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    yield TestClient(app)
    app.dependency_overrides.clear()
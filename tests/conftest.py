import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base

# Base SQLite en mémoire (ultra rapide, disparaît après la fin du test)
DATABASE_URL = "sqlite:///:memory:"

# Création de l'engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session liée à l'engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Avant chaque test, créer les tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

    # Après chaque test, drop des tables pour nettoyer la base
    Base.metadata.drop_all(bind=engine)

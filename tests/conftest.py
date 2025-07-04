import pytest
from fastapi.testclient import TestClient
from app.main import app  # Remplace par ton app FastAPI
from app.config.database import Base, get_db  # get_db vient de database.py

# (déjà défini)
DATABASE_URL_test = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL_test, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture session de test
@pytest.fixture(scope="function")
def db_session():
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
    Base.metadata.drop_all(bind=engine)

# Surcharge de la dépendance get_db de database.py
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

from fastapi import FastAPI
from .routers import product
from .config.database import Base, engine

app = FastAPI()

# Ne plus exécuter create_all ici automatiquement
# Base.metadata.create_all(bind=engine)

app.include_router(product.router, prefix="/api")

def init_db():
    """Fonction à appeler manuellement pour créer les tables."""
    Base.metadata.create_all(bind=engine)

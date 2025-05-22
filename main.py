from fastapi import FastAPI
from routers import product
from config.database import Base, engine


app = FastAPI()

# Créer les tables
Base.metadata.create_all(bind=engine)

app.include_router(product.router, prefix="/api")

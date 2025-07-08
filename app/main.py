from fastapi import FastAPI
from .routers import product
from .config.database import Base, engine
from prometheus_fastapi_instrumentator import Instrumentator




app = FastAPI()

# Ne plus exécuter create_all ici automatiquement
# Base.metadata.create_all(bind=engine)

app.include_router(product.router, prefix="/api")

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_group_untemplated=True,
)
Instrumentator().instrument(app).expose(app)




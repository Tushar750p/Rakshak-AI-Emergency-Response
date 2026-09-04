from .main import app
from .advanced import router as advanced_router
from .production_routes import router as production_router

# Production entrypoint mounts the advanced safety and production integration contracts.
app.include_router(advanced_router)
app.include_router(production_router)

from .main import app
from .advanced import router as advanced_router

# Production entrypoint: keeps the existing API and mounts advanced modules.
app.include_router(advanced_router)

from .main import app, init_db

# Initialize the base schema before importing advanced routes.
# advanced.py extends the incidents table during import, so the base table
# must exist first in production startup.
init_db()

from .advanced import router as advanced_router
from .production_routes import router as production_router

# Production entrypoint mounts the advanced safety and production integration contracts.
app.include_router(advanced_router)
app.include_router(production_router)

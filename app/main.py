# main.py -> app yahin banta hai. Yahi "entry point" hai.
# Chalane ke liye:  uvicorn app.main:app --reload
# ("app.main" = app folder ki main.py, ":app" = us file ka `app` variable)

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.errors import register_error_handlers
from app.routes import router

app = FastAPI(
    title="MaaKosh Simulator API",
    description="Generates simulated newborn-patch and belly-band readings. Not for clinical use.",
    version="0.1.0",
)

# Error ka common format jodte hain (errors.py).
register_error_handlers(app)

# Saare endpoints jodte hain (routes.py).
app.include_router(router)

# /static/... se HTML/CSS/JS files milti hain.
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    """Browser mein http://127.0.0.1:8000/ kholo to input box + output box wala page dikhta hai."""
    return FileResponse(config.STATIC_DIR / "index.html")

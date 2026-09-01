from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, profiles, listings, favorites, notifications, stats

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ImmoFinder API",
    description="Wohnungssuche-Assistent für den deutschen Wohnungsmarkt.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(listings.router)
app.include_router(favorites.router)
app.include_router(notifications.router)
app.include_router(stats.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

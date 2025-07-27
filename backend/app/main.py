from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import auth, users, friends, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("Starting up... Initialize resources here if needed")
    yield
    # Shutdown code
    print("Shutting down... Clean up resources here if needed")

app = FastAPI(title="Chat App API", lifespan=lifespan)

# CORS setup
origins = [
    "http://localhost",
    "http://localhost:3000",
    # add other allowed origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(friends.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
@app.get("/")
async def root():
    return {"message": "Welcome to the Chat App API"}

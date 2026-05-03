from dotenv import load_dotenv
from fastapi import FastAPI
from api.routes import reddit


app = FastAPI()

load_dotenv()


app.include_router(reddit.router, prefix="/api")
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from routes.chat import router

app = FastAPI()

app.include_router(router)
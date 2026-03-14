from fastapi import FastAPI

from app.config.set_main import register_routers, register_exception_handlers, lifespan

app = FastAPI(lifespan=lifespan)

register_routers(app)
register_exception_handlers(app)

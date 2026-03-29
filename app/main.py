from fastapi import FastAPI

from app.config.set_main import lifespan, setup_main, create_lifespan


def create_app(test_mode: bool = False):
    """Create FastAPI application.

    Args:
        test_mode: If True, skip database/redis initialization in lifespan
    """
    app_lifespan = create_lifespan(test_mode=test_mode) if test_mode else lifespan
    app = FastAPI(lifespan=app_lifespan)
    setup_main(app)
    return app


# Production app
app = create_app(test_mode=False)

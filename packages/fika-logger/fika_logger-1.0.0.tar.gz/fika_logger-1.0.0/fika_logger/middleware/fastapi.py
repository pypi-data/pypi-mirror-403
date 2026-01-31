from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from ..logger import FikaLogger


class FikaExceptionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger: "FikaLogger"):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            self.logger.exception(
                f"Unhandled exception: {e.__class__.__name__}: {str(e)}",
                request_method=request.method,
                request_path=request.url.path,
            )
            raise


def instrument_fastapi(app: FastAPI, logger: "FikaLogger") -> None:
    app.add_middleware(FikaExceptionMiddleware, logger=logger)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(
            f"Unhandled: {exc.__class__.__name__}: {str(exc)}",
            request_method=request.method,
            request_path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

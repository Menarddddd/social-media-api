from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.exception import (
    BadRequestException,
    FieldNotFoundException,
    DuplicateEntryException,
    CredentialsException,
)


def field_not_found_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, FieldNotFoundException)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={exc.field: exc.value, "message": str(exc)},
    )


def duplicate_entry_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DuplicateEntryException)

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={exc.field: exc.value, "message": str(exc)},
    )


def credentials_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, CredentialsException)

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": exc.error},
    )


def bad_request_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, BadRequestException)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"message": exc.message}
    )

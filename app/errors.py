# errors.py -> sab errors ka ek hi format.
# Chahe galti validation ki ho, URL galat ho ya server mein bug ho, client ko hamesha ye shape milega:
#   {"error": {"code": "...", "message": "...", "details": [...]}}
# Fayda: frontend / evaluator ko har error alag tareeke se samajhna nahi padta.

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Hamare apne errors ka base class. Har error ka status code, code aur message hota hai."""

    status_code = 400
    code = "app_error"

    def __init__(self, message: str, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or []


class DeviceNotFound(AppError):
    """Jab aisa device maanga jaaye jo hamare paas hai hi nahi -> 404."""

    status_code = 404
    code = "device_not_found"


def error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    # Ek jagah se hi error ka JSON banta hai, isliye format kabhi alag nahi hoga.
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or []}},
    )


def register_error_handlers(app: FastAPI) -> None:
    """main.py is function ko ek baar call karta hai; yahan saare handlers jud jaate hain."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        # Pydantic ke errors ko seedhe-saade shape mein badalte hain: kaun si field, kya problem.
        details = []
        for err in exc.errors():
            # "loc" jaise ("body", "count") ya ("query", "seed") hota hai;
            # "body"/"query" hata ke sirf field naam rakhte hain, taaki format ek jaisa rahe.
            parts = [str(p) for p in err["loc"] if p not in ("body", "query")]
            details.append(
                {
                    "field": ".".join(parts) or "body",
                    "problem": err["msg"],
                    "type": err["type"],
                }
            )
        return error_response(422, "validation_error", "Request data is invalid.", details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        # Jaise galat URL (404) ya galat method (405) - ye FastAPI khud uthata hai.
        codes = {404: "not_found", 405: "method_not_allowed"}
        code = codes.get(exc.status_code, "http_error")
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # Koi anjaan bug: andar ki detail bahar nahi dikhate (security), bas generic message.
        return error_response(500, "internal_error", "Something went wrong on the server.")

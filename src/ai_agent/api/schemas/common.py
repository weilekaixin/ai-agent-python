from typing import Any

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai_agent.models.constants import SUCCESS, ZERO


class ApiResponse(BaseModel):
    code: int = ZERO
    message: str = SUCCESS
    data: Any = None


def ok(data: Any = None) -> JSONResponse:
    return JSONResponse(ApiResponse(data=data).model_dump(), status_code=status.HTTP_200_OK)


def fail(code: int, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> JSONResponse:
    return JSONResponse(ApiResponse(code=code, message=message).model_dump(), status_code=status_code)

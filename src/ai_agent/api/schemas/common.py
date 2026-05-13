from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai_agent.models.constants import SUCCESS, ZERO, HTTP_200, HTTP_400


class ApiResponse(BaseModel):
    code: int = ZERO
    message: str = SUCCESS
    data: object = None


def ok(data: object = None) -> JSONResponse:
    return JSONResponse(ApiResponse(data=data).model_dump(), status_code=HTTP_200)


def fail(code: int, message: str, status: int = HTTP_400) -> JSONResponse:
    return JSONResponse(ApiResponse(code=code, message=message).model_dump(), status_code=status)

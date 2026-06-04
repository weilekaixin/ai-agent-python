from typing import Optional

from pydantic import BaseModel, Field


class PersonaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    avatar: Optional[str] = Field(None, max_length=200)


class PersonaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    avatar: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None

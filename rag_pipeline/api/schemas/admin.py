from __future__ import annotations

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str


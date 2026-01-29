from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# -----------------------------
# Enumeraciones
# -----------------------------


class State(Enum):
    """Estados posibles de las solicitudes."""

    NA = ""
    APROBADA = "aprobada"
    NEGADA = "negada"
    APLAZADA = "aplazada"


class RequestDataUnique(BaseModel):
    """Modelo de request para data_unique"""

    solicitud: str


class RequestDataFull(BaseModel):
    """Modelo de request para data_full"""

    estado: State
    fechaInicio: datetime = Field(..., description="YYYY-MM-DD")
    fechaFin: datetime = Field(..., description="YYYY-MM-DD")

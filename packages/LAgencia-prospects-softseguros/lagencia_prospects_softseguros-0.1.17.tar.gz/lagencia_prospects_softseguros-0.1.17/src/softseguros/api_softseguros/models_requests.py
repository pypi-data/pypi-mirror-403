from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict


class Observations(BaseModel):
    canon: Optional[Union[int, float, str]] = None
    valor_comercial: Optional[Union[int, float, str]] = None
    destinacion: Optional[str] = None
    clase: Optional[str] = None
    urbanizacion_inmueble: Optional[str] = None
    asesor: Optional[str] = None
    correoAsesor: Optional[str] = None


class RequestsCreateCustomerSoftseguros(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    tipo_documento: Optional[str] = "cedula"
    numero_documento: Optional[str|int]
    nombres: Optional[str]
    genero: Optional[str] = "MASCULINO"
    direccion: Optional[str]
    telefono: Optional[str]
    celular: Optional[str]
    email: Optional[str]
    departamento: Optional[str] = "ANTIOQUIA"
    ciudad: Optional[str]
    ids_categorias: Optional[str] = None
    fecha_expedicion_cedula: Optional[str | datetime] = None
    ingreso_mensual: Optional[str | int | float] = None
    observaciones: Optional[str] = None

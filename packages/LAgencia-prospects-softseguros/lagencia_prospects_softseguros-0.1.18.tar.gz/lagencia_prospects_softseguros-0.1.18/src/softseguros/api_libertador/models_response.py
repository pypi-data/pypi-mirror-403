from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class DetailByDataUnique(BaseModel):
    """
    Detalles de una solicitud individual en la API de Libertador.

    Attributes:
        solicitud: Número único de solicitud
        codigoResultado: Código numérico del resultado
        descripcionResultado: Descripción del estado o resultado de la solicitud
        tipoDeudor: Tipo de deudor (ej: INQUILINO)
        nombre: Nombre completo del solicitante
        identificacion: Número de identificación del deudor
        ingresos: Ingresos mensuales del deudor
        fechaExpedicion: fecha de expedicion del documento del deudor

        # Ejemplo de respuesta json del endpoint del api
        [
            {
                "solicitud": "7863524",
                "codigoResultado": "03",
                "descripcionResultado": "LAMENTAMOS NO PODER ASEGURARLO",
                "tipoDeudor": "INQUILINO",
                "nombre": "LONDOÑO USUGA LAURA PAULINA",
                "identificacion": "1000547341",
                "ingresos": "0",
                "fechaExpedicion": "No Registra"
            },
            {
                "solicitud": "7863525",
                "codigoResultado": "03",
                "descripcionResultado": "LAMENTAMOS NO PODER ASEGURARLO",
                "tipoDeudor": "DEUDOR SOLIDARIO",
                "nombre": "ORTIZ CARDONA MILLER JOVANA",
                "identificacion": "43205687",
                "ingresos": "0",
                "fechaExpedicion": "No Registra"
            }
        ]

    """

    model_config = ConfigDict(title="Detalle de Solicitud Individual", frozen=False)

    solicitud: str = Field(..., description="Número único de solicitud")
    descripcionResultado: str = Field(..., description="Descripción del estado o resultado")
    codigoResultado: str = Field(..., description="Código numérico del resultado")
    nombre: str = Field(..., description="Nombre completo del solicitante")
    tipoDeudor: str = Field(..., description="Tipo de deudor (ej: INQUILINO)")
    identificacion: str = Field(..., description="Número de identificación del deudor")
    ingresos: str = Field(..., description="ingresos mensuales", examples=["965886", "0"])
    fechaExpedicion: str = Field(..., description="Fecha de expedicion del documento (YYYY-MM-DDTHH:MM)", examples=["2019-12-20T00:00", "No Registra"])


class DetailByDataFull(BaseModel):
    """
    Detalles completos de una solicitud en la API de Libertador.

    Attributes:
        poliza: Número de póliza
        solicitud: Número de solicitud
        tipoIdentificacion: Tipo de documento (CC)
        identificacionInquilino: Número de identificación del inquilino
        estadoGeneral: Estado actual de la solicitud
        direccionInmueble: Dirección del inmueble
        correoInquilino: Correo electrónico del inquilino
        telefonoInquilino: Teléfono de contacto del inquilino
        canon: Valor del canon de arrendamiento
        destinoInmueble: Destino del inmueble (Vivienda/Comercial)
        ciudadInmueble: Ciudad donde está ubicado el inmueble
        fechaRadicacion: Fecha y hora de radicación (formato: DD/MM/YYYY HH:MM:SS)
        fechaResultado: Fecha y hora del resultado
        cuota: Valor de la cuota (puede ser 0 o un monto)
        nombreInquilino: Nombre completo del inquilino
        fechaExpedicion: Fecha de expedicion del documento del inquilino
        ingresos: ingresos mensuales del inquilino
        nombreAsesor: nombre del asesor responsable
        correoAsesor: correo del asesor responsable

        # Ejemplo de respuesta json del endpoint del api
        [
            {
                "poliza": "13183",
                "solicitud": "11791941",
                "nombreInquilino": "RUA CASTRO JUAN CARLOS",
                "tipoIdentificacion": "CC",
                "identificacionInquilino": "3570851",
                "fechaExpedicion": "2003-01-10",
                "ingresos": "965886",
                "estadoGeneral": "NEGADA",
                "direccionInmueble": "CRA 62 A # 74 SUR 167",
                "correoInquilino": "juanruacastro@hotmail.com",
                "telefonoInquilino": "3136069361",
                "canon": 1150000,
                "destinoInmueble": "Vivienda",
                "ciudadInmueble": "LA ESTRELLA",
                "fechaRadicacion": "29/10/2025 10:10:07",
                "fechaResultado": "29/10/2025 10:10:19",
                "cuota": "0",
                "nombreAsesor": "María Elena Gomez",
                "correoAsesor": "Comerial1@inmobiliarialaestrella.com"
            },
            {
                "poliza": "13183",
                "solicitud": "11792603",
                "nombreInquilino": "Johenis  Guerrero ",
                "tipoIdentificacion": "CC",
                "identificacionInquilino": "1007967825",
                "fechaExpedicion": "2019-12-20T00:00",
                "ingresos": "1662232",
                "estadoGeneral": "APLAZADO-NUBE",
                "direccionInmueble": "CL 55 80 39 AP 401",
                "correoInquilino": "johenisduran05@gmail.com",
                "telefonoInquilino": "3116076942",
                "canon": 1750000,
                "destinoInmueble": "Vivienda",
                "ciudadInmueble": "MEDELLIN",
                "fechaRadicacion": "29/10/2025 12:10:00",
                "fechaResultado": "29/10/2025 12:10:00",
                "cuota": "0",
                "nombreAsesor": "Katherine contreras",
                "correoAsesor": "Comercial4@inmobiliarialaestrella.com"
            },
        ]


    """

    model_config = ConfigDict(title="Detalle Completo de Solicitud", frozen=False)

    poliza: str = Field(..., description="Número de póliza")
    solicitud: str = Field(..., description="Número de solicitud")
    tipoIdentificacion: str = Field(..., description="Tipo de documento (CC, CE, etc)")
    identificacionInquilino: str = Field(..., description="Número de identificación del inquilino")
    estadoGeneral: str = Field(..., description="Estado actual de la solicitud")
    direccionInmueble: str = Field(..., description="Dirección del inmueble")
    correoInquilino: str = Field(..., description="Correo electrónico del inquilino")
    telefonoInquilino: str = Field(..., description="Teléfono de contacto del inquilino")
    canon: int = Field(..., description="Valor del canon de arrendamiento", gt=0)
    destinoInmueble: str = Field(..., description="Destino del inmueble (Vivienda/Comercial)")
    ciudadInmueble: str = Field(..., description="Ciudad donde está ubicado el inmueble")
    fechaRadicacion: str = Field(..., description="Fecha y hora de radicación (DD/MM/YYYY HH:MM:SS)", examples=["29/10/2025 12:10:00"])
    fechaResultado: str = Field(..., description="Fecha y hora del resultado (DD/MM/YYYY HH:MM:SS)", examples=["30/10/2025 12:10:00"])
    cuota: Union[int, str] = Field(..., description="Valor de la cuota (puede ser 0 o un monto)")
    nombreInquilino: str = Field(..., description="Nombre completo del inquilino")
    ingresos: str = Field(..., description="ingresos mensuales", examples=["965886", "0"])
    fechaExpedicion: str = Field(..., description="Fecha de expedicion del documento (YYYY-MM-DDTHH:MM)", examples=["2019-12-20T00:00", "No Registra"])
    nombreAsesor: str = Field(..., description="")
    correoAsesor: str = Field(..., description="")


class ResponseDataUnique(BaseModel):
    """Modelo de response para data_unique"""

    status: bool = Field(...)
    data: Optional[List[DetailByDataUnique]] = Field(None)
    message: str = Field(...)


class ResponseDataFull(BaseModel):
    """Modelo de response para data_full"""

    status: bool = Field(...)
    data: Optional[List[DetailByDataFull]] = None
    message: str = Field(...)

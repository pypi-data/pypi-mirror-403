import os
from pathlib import Path
from typing import Dict, Union

import httpx
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

from softseguros.database.models.models import ProspectsSoftin
from softseguros.database.repositories.softin import insert_records as insert_records_softin  # noqa: F401
from softseguros.database.repositories.softin import select_last_contract
from softseguros.database.repositories.softin import upsert_records as upsert_records_softin

load_dotenv()
ruta = Path(__file__).resolve().parent / ".." / "contract_registry.json"

# phones = os.getenv("PHONES")
# phones = ast.literal_eval(phones)
phones = ["573165241659", "573013853937", "573006538383"]
USERNAME = os.getenv("USERNAME_SOFTSEGUROS")
PASSWORD = os.getenv("USERNAME_PASSWORD_SOFTSEGUROS")


def with_point(n: Union[int, float, str]) -> str:
    """
    Formatea un número con puntos como separador de miles.

    Args:
        n: Número a formatear (puede ser entero, decimal o string)

    Returns:
        str: Número formateado con puntos como separador de miles
    """
    return f"{int(n):,}".replace(",", ".")


class ResquestData(BaseModel):
    username: str = os.getenv("USERNAME_SOFTSEGUROS")
    password: str = os.getenv("USERNAME_PASSWORD_SOFTSEGUROS")
    company: str
    token: str
    category: str
    numero_inmobiliaria: str
    contrato: str = Field(...)
    consecutivo: str = Field("0")
    solicitud: str = Field("0")


class ResquestDataVillacruz(ResquestData):
    company: str = "villacruz"
    token: str = os.getenv("TOKEN_SOFTIN_VILLACRUZ")
    category: str = "47665,47202"
    numero_inmobiliaria: str = "890918082"


class ResquestDataCastillo(ResquestData):
    company: str = "arrcastillo"
    token: str = os.getenv("TOKEN_SOFTIN_CASTILLO")
    category: str = "47665,47203"
    numero_inmobiliaria: str = "890930984"


class ResquestDataEstrella(ResquestData):
    company: str = "alquiventas"
    token: str = os.getenv("TOKEN_SOFTIN_ESTRELLA")
    category: str = "47665,47205"
    numero_inmobiliaria: str = "800018892"


def fetch_data(data: ResquestData) -> Dict:
    url = f"https://zonaclientes.softinm.com/api/contratos/contratoEstructurado/{data.company}"
    logger.info(f"Consultando datos en la URL: {url}")
    headers = {"Authorization": f"Bearer {data.token}"}
    payload = {"contrato": data.contrato}
    with httpx.Client() as client:
        response = client.post(url=url, headers=headers, json=payload)
        logger.debug(f"Respuesta HTTP: {response.status_code}")
        response.raise_for_status()
        response_json = response.json()
        # logger.debug(f"JSON recibido: {response_json}")
        if not response_json:
            logger.warning(f"No se recibió información del contrato: inmobiliaria:{data.company} contrto:{data.contrato}.")
            return {}
        response_json = response_json.get("contratos")
        if not response_json:
            return {}

        informacion_contrato_Inmueble = response_json[0].get("informacion_contrato_Inmueble")
        informacion_propietario = response_json[0].get("informacion_propietario")
        informacion_inquilino = response_json[0].get("informacion_inquilino")
        asignaciones_y_operaciones = response_json[0].get("asignaciones_y_operaciones")
        contrato = informacion_contrato_Inmueble.get("contrato")

        # if informacion_contrato_Inmueble.get("destinacionComercial") is False:
        #     destination = "Vivienda"
        # elif informacion_contrato_Inmueble.get("destinacionComercial") is True:
        #     destination = "Comercial"
        # else:
        #     destination = ""

        # # Calcular valor comercial según el canon
        # market_value = "0"
        # if informacion_contrato_Inmueble.get("canon"):
        #     canon = float(informacion_contrato_Inmueble.get("canon"))
        #     # Si el canon > 2M, el valor comercial es canon * 166.67, sino es canon * 200
        #     market_value = with_point(canon * 100 / 0.6 if canon > 2_000_000 else canon * 100 / 0.5)
        #     logger.debug(f"Valor comercial calculado: {market_value} para canon {canon}")

        # obs = Observations(valor_comercial=market_value, destinacion=destination, clase=inm.get("clase"), urbanizacion_inmueble=inm.get("urbanizacion_Inmueble"), asesor=asig_y_ope.get("nombre_Asesor"))
        # obs = str(obs.model_dump(mode="json"))
        # resp = {
        #     "numero_documento": prop.get("nro_id_prop"),
        #     "nombres": prop.get("nombre_Prop"),
        #     "direccion": inm.get("dir_inmueble"),
        #     "telefono": prop.get("celular_Prop"),
        #     "celular": prop.get("celular_Prop"),
        #     "email": prop.get("email_Prop"),
        #     "ciudad": inm.get("municipio_Inmueble"),
        #     "ids_categorias": data.category,
        #     "observaciones": obs,
        # }
        # logger.info(f"Datos transformados para Softseguros: {resp}")
        # return resp

        if data.company == "alquiventas":
            data.company = "estrella"

        if data.company == "arrcastillo":
            data.company = "castillo"

        return {
            "contrato": contrato,
            "informacion_contrato_Inmueble": str(informacion_contrato_Inmueble),
            "informacion_propietario": str(informacion_propietario),
            "informacion_inquilino": str(informacion_inquilino),
            "asignaciones_y_operaciones": str(asignaciones_y_operaciones),
            "real_state": data.company,
        }


def synchronize_prospects_softin(real_state: str):
    contrato = select_last_contract(real_state)
    print(contrato)
    retry = 0
    while retry < 30:
        logger.info("Intentando obtener datos para el contrato:", contrato)
        data = ResquestDataEstrella(contrato=str(contrato))
        result = fetch_data(data)

        # guardar en la base de datos
        if result:
            logger.info("Datos obtenidos para el contrato:", contrato)
            logger.info("Datos obtenidos para el contrato:", result)
            logger.info("Guardando en la base de datos")
            records = [ProspectsSoftin(**result)]
            upsert_records_softin(records)
        if not result:
            retry += 1
            contrato += 1
        else:
            retry = 0
            contrato += 1


def synchronize_prospects_softin_table_for_estrella():
    contrato = int(select_last_contract("estrella"))
    retry = 0
    while retry < 30:
        print(f"*** {contrato=}")
        print(f"*** {retry=}")
        logger.info("Intentando obtener datos para el contrato:", contrato)
        data = ResquestDataEstrella(contrato=str(contrato))
        result = fetch_data(data)

        # guardar en la base de datos
        if result:
            logger.info("Datos obtenidos para el contrato:", contrato)
            logger.info("Datos obtenidos para el contrato:", result)
            logger.info("Guardando en la base de datos")
            records = [ProspectsSoftin(**result)]
            upsert_records_softin(records)
        if not result:
            retry += 1
            contrato += 1
        else:
            retry = 0
            contrato += 1


def synchronize_prospects_softin_table_for_castillo():
    contrato = int(select_last_contract("castillo"))
    print(contrato)
    retry = 0
    while retry < 30:
        logger.info("Intentando obtener datos para el contrato:", contrato)
        data = ResquestDataCastillo(contrato=str(contrato))
        result = fetch_data(data)
        print(result)
        # guardar en la base de datos
        if result:
            logger.info("Datos obtenidos para el contrato:", contrato)
            logger.info("Datos obtenidos para el contrato:", result)
            logger.info("Guardando en la base de datos")
            records = [ProspectsSoftin(**result)]
            upsert_records_softin(records)
        if not result:
            retry += 1
            contrato += 1
        else:
            retry = 0
            contrato += 1


def synchronize_prospects_softin_table_for_villacruz():
    contrato = int(select_last_contract("villacruz"))
    print(contrato)
    retry = 0
    while retry < 30:
        logger.info("Intentando obtener datos para el contrato:", contrato)
        data = ResquestDataVillacruz(contrato=str(contrato))
        result = fetch_data(data)

        # guardar en la base de datos
        if result:
            logger.info("Datos obtenidos para el contrato:", contrato)
            logger.info("Datos obtenidos para el contrato:", result)
            logger.info("Guardando en la base de datos")
            records = [ProspectsSoftin(**result)]
            upsert_records_softin(records)
        if not result:
            retry += 1
            contrato += 1
        else:
            retry = 0
            contrato += 1

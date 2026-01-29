import ast
from typing import Union
import re
from loguru import logger  # noqa: F401

from softseguros.api_libertador.execute_load_to_db import synchronize_prospects_libertador_table_for_castillo, synchronize_prospects_libertador_table_for_estrella, synchronize_prospects_libertador_table_for_livin, synchronize_prospects_libertador_table_for_villacruz  # noqa: F401
from softseguros.api_softin.fetch_softin import fetch_data as fetch_data
from softseguros.api_softseguros.api_softseguros import ServiceAPISoftSeguros  # noqa: F401
from softseguros.api_softseguros.models_requests import Observations, RequestsCreateCustomerSoftseguros  # noqa: F401
from softseguros.database.models.models import ProspectsSoftin, ProspectsToSecure, create_schemas_segutos_bolivar  # noqa: F401
from softseguros.database.repositories.softin import insert_records as insert_records_softin  # noqa: F401
from softseguros.database.repositories.softin import select_prospects_softin_not_notified, update_field_created_in_softseguros_from_prospects_softin
from softseguros.database.repositories.softseguros import upsert_records as upsert_records_softseguros


def with_point(n: Union[int, float, str]) -> str:
    """
    Formatea un número con puntos como separador de miles.

    Args:
        n: Número a formatear (puede ser entero, decimal o string)

    Returns:
        str: Número formateado con puntos como separador de miles
    """
    return f"{int(n):,}".replace(",", ".")





def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D+", "", value)  # deja solo números
    if not digits:
        return None

    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def create_prospects_to_secure_for_landlord(real_state, informacion_contrato_Inmueble, informacion_propietario, asignaciones_y_operaciones):
    match real_state:
        case "villacruz":
            ids_categorias = ["47665", "47202"]
        case "castillo":
            ids_categorias = ["47665", "47203"]
        case "estrella":
            ids_categorias = ["47665", "47205"]
        case _:
            raise ()

    canon = float(informacion_contrato_Inmueble.get("canon", 0))
    # Si el canon > 2M, el valor comercial es canon * 166.67, sino es canon * 200
    market_value = with_point(canon * 100 / 0.6 if canon > 2_000_000 else canon * 100 / 0.5)
    logger.debug(f"Valor comercial calculado: {market_value} para canon {canon}")

    status_destination = informacion_contrato_Inmueble.get("destinacionComercial")
    destination = "Comercial" if status_destination else "Vivienda"

    observations = Observations(
        canon=informacion_contrato_Inmueble.get("canon"),
        valor_comercial=market_value,
        destinacion=destination,
        clase=informacion_contrato_Inmueble.get("clase"),
        urbanizacion_inmueble=informacion_contrato_Inmueble.get("urbanizacion_Inmueble"),
        asesor=asignaciones_y_operaciones.get("nombre_Asesor"),
        correoAsesor="",
    )

    phone= informacion_propietario.get("celular_Prop")
    clente = RequestsCreateCustomerSoftseguros(
        numero_documento=informacion_propietario.get("nro_id_prop"),
        nombres=informacion_propietario.get("nombre_Prop"),
        # apellidos="villa",
        direccion=informacion_contrato_Inmueble.get("dir_inmueble"),
        ciudad="",  # informacion_contrato_Inmueble.get("")
        telefono=phone,
        celular=phone,
        email=informacion_propietario.get("email_Prop"),
        ids_categorias=",".join(ids_categorias),
        fecha_expedicion_cedula=None,  # "yyyy-mm-dd"
        ingreso_mensual=None,
        observaciones=str(observations.model_dump(mode="json")),
    )

    return clente


def create_prospects_to_secure_for_tenant(real_state, informacion_contrato_Inmueble, informacion_inquilino, asignaciones_y_operaciones):
    match real_state:
        case "villacruz":
            ids_categorias = ["55088", "47202"]
        case "castillo":
            ids_categorias = ["55088", "47203"]
        case "estrella":
            ids_categorias = ["55088", "47205"]
        case _:
            raise ()

    canon = float(informacion_contrato_Inmueble.get("canon", 0))
    # Si el canon > 2M, el valor comercial es canon * 166.67, sino es canon * 200
    #market_value = with_point(canon * 100 / 0.6 if canon > 2_000_000 else canon * 100 / 0.5)
    market_value= "No aplica"
    logger.debug(f"Valor comercial calculado: {market_value} para canon {canon}")

    status_destination = informacion_contrato_Inmueble.get("destinacionComercial")
    destination = "Comercial" if status_destination else "Vivienda"

    observations = Observations(
        canon=informacion_contrato_Inmueble.get("canon"),
        valor_comercial=market_value,
        destinacion=destination,
        clase=informacion_contrato_Inmueble.get("clase"),
        urbanizacion_inmueble=informacion_contrato_Inmueble.get("urbanizacion_Inmueble"),
        asesor=asignaciones_y_operaciones.get("nombre_Asesor"),
        correoAsesor="",
    )

    phone= normalize_phone(informacion_inquilino.get("celular_Inq"))
    clente = RequestsCreateCustomerSoftseguros(
        numero_documento=informacion_inquilino.get("nro_id_Inq"),
        nombres=informacion_inquilino.get("nombre_Inq"),
        direccion=informacion_contrato_Inmueble.get("dir_inmueble"),
        ciudad="",  # informacion_contrato_Inmueble.get("")
        telefono=phone,
        celular=phone,
        email=informacion_inquilino.get("email_Inq"),
        ids_categorias=",".join(ids_categorias),
        fecha_expedicion_cedula=None,  # "yyyy-mm-dd"
        ingreso_mensual=None,
        observaciones=str(observations.model_dump(mode="json")),
    )

    return clente


def synchronize_the_softseguros_table_with_softin_prospects_for_landlord():
    records = select_prospects_softin_not_notified()
    for record in records:
        contrato = record.contrato
        logger.info(f"Procesando contrato: {contrato}")
        real_state = record.real_state
        informacion_contrato_Inmueble = ast.literal_eval(record.informacion_contrato_Inmueble)
        informacion_propietario = ast.literal_eval(record.informacion_propietario)
        informacion_inquilino = ast.literal_eval(record.informacion_inquilino)
        asignaciones_y_operaciones = ast.literal_eval(record.asignaciones_y_operaciones)

        client_landlord = create_prospects_to_secure_for_landlord(real_state, informacion_contrato_Inmueble, informacion_propietario, asignaciones_y_operaciones)
        client_tanant = create_prospects_to_secure_for_tenant(real_state, informacion_contrato_Inmueble, informacion_inquilino, asignaciones_y_operaciones)

        record_ = [ProspectsToSecure(**{**client_landlord.model_dump(mode="json"), "type": "propietario", "source": "softin", "real_state": real_state, "contrato_solicitud": str(contrato)+"p"})]
        upsert_records_softseguros(record_)
        logger.info(f"cliente propietario con documento: {informacion_propietario.get('nro_id_prop')} guardado en la tabla prospects_to_secure correctamente")

        record_ = [ProspectsToSecure(**{**client_tanant.model_dump(mode="json"), "type": "inquilino", "source": "softin", "real_state": real_state, "contrato_solicitud": str(contrato)+"i"})]
        upsert_records_softseguros(record_)
        logger.info(f"cliente inquilino-contrato con documento: {informacion_propietario.get('nro_id_prop')} guardado en la tabla prospects_to_secure correctamente")

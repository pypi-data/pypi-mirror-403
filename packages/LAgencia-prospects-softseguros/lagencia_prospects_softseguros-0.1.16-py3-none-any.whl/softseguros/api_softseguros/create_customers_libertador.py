from datetime import datetime
from typing import Optional, Union

from loguru import logger

from softseguros.api_softseguros.models_requests import Observations, RequestsCreateCustomerSoftseguros
from softseguros.database.models.models import ProspectsToSecure
from softseguros.database.repositories.libertadors import select_approved_records_liberator
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


def normalizar_fecha(fecha: Optional[Union[str, datetime]]) -> Optional[str]:
    """
    Convierte varios formatos de fecha a 'YYYY-MM-DD'.
    Acepta:
      - '1974-01-21T00:00'
      - '1974-01-21'
      - datetime.datetime
    Devuelve:
      - '1974-01-21' o None si no puede parsear / viene None.
    """
    if fecha is None:
        return None

    # Si ya es datetime, solo la formateamos
    if isinstance(fecha, datetime):
        return fecha.date().isoformat()

    if isinstance(fecha, str):
        fecha_str = fecha.strip()

        # Caso simple: ya viene en 'YYYY-MM-DD'
        if len(fecha_str) == 10 and fecha_str[4] == "-" and fecha_str[7] == "-":
            return fecha_str

        # Caso con 'T', tipo 'YYYY-MM-DDTHH:MM' o 'YYYY-MM-DDTHH:MM:SS'
        if "T" in fecha_str:
            solo_fecha = fecha_str.split("T", 1)[0]
            # Nos aseguramos de que sea YYYY-MM-DD
            try:
                dt = datetime.strptime(solo_fecha, "%Y-%m-%d")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                # si no matchea, dejamos caer al raise final
                pass

    # Si llegamos aquí, no supimos interpretar la fecha
    #raise ValueError(f"No se pudo normalizar la fecha: {fecha!r}")
    print(f"No se pudo normalizar la fecha: {fecha!r}")
    return None


def synchronize_the_softseguros_table_with_libertador_prospects():
    records = select_approved_records_liberator()
    for record in records:
        logger.info(f"Procesando solicitud del libertador: {record.solicitud}")
        canon = float(record.canon)
        # Si el canon > 2M, el valor comercial es canon * 166.67, sino es canon * 200
        market_value = with_point(canon * 100 / 0.6 if canon > 2_000_000 else canon * 100 / 0.5)
        logger.debug(f"Valor comercial calculado: {market_value} para canon {canon}")
        market_value= "No aplica"

        if record.fechaExpedicion != "No Registra":
            fecha_formatted = normalizar_fecha(record.fechaExpedicion)
        else:
            fecha_formatted = None

        match record.source:
            case "villacruz":
                ids_categorias = "47202,47664"
            case "castillo":
                ids_categorias = "47203,47664"
            case "estrella":
                ids_categorias = "47205,47664"
            case "livin":
                ids_categorias = "47204,47664"
            case _:
                raise ()

        observations = Observations(canon=record.canon, valor_comercial=market_value, destinacion=record.destinoInmueble, clase="No aplica", urbanizacion_inmueble="No aplica", asesor=record.nombreAsesor, correoAsesor=record.correoAsesor)
        client_tanant = RequestsCreateCustomerSoftseguros(
            numero_documento=record.identificacionInquilino,
            nombres=record.nombreInquilino,
            # apellidos="villa",
            direccion=record.direccionInmueble,
            ciudad=record.ciudadInmueble,
            telefono=record.telefonoInquilino,
            celular=record.telefonoInquilino,
            email=record.correoInquilino,
            ids_categorias=ids_categorias,
            fecha_expedicion_cedula=fecha_formatted,  # "yyyy-mm-dd"
            ingreso_mensual=record.ingresos,
            observaciones=str(observations.model_dump(mode="json")),
        )

        record_ = [ProspectsToSecure(**{**client_tanant.model_dump(mode="json"), "type": "inquilino", "source": "libertador", "real_state": record.source, "contrato_solicitud": str(record.solicitud)})]
        upsert_records_softseguros(record_)
        logger.info(f"cliente inquilino con documento: {record.identificacionInquilino} guardado en la tabla prospects_to_secure correctamente")

from datetime import datetime
import os
from typing import Optional, Union

from dotenv import load_dotenv

from softseguros.api_libertador.api import OAuth2BearerAuth, RequestDataUnique, ServiceAPILibertador, State
from softseguros.api_libertador.execute_load_to_db import synchronize_prospects_libertador_table_for_castillo, synchronize_prospects_libertador_table_for_estrella, synchronize_prospects_libertador_table_for_villacruz  # noqa: F401
from softseguros.api_libertador.models_request import RequestDataFull
from softseguros.api_softin.fetch_softin import fetch_data as fetch_data  # noqa: F401
from softseguros.api_softin.fetch_softin import synchronize_prospects_softin_table_for_castillo, synchronize_prospects_softin_table_for_estrella, synchronize_prospects_softin_table_for_villacruz  # noqa: F401
from softseguros.api_softseguros.create_customers_libertador import synchronize_the_softseguros_table_with_libertador_prospects  # noqa: F401
from softseguros.api_softseguros.create_customers_softin import synchronize_the_softseguros_table_with_softin_prospects_for_landlord  # noqa: F401
from softseguros.api_softseguros.create_prospectsfrom_in_crm_softseguros import create_prospectsfrom_libertador_in_crm_softseguros  # noqa: F401
from softseguros.database.models.models import create_schemas_segutos_bolivar  # noqa: F401
from softseguros.notifier.notificaciones import notify_prospect_from_libertador, notify_prospect_from_softin  # noqa: F401

load_dotenv()


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
    raise ValueError(f"No se pudo normalizar la fecha: {fecha!r}")


def main():
    #create_schemas_segutos_bolivar()

    # synchronize_prospects_libertador_table_for_estrella()
    # synchronize_prospects_libertador_table_for_castillo()
    # synchronize_prospects_libertador_table_for_villacruz()

    # synchronize_prospects_softin_table_for_estrella()
    # synchronize_prospects_softin_table_for_castillo()
    # synchronize_prospects_softin_table_for_villacruz()

    # synchronize_the_softseguros_table_with_libertador_prospects()
    # synchronize_the_softseguros_table_with_softin_prospects_for_landlord()

    # create_prospectsfrom_libertador_in_crm_softseguros()

    #notify_prospect_from_softin()
    #notify_prospect_from_libertador()
    #!=========================================================

    client_id = os.getenv("CLIENT_ID_ESTRELLA")
    client_secret = os.getenv("CLIENT_SECRET_ESTRELLA")

    # client_id = os.getenv("CLIENT_ID_CASTILLO")
    # client_secret = os.getenv("CLIENT_SECRET_CASTILLO")

    # client_id = os.getenv("CLIENT_ID_VILLACRUZ")
    # client_secret = os.getenv("CLIENT_SECRET_VILLACRUZ")

    service_libertador = ServiceAPILibertador(client_id=client_id, client_secret=client_secret)

    # data = RequestDataUnique(solicitud="11725333")
    # result = service_libertador.data_unique(data=data)
    # print(result)

    data = RequestDataFull(estado=State.APROBADA, fechaInicio=datetime(2026, 1, 12), fechaFin=datetime(2026, 1, 13))
    result = service_libertador.data_full(data=data)
    print(result)

    # result = service_libertador.request_a_one_day_range()
    # print(result)
    ...


if __name__ == "__main__":
    main()

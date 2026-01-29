import os
from datetime import datetime, timedelta
from typing import Optional, Union

from softseguros.api_libertador.api import RequestDataUnique, ServiceAPILibertador, State
from softseguros.api_libertador.models_request import RequestDataFull
from softseguros.database.models.models import ProspectsLibertador
from softseguros.database.repositories.libertadors import select_postponed_records_liberator, update_state_record_libertador, upsert_records


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
    # raise ValueError(f"No se pudo normalizar la fecha: {fecha!r}")
    print(f"No se pudo normalizar la fecha: {fecha!r}")
    return None


def synchronize_prospects_libertador_table(service_libertador: ServiceAPILibertador, start_date: datetime, end_date: datetime, source: str):
    # Consultamos registros aplazados y actualizamos su estado APROBADO si aplica (02: "APLAZADA", "143": "APLAZADA-NUBE")
    postponed_records_liberator = select_postponed_records_liberator(source=source)
    print(f"***{len(postponed_records_liberator)}")
    for record_liberator in postponed_records_liberator:
        data = RequestDataUnique(solicitud=str(record_liberator.solicitud))
        result_service_libertador_data_unique = service_libertador.data_unique(data=data)
        if result_service_libertador_data_unique.status:
            records_data_unique = result_service_libertador_data_unique.data
            for record_data_unique in records_data_unique:
                if record_data_unique.codigoResultado == "01":
                    print(f"Actualizando registro {str(record_liberator.solicitud)}: {record_data_unique.codigoResultado} -> APROBADA ")
                    update_state_record_libertador(solicitud=record_liberator.solicitud, new_state="APROBADA")
                    break

    # Carga de registros de libertador en tabla <prospects_libertador>
    data = RequestDataFull(estado=State.NA, fechaInicio=start_date, fechaFin=end_date)
    result = service_libertador.data_full(data=data)
    if result.data:
        for record in result.data:
            record.fechaExpedicion = normalizar_fecha(record.fechaExpedicion)

        records = [ProspectsLibertador(**{**record.model_dump(), "source": source}) for record in result.data]
        upsert_records(records)


def synchronize_prospects_libertador_table_for_estrella():
    client_id = os.getenv("CLIENT_ID_ESTRELLA")
    client_secret = os.getenv("CLIENT_SECRET_ESTRELLA")
    service_libertador = ServiceAPILibertador(client_id=client_id, client_secret=client_secret)
    start_date = datetime.now().date() - timedelta(days=1)
    end_date = datetime.now().date()
    # start_date = datetime(2025, 11, 1)
    # end_date = datetime(2025, 11, 26)
    synchronize_prospects_libertador_table(service_libertador=service_libertador, start_date=start_date, end_date=end_date, source="estrella")


def synchronize_prospects_libertador_table_for_castillo():
    client_id = os.getenv("CLIENT_ID_CASTILLO")
    client_secret = os.getenv("CLIENT_SECRET_CASTILLO")
    service_libertador = ServiceAPILibertador(client_id=client_id, client_secret=client_secret)
    start_date = datetime.now().date() - timedelta(days=1)
    end_date = datetime.now().date()
    # start_date = datetime(2025, 11, 1)
    # end_date = datetime(2025, 11, 26)
    synchronize_prospects_libertador_table(service_libertador=service_libertador, start_date=start_date, end_date=end_date, source="castillo")


def synchronize_prospects_libertador_table_for_villacruz():
    client_id = os.getenv("CLIENT_ID_VILLACRUZ")
    client_secret = os.getenv("CLIENT_SECRET_VILLACRUZ")
    service_libertador = ServiceAPILibertador(client_id=client_id, client_secret=client_secret)
    start_date = datetime.now().date() - timedelta(days=1)
    end_date = datetime.now().date()
    # start_date = datetime(2025, 11, 1)
    # end_date = datetime(2025, 11, 26)
    synchronize_prospects_libertador_table(service_libertador=service_libertador, start_date=start_date, end_date=end_date, source="villacruz")


def synchronize_prospects_libertador_table_for_livin():
    client_id = os.getenv("CLIENT_ID_LIVIN")
    client_secret = os.getenv("CLIENT_SECRET_LIVIN")
    service_libertador = ServiceAPILibertador(client_id=client_id, client_secret=client_secret)
    start_date = datetime.now().date() - timedelta(days=1)
    end_date = datetime.now().date()
    # start_date = datetime(2025, 11, 1)
    # end_date = datetime(2025, 11, 26)
    synchronize_prospects_libertador_table(service_libertador=service_libertador, start_date=start_date, end_date=end_date, source="livin")

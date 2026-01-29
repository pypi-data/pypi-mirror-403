import os

from softseguros.api_libertador.execute_load_to_db import synchronize_prospects_libertador_table_for_castillo, synchronize_prospects_libertador_table_for_estrella, synchronize_prospects_libertador_table_for_livin, synchronize_prospects_libertador_table_for_villacruz  # noqa: F401
from softseguros.api_softseguros.api_softseguros import ServiceAPISoftSeguros
from softseguros.api_softseguros.models_requests import RequestsCreateCustomerSoftseguros
from softseguros.database.models.models import ProspectsToSecure, create_schemas_segutos_bolivar  # noqa: F401
from softseguros.database.repositories.softseguros import insert_records as insert_records_softseguros  # noqa: F401
from softseguros.database.repositories.softseguros import select_those_not_created_in_the_crm, update_created_in_crm


def create_prospectsfrom_libertador_in_crm_softseguros():
    USERNAME = os.getenv("USERNAME_SOFTSEGUROS")
    PASSWORD = os.getenv("USERNAME_PASSWORD_SOFTSEGUROS")
    api = ServiceAPISoftSeguros(username=USERNAME, password=PASSWORD)

    records = select_those_not_created_in_the_crm()
    for record in records:
        print(f"***Creando prospecto en el crm contrato_solicitud: {record.contrato_solicitud}")
        result = api.fetch_customer(numero_documento=str(record.numero_documento))
        print(f"{result=}")
        if result:
            print(f"{record.contrato_solicitud=}")
            update_created_in_crm(contrato_solicitud=record.contrato_solicitud, status=True)
        if not result:
            # print(f"***Cliente con documento: {record.numero_documento} no ha sido creado")
            print(f"{record=}")
            obj = RequestsCreateCustomerSoftseguros.model_validate(record)
            print(f"{obj=}")
            result_create_customer = api.create_customer(obj)
            print(f"{result_create_customer=}")
            if result_create_customer.get("status"):
                print(f"{record.contrato_solicitud=}")
                update_created_in_crm(contrato_solicitud=record.contrato_solicitud, status=True)

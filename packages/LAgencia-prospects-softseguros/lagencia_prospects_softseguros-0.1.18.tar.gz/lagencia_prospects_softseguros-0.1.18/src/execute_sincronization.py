from dotenv import load_dotenv

from softseguros.api_libertador.execute_load_to_db import synchronize_prospects_libertador_table_for_castillo, synchronize_prospects_libertador_table_for_estrella, synchronize_prospects_libertador_table_for_villacruz
from softseguros.api_softin.fetch_softin import synchronize_prospects_softin_table_for_castillo, synchronize_prospects_softin_table_for_estrella, synchronize_prospects_softin_table_for_villacruz
from softseguros.api_softseguros.create_customers_libertador import synchronize_the_softseguros_table_with_libertador_prospects
from softseguros.api_softseguros.create_customers_softin import synchronize_the_softseguros_table_with_softin_prospects_for_landlord
from softseguros.api_softseguros.create_prospectsfrom_in_crm_softseguros import create_prospectsfrom_libertador_in_crm_softseguros
from softseguros.config.logging_config import configure_logger
from softseguros.notifier.notificaciones import notify_prospect_from_libertador, notify_prospect_from_softin


load_dotenv()
logger = configure_logger()


# def pr_api_softseguros_extrella():
#     username = os.getenv("USERNAME_SOFTSEGUROS")
#     password = os.getenv("USERNAME_PASSWORD_SOFTSEGUROS")
#     api_softseguros = ServiceAPISoftSeguros(username=username, password=password)

#     # 3610548
#     category_estrella = {"id": 47205, "nombre": "La Estrella", "color": "#28a187", "tipo": "cliente"}
#     customer = {"canon": 1800000, "identificacionInquilino": "10072325401", "nombreInquilino": "Juan Villa", "direccionInmueble": "Direcciion prueba", "telefonoInquilino": "573103555748", "correoInquilino": "juan@gmail.com"}
#     observations = Observations(canon=customer.get("canon"))
#     new_customer_softseguros = RequestsCreateCustomerSoftseguros(
#         numero_documento=customer.get("identificacionInquilino"),
#         nombres=customer.get("nombreInquilino"),
#         direccion=customer.get("direccionInmueble"),
#         telefono=customer.get("telefonoInquilino"),
#         celular=customer.get("telefonoInquilino"),
#         email=customer.get("correoInquilino"),
#         observations=observations,
#         ids_categorias=str(category_estrella.get("id")),
#     )

#     resp_create_customer = api_softseguros.create_customer(new_customer_softseguros)
#     print()
#     print(f"{customer=}\n")
#     print(f"{new_customer_softseguros=}\n")
#     print(f"{resp_create_customer=}\n")
#     print("*" * 50)

#     result_fetch_customer = api_softseguros.fetch_customer(numero_documento=customer.get("identificacionInquilino"))
#     print(f"{result_fetch_customer=}")


def main():
    logger.info("Hello from api-libertador!")
    # # + sincronizacion por libertador
    synchronize_prospects_libertador_table_for_estrella()
    synchronize_prospects_libertador_table_for_castillo()
    synchronize_prospects_libertador_table_for_villacruz()

    # # # # # # + sincronizacion por softin
    # synchronize_prospects_softin_table_for_estrella()
    # synchronize_prospects_softin_table_for_castillo()
    # synchronize_prospects_softin_table_for_villacruz()

    # # # # # + sincronizacion tabla softseguros
    # synchronize_the_softseguros_table_with_libertador_prospects()
    # synchronize_the_softseguros_table_with_softin_prospects_for_landlord()

    # # # + crear cleintes softseguros
    # create_prospectsfrom_libertador_in_crm_softseguros()

    # # # + notificar asesores
    # notify_prospect_from_libertador()
    # notify_prospect_from_softin()


if __name__ == "__main__":
    main()

    ...

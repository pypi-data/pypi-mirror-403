import ast
import json
import os
import time
from collections import defaultdict
from typing import Any, Dict, List

import httpx
from loguru import logger
from pydantic import BaseModel

from softseguros.database.repositories.softseguros import select_not_notified, update_notified  # noqa: F401

phones = os.getenv("PHONES")
PHONES = ast.literal_eval(phones)


def shipment_message_customers_libertador(phone_advisers: list[str], data_customers: Dict[str, Any], real_state: str) -> Dict[str, Any]:
    """
    Envía notificaciones de solicitudes a los asesores por WhatsApp usando la API externa.
    phone_advisers: lista de números de asesores
    data_customers: lista de datos de clientes (solicitud, nombre, celular)
    real_state: nombre de la inmobiliaria
    """
    logger.info("[INICIO] Envío de notificaciones de solicitudes a asesores")
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"
    headers = {"Content-Type": "application/json"}
    result = {}
    customers_list = " | ".join(f"solicitud: {s}, cedula:{d}, nombre: {n}, celular: {c}" for s, d, n, c in data_customers)
    for phone in phone_advisers:
        logger.debug(f"Preparando notificación para el asesor {phone} con clientes: {customers_list}")
        payload_notificacion_softseguros = json.dumps(
            {
                "app": "laestrellaalquiventas",
                "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
                "template": [{"id": "02e2070d-1e30-4e4e-9e16-20a4917956a6", "params": [customers_list, real_state]}],
                "localid": "softseg_inqs",
                "IntegratorUser": "0",
                "message": [],
                "number": phone,
            }
        )
        try:
            with httpx.Client() as session:
                response = session.post(url=url, headers=headers, data=payload_notificacion_softseguros)
                if response.status_code == 200:
                    logger.info(f"Notificación enviada con éxito a {phone}")
                    logger.debug(f"Respuesta de la API: {response.text}")
                    result.update({"status": True, "message": f"Notificación enviada con éxito a {phone}"})
                else:
                    logger.warning(f"Notificación fallida a {phone}")
                    logger.debug(f"Respuesta de la API: {response.text}")
                    result.update({"status": False, "message": f"Notificación fallida a {phone}: {response.text}"})
        except Exception as ex:
            logger.error(f"Error al enviar notificación a {phone}: {ex}")
            result.update({"status": False, "message": f"Notificación fallida a {phone} -> Error:{ex}"})
        time.sleep(30)
    logger.info("[FIN] Envío de notificaciones de solicitudes a asesores")


def shipment_message_owner_softin(phone_advisers: list[str], data_customers: List[List], real_state: str) -> Dict[str, Any]:
    """
    Envía notificaciones de propietarios a los asesores por WhatsApp usando la API externa.
    phone_advisers: lista de números de asesores
    data_customers: lista de datos de propietarios (nombre, celular)
    real_state: nombre de la inmobiliaria
    """
    logger.info("[INICIO] Envío de notificaciones de propietarios a asesores")
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"
    headers = {"Content-Type": "application/json"}
    result = {}
    customers_list = " | ".join(f"nombre: {n}, celular: {c}" for n, c in data_customers)
    for phone in phone_advisers:
        logger.debug(f"Preparando notificación para el asesor {phone} con propietarios: {customers_list}")
        payload_notificacion_softseguros = json.dumps(
            {"app": "laestrellaalquiventas", "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c", "template": [{"id": "f73387b9-8416-4ceb-994b-f2ae65b71a33", "params": [customers_list, real_state]}], "localid": "softseg_props", "IntegratorUser": "0", "message": [], "number": phone}
        )
        try:
            with httpx.Client() as session:
                response = session.post(url=url, headers=headers, data=payload_notificacion_softseguros)
                if response.status_code == 200:
                    logger.info(f"Notificación enviada con éxito a {phone}")
                    logger.debug(f"Respuesta de la API: {response.text}")
                    result.update({"status": True, "message": f"Notificación enviada con éxito a {phone}"})
                else:
                    logger.warning(f"Notificación fallida a {phone}")
                    logger.debug(f"Respuesta de la API: {response.text}")
                    result.update({"status": False, "message": f"Notificación fallida a {phone}: {response.text}"})
        except Exception as ex:
            logger.error(f"Error al enviar notificación a {phone}: {ex}")
            result.update({"status": False, "message": f"Notificación fallida a {phone} -> Error:{ex}"})
        time.sleep(30)
    logger.info("[FIN] Envío de notificaciones de propietarios a asesores")


class DataNotificationSofint(BaseModel):
    name_landlord: str
    document_landlord: str
    phone_landlor: str
    name_tenant: str
    document_tenant: str
    phone_tenant: str
    real_state: str


def shipment_message_prospect_from_softin(phones: List[str], data: DataNotificationSofint):
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"

    headers = {"Content-Type": "application/json"}

    result = []
    for phone in phones:
        with httpx.Client() as client:
            payload = {
                "app": "laestrellaalquiventas",
                "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
                "template": [
                    {
                        "id": "fdfe8742-fe86-4992-8705-ea69cc11f42c",
                        "params": [
                            data.name_landlord,  # "Nombre propietario"
                            data.document_landlord,  # "Documento propietario"
                            data.phone_landlor,  # "Celular propietario"
                            data.name_tenant,  # "Nombre inquilino"
                            data.document_tenant,  # "documento_inquilino"
                            data.phone_tenant,  # "Celular Inquilino"
                            data.real_state,  # "Inmobiliaria"
                        ],
                    }
                ],
                "localid": "custo_createdsoftseg",
                "IntegratorUser": "0",
                "message": [],
                "number": phone,
            }
            response = client.post(url, headers=headers, json=payload)
            result.append(response.status_code)
            print(f"Codigo de respuesta del envio: {response.status_code}")
            print(f"Resultado del envio: {response.text}")
            time.sleep(5)
    return result


def notify_prospect_from_softin():
    records = select_not_notified(source="softin")
    for record in records:
        record.contrato_solicitud = record.contrato_solicitud[:-1]

    # Agrupar por contrato_solicitud
    grupos = defaultdict(list)
    for record in records:
        grupos[record.contrato_solicitud].append(record)

    # Quedarnos solo con los que están duplicados (len > 1)
    lista_de_tuplas = [tuple(regs) for regs in grupos.values() if len(regs) > 1]

    for record in lista_de_tuplas:
        if len(record) > 0:
            if record[0].type == "inquilino":
                inquilino = record[0]
            elif record[0].type == "propietario":
                propietario = record[0]

            if record[1].type == "inquilino":
                inquilino = record[1]
            elif record[1].type == "propietario":
                propietario = record[1]

            record_ = DataNotificationSofint(name_landlord=propietario.nombres, document_tenant=propietario.numero_documento, phone_landlor=propietario.telefono, name_tenant=inquilino.nombres, document_landlord=inquilino.numero_documento, phone_tenant=inquilino.telefono, real_state=inquilino.real_state)

            result = shipment_message_prospect_from_softin(PHONES, record_)

            if result and len(result) > 0:
                if 200 in result:
                    print("mensaje enviado, actualizando estado de prospects_to_secure {}")
                    update_notified(contrato_solicitud=str(inquilino.contrato_solicitud) + "i", status=True)
                    update_notified(contrato_solicitud=str(propietario.contrato_solicitud) + "p", status=True)
            print(result)


class DataNotificationpLibertador(BaseModel):
    name: str  # "nombre_propietario"
    document: str  # "numero_documento"
    phone: str  # "cel_prop"
    real_state: str  # "inmobiliaria"


def shipment_new_prospect_from_libertador(phones: List[str], data: DataNotificationpLibertador):
    url = "https://alquiventasback.bonett.chat/gupshup-send-templates"
    headers = {"Content-Type": "application/json"}

    result = []

    for phone in phones:
        payload = {
            "app": "laestrellaalquiventas",
            "securekey": "sk_e570ebcf60a548b0bc1de18186d3b78c",
            "template": [
                {
                    "id": "8a17afd9-6a80-449c-8095-aad2fa8293cd",
                    "params": [
                        data.name,  # nombre_propietario
                        data.document,  # numero_documento
                        data.phone,  # cel_prop
                        data.real_state,  # inmobiliaria
                    ],
                }
            ],
            "localid": "new_inq_softseg",
            "IntegratorUser": "0",
            "message": [],
            "number": phone,
        }

        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload)
            logger.info(response.text)
            result.append(response.status_code)
            time.sleep(5)
            print(f"Codigo de respuesta del envio: {response.status_code}")
            print(f"Resultado del envio: {response.text}")

    return result


def notify_prospect_from_libertador():
    records = select_not_notified(source="libertador")
    for record in records:
        record_ = DataNotificationpLibertador(name=record.nombres, document=record.numero_documento, phone=record.telefono, real_state=record.real_state)

        result = shipment_new_prospect_from_libertador(PHONES, record_)

        if result and len(result) > 0:
            if 200 in result:
                print("mensaje enviado, actualizando estado de prospects_to_secure {}")
                update_notified(contrato_solicitud=str(record.contrato_solicitud), status=True)


if __name__ == "__main__":
    # phone_advisers_numbers = ["573103738772", "573103555742"]
    # results = shipment_message_customers_libertador()
    # print(f"{results=}")

    phones_advisers = ["573103555742", "573006538383", "573013853937"]
    data_customers = [["juan camilo villa", "573103555742"], ["juanes", "573103738772"]]
    shipment_message_owner_softin(phones_advisers, data_customers, "castillo")

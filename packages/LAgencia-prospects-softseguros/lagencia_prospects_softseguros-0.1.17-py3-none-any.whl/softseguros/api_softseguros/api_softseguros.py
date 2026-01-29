"""
Módulo para interactuar con la API de Softseguros.
Proporciona clases y funciones para la gestión de clientes y categorías en la plataforma Softseguros,
incluyendo la creación y consulta de clientes, y la obtención de categorías disponibles.
"""
# https://app.softseguros.com/docs/cliente

import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv
from loguru import logger

from softseguros.api_softseguros.models_requests import RequestsCreateCustomerSoftseguros

load_dotenv()


class ServiceAPISoftSeguros:
    """
    Cliente para interactuar con la API de Softseguros.

    Proporciona métodos para crear y consultar clientes, así como obtener
    información sobre las categorías disponibles en el sistema.
    """

    def __init__(self, username: str, password: str) -> None:
        """
        Inicializa el cliente de la API con las credenciales proporcionadas.
        """
        self.auth = httpx.BasicAuth(username=username, password=password)
        self.session = httpx.Client(auth=self.auth)

    def create_customer(self, payload_create_client: RequestsCreateCustomerSoftseguros) -> Dict[str, Any]:
        """
        Crea un nuevo cliente en Softseguros con los datos proporcionados.
        """
        url_create_client = "https://app.softseguros.com/api/cliente/"
        payload = payload_create_client.model_dump(mode="json")
        print(f"{payload=}")
        try:
            response = self.session.post(url=url_create_client, json=payload)
            logger.info(f"{response.status_code=}")
            if response.status_code == 200:
                logger.info(f"Cliente creado exitosamente -> id: {response.json().get('id')}, cc: {response.json().get('numero_documento')}")
                return {"status": True, "message": "Solicitud realizada exitosamente", "data": response.json()}

            elif "Ya hay un cliente registrado con este número de documento" in response.text:
                logger.info(f"Ya hay un cliente registrado con este número de documento {payload_create_client.numero_documento}: {response.status_code=}: {response.text=}")
                return {"status": True, "message": "Ya hay un cliente registrado con este número de documento", "data": None}

            logger.error(f"Ha ocurrido un error al procesar la solicitud: {response.status_code=}: {response.text=}")
            return {"status": False, "message": "Ha ocurrido un error al procesar la solicitud", "data": None}

        except Exception as ex:
            logger.error(f"Ha ocurrido un error inesperado al intentar crear: {str(ex)}")
            return {"status": False, "message": "Error inesperado", "data": None}

    def update_customer_by_id(self, client_id, payload):
        if client_id:
            update_resp = self.session.put(f"https://app.softseguros.com/api/cliente/{client_id}/", json=payload)
            logger.info("Status:", update_resp.status_code)
            logger.info("Body:", update_resp.text)
            update_resp.raise_for_status()
            return update_resp

        logger.warning("No se puede hacer la actualizacion para el cliente ya que no cuenta con un valor de cliente_id")
        raise

    def fetch_customer(self, numero_documento: str) -> Dict[str, Any]:
        """
        Consulta un cliente por su número de documento.
        """
        logger.debug(f"Consultando cliente con documento: {numero_documento}")
        url_fetch_customer = "https://app.softseguros.com/api/cliente/listar_cliente_por_documento/"
        params = {"numero_documento": numero_documento}

        response = self.session.get(url=url_fetch_customer, params=params)
        logger.debug(f"Código de respuesta: {response.status_code}")
        if response.status_code == 404:
            logger.error(f"Ha ocurrido un error al consultar el cliente: {response.status_code=}: {response.text=}")
            return {}
        if response.status_code == 200:
            logger.info(f"Cliente consultado exitosamente -> ID: {response.json().get('id')}")
            return response.json()

        raise ("Error inesperado")

    def fetch_category(self) -> Dict[str, Any]:
        """
        Obtiene la lista de categorías disponibles en Softseguros.
        """
        url_fetch_category = "https://app.softseguros.com/api/categoria/"

        response = self.session.get(url=url_fetch_category)
        if response.status_code == 200:
            logger.info("Categorías consultadas exitosamente")
            logger.debug(f"Categorías obtenidas: {len(response.json())}")
            return response.json()
        logger.error(f"Ha ocurrido un error al consultar las categorías: {response.status_code=}: {response.text=}")

        return {}

    def upda_categoies_by_customer(self, numero_documento: str, nuevas_categorias_ids: List[str]):
        # 1. Obtener datos actuales del cliente
        data = self.fetch_customer(numero_documento)
        print(f"{numero_documento=}")
        client_id = data.get("id")

        # 2. Obtener IDs de categorías actuales (solo IDs)
        categorias_actuales = [c["id"] for c in data.get("categorias", [])]
        logger.info("Categorías actuales (ids):", categorias_actuales)


        # 3. Unir las categorías actuales con las nuevas (sin duplicados)
        categorias_finales = set(categorias_actuales)  # para evitar duplicados
        categorias_finales.update(nuevas_categorias_ids)
        categorias_finales = set(categorias_finales)
        logger.info(f"{categorias_finales=}")

        # 4. Construir el payload para actualizar el cliente
        payload = {
            "tipo_documento": data["tipo_documento"],
            "numero_documento": data["numero_documento"],
            "nombres": data["nombres"],
            "apellidos": data.get("apellidos", ""),
            "genero": data["genero"],
            "fecha_nacimiento": data["fecha_nacimiento"],
            "direccion": data["direccion"],
            "telefono": data["telefono"],
            "celular": data["celular"],
            "email": data["email"],
            "ids_categorias": ",".join(str(cid) for cid in categorias_finales),
        }

        # # 5. Actualizar el cliente
        update_resp = self.update_customer_by_id(client_id=client_id, payload=payload)

        cliente_actualizado = update_resp.json()
        logger.info("Cliente actualizado:", cliente_actualizado["id"])
        logger.info("Categorías nuevas:", cliente_actualizado.get("categorias", []))
        return update_resp


if __name__ == "__main__":
    USERNAME = os.getenv("USERNAME_SOFTSEGUROS")
    PASSWORD = os.getenv("USERNAME_PASSWORD_SOFTSEGUROS")

    # observations = Observations(canon=1800000)
    # clente_test = RequestsCreateCustomer(numero_documento="100723254405", nombres="nombre_1 nombre_2", apellidos="apellido_1 apellido_2", direccion="diagonal 40 32 32", telefono="3103555744", celular="3103555744", email="nombre_1@gmail.com", ids_categorias=[47205], observations=observations)

    api = ServiceAPISoftSeguros(username=USERNAME, password=PASSWORD)
    # result = api.create_customer(clente_test)
    # result = api.fetch_customer(numero_documento="100723254405")

    # result = api.fetch_category()
    # print(f"{result=}")

    document = "1035861280"
    NUEVAS_CATEGORIAS_IDS = [47205, 47202]
    api.upda_categoies_by_customer(numero_documento=document, nuevas_categorias_ids=NUEVAS_CATEGORIAS_IDS)

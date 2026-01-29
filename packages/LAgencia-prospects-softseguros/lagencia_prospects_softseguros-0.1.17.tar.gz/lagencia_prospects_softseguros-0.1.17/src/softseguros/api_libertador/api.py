"""
Módulo para interactuar con la API de Libertador Seguros.

Este módulo proporciona clases y funciones para:
- Autenticación OAuth2 con el servicio de Libertador
- Consulta de solicitudes individuales y por rango de fechas
- Manejo de respuestas y errores de la API
- Modelos de datos validados con Pydantic

Las principales clases son:
- OAuth2BearerAuth: Maneja la autenticación OAuth2
- APILibertador: Cliente base para interactuar con la API
- ServiceAPILibertador: Implementación de alto nivel del cliente

Uso típico:
    service = ServiceAPILibertador(client_id="id", client_secret="secret")
    data = RequestDataUnique(solicitud="123456")
    result = service.data_unique(data=data)
"""

import asyncio
import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Generator, List, Optional

import httpx
from dotenv import load_dotenv
from loguru import logger

from softseguros.api_libertador.codes_status_api import status_code_http_data_full, status_code_http_data_unique
from softseguros.api_libertador.custom_execptions_api import ErrorClientId, ErrorClientSecret, ErrorCredentials, ErrorStartDateEqualsEndDate, ErrorStartDateGreaterThanEndDate
from softseguros.api_libertador.models_request import RequestDataFull, RequestDataUnique, State
from softseguros.api_libertador.models_response import ResponseDataFull, ResponseDataUnique

load_dotenv()


# -----------------------------
# Clase OAuth2BearerAuth
# -----------------------------


class OAuth2BearerAuth(httpx.Auth):
    """Clase para autenticación OAuth2 usando bearer token."""

    def __init__(self, client_id: str, client_secret: str):
        self.token: Optional[str] = None
        self.expiry: Optional[datetime] = None
        self.client_id = client_id
        self.client_secret = client_secret
        self._lock = threading.RLock()

        if not self.client_id:
            raise ErrorClientId("El client_id no puede estar vacío")

        if not self.client_secret:
            raise ErrorClientSecret("El client_secret no puede estar vacío")

    def _get_token(self):
        """Obtiene un nuevo token desde Cognito."""
        logger.info("Solicitando nuevo token OAuth2...")
        url = "https://inmobiliarias-prod-api.auth.us-east-1.amazoncognito.com/oauth2/token"

        payload = {
            "grant_type": os.getenv("GRANT_TYPE"),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            with httpx.Client() as session:
                response = session.post(url, headers=headers, data=payload)
                response.raise_for_status()

                data = response.json()
                if "access_token" not in data or "expires_in" not in data:
                    raise ErrorCredentials("Token response malformado: faltan campos")

                self.token = data["access_token"]
                self.expiry = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"] - 30)
                logger.info("Token OAuth2 obtenido exitosamente")

        except httpx.HTTPError as e:
            logger.critical(f"Error de red al obtener token: {e}")
            raise ErrorCredentials(f"Error de red al obtener token: {e}")

        except KeyError as e:
            logger.critical(f"Token response malformado: falta {e}")
            raise ErrorCredentials(f"Token response malformado: falta {e}")

    def _ensure_valid_token(self):
        """Verifica si el token sigue siendo válido; si no, lo renueva."""
        with self._lock:
            if self.token is None or self.expiry is None or datetime.now(timezone.utc) >= self.expiry:
                logger.info("Token expiro o no existe, obteniendo nuevo token...")
                self._get_token()

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, None, None]:
        """Se ejecuta antes de cada request httpx para añadir el token."""
        self._ensure_valid_token()
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


# -----------------------------
# Consumo de endpoints
# -----------------------------


class EndPointsAPILibertador:
    """Clase para consumir la API de Libertador."""

    def __init__(self, auth: OAuth2BearerAuth):
        self.auth = auth

        self.client = httpx.Client(auth=self.auth, headers={"Content-Type": "application/json"})

    def data_unique(self, data: RequestDataUnique) -> ResponseDataUnique:
        """Consulta data_unique para un numero de solicitud específica.
        # endpoint data_unique
        # codigoResultado
        # 03 negada, 37 mora
        # 02 aplazada
        # 01 asegurable
        # 500 "INFORMACION DE SOLICITANTES CONFIRMADA, PENDIENTE VALIDACION  BIOMETRICA" ¿firma auco?
        """
        url = f"https://9mbvccw8gj.execute-api.us-east-1.amazonaws.com/prod/portal/api/data/v2/solicitud/{data.solicitud}"

        try:
            response = self.client.get(url)
            response.raise_for_status()
            message = status_code_http_data_unique.get(response.status_code, "Error desconocido")

            logger.info(f"Request data_unique: {data.solicitud} -> HTTP {response.status_code}")

            if response.status_code == 200:
                return ResponseDataUnique(status=True, data=response.json(), message=message)
            return ResponseDataUnique(status=False, data=None, message=message)

        except httpx.HTTPStatusError as exc:
            logger.error(f"Error HTTP: {exc}")
            return ResponseDataUnique(status=False, data=None, message="Error HTTP")
        except httpx.RequestError as exc:
            logger.error(f"Error de conexión al consultar solicitud: {exc}")
            return ResponseDataUnique(status=False, data=None, message="Error de conexión al consultar solicitud")
        except Exception as exc:
            logger.error(f"Error inesperado: {exc}")
            return ResponseDataUnique(status=False, data=None, message="Error inesperado")

    def data_full(self, data: RequestDataFull) -> ResponseDataFull:
        """Consulta data_full para un rango de fechas y estado específico."""
        if data.fechaInicio == data.fechaFin:
            raise ErrorStartDateEqualsEndDate()

        if data.fechaInicio > data.fechaFin:
            raise ErrorStartDateGreaterThanEndDate()

        url = "https://9mbvccw8gj.execute-api.us-east-1.amazonaws.com/prod/portal/api/data/v2/obtenerSolicitudes"
        response = self.client.post(url, json=data.model_dump(mode="json"), timeout=60)
        try:
            response.raise_for_status()
            message = status_code_http_data_full.get(response.status_code, "Error desconocido")

            logger.info(f"Request data_full filtrada por: {data} -> HTTP {response.status_code}")
            if response.status_code == 200:
                return ResponseDataFull(status=True, data=response.json(), message=message)

            return ResponseDataFull(status=False, data=None, message=message + " -> " + response.text)

        except httpx.HTTPStatusError as exc:
            logger.error(f"Error HTTP: {exc}")
            return ResponseDataFull(status=False, data=None, message="Error HTTP")
        except httpx.RequestError as exc:
            logger.error(f"Error de conexión al consultar rango de fechas: {exc}")
            return ResponseDataFull(status=False, data=None, message="Error de conexión al consultar rango de fechas")
        except Exception as exc:
            logger.error(f"Error inesperado: {exc}")
            return ResponseDataFull(status=False, data=None, message="Error inesperado")

    def request_a_one_day_range(self, state: State = State.NA) -> ResponseDataFull:
        """
        Realiza una consulta de datos para el rango del día anterior al actual.

        Este método es una utilidad que simplifica la consulta de datos para un período
        de 24 horas, desde el día anterior hasta hoy.

        Args:
            state: Estado de las solicitudes a consultar (default: State.NA)

        Returns:
            ResponseDataFull: Respuesta de la API con los datos encontrados

        Example:
            ```python
            api = APILibertador(auth)
            # Consultar aprobados del último día
            result = api.request_a_one_day_range(state=State.APROBADA)
            ```
        """
        now = datetime.now().date()
        yesterday = now - timedelta(days=1)

        logger.info(f"Consultando solicitudes {state.value} entre {yesterday} y {now}")

        data = RequestDataFull(estado=state, fechaInicio=yesterday, fechaFin=now)
        return self.data_full(data=data)


# -----------------------------
# Servicio para interactuar con el api libertador
# -----------------------------


class ServiceAPILibertador(EndPointsAPILibertador):
    """
    Implementación de alto nivel del cliente API de Libertador.

    Esta clase simplifica la creación de un cliente API de Libertador al manejar
    automáticamente la autenticación OAuth2 usando las credenciales proporcionadas.

    Attributes:
        client_id: ID del cliente para autenticación OAuth2
        client_secret: Secret del cliente para autenticación OAuth2

    Example:
        ```python
        service = ServiceAPILibertador(
            client_id="mi_client_id",
            client_secret="mi_client_secret"
        )
        data = RequestDataUnique(solicitud="123456")
        result = service.data_unique(data=data)
        ```
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        """
        Inicializa el servicio con las credenciales OAuth2.

        Args:
            client_id: ID del cliente para autenticación
            client_secret: Secret del cliente para autenticación

        Raises:
            ErrorClientId: Si client_id está vacío
            ErrorClientSecret: Si client_secret está vacío
        """
        self.client_id = client_id
        self.client_secret = client_secret
        auth = OAuth2BearerAuth(client_id=self.client_id, client_secret=self.client_secret)
        super().__init__(auth=auth)
        logger.info(f"Servicio API Libertador inicializado para client_id: {client_id[:8]}...")


async def main() -> List[ResponseDataUnique]:
    """
    Función de ejemplo que demuestra el uso asíncrono del servicio.

    Returns:
        List[ResponseDataUnique]: Lista de respuestas de las solicitudes consultadas

    Raises:
        ErrorClientId: Si no se encuentra CLIENT_ID_ESTRELLA en variables de entorno
        ErrorClientSecret: Si no se encuentra CLIENT_SECRET_ESTRELLA en variables de entorno
    """
    client_id = os.getenv("CLIENT_ID_ESTRELLA")
    client_secret = os.getenv("CLIENT_SECRET_ESTRELLA")

    if not client_id or not client_secret:
        logger.error("Credenciales no encontradas en variables de entorno")
        raise ValueError("CLIENT_ID_ESTRELLA y CLIENT_SECRET_ESTRELLA son requeridos")

    service_libertador = ServiceAPILibertador(client_id=client_id, client_secret=client_secret)
    logger.info("Iniciando consultas asíncronas de prueba...")

    data_1 = RequestDataUnique(solicitud="11725333")
    data_2 = RequestDataUnique(solicitud="11197128")

    tasks = [service_libertador.data_unique(data=task_data) for task_data in [data_1, data_2]]
    results = await asyncio.gather(*tasks)  # Corregido: * en lugar de **

    logger.info(f"Consultas completadas. Resultados obtenidos: {len(results)}")
    return results


if __name__ == "__main__":
    client_id = os.getenv("CLIENT_ID_ESTRELLA")
    client_secret = os.getenv("CLIENT_SECRET_ESTRELLA")

    service_libertador = ServiceAPILibertador(client_id=client_id, client_secret=client_secret)

    data = RequestDataUnique(solicitud="11725333")
    result = service_libertador.data_unique(data=data)
    print(result)

    data = RequestDataFull(estado=State.APROBADA, fechaInicio=datetime(2025, 11, 20), fechaFin=datetime(2025, 11, 24))
    result = service_libertador.data_full(data=data)
    print(result)

    # result = service_libertador.request_a_one_day_range()
    # print(result)

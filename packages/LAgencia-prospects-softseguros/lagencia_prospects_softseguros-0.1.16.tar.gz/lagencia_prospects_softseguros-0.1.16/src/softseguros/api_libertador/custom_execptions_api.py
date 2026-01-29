from loguru import logger

# -----------------------------
# Excepciones personalizadas
# -----------------------------


class ErrorCredentials(Exception):
    """Excepción lanzada cuando hay un error de credenciales OAuth2."""

    def __init__(self, message="Error en credenciales de autenticación"):
        super().__init__(message)
        logger.error(f"ErrorCredentials: {message}")


class ErrorClientId(Exception):
    """Excepción lanzada cuando client_id no está definido o es inválido."""

    def __init__(self, message="Error: client_id no definido"):
        super().__init__(message)
        logger.error(f"ErrorClientId: {message}")


class ErrorClientSecret(Exception):
    """Excepción lanzada cuando client_secret no está definido o es inválido."""

    def __init__(self, message="Error: client_secret no definido"):
        super().__init__(message)
        logger.error(f"ErrorClientSecret: {message}")


class ErrorStartDateEqualsEndDate(Exception):
    """Excepción lanzada cuando fecha de inicio y fin son iguales."""

    def __init__(self, message="Error: fecha inicio igual a fecha fin"):
        super().__init__(message)
        logger.error(f"ErrorStartDateEqualsEndDate: {message}")


class ErrorStartDateGreaterThanEndDate(Exception):
    """Excepción lanzada cuando fecha de inicio es mayor que fecha fin."""

    def __init__(self, message="Error: fecha inicio mayor a fecha fin"):
        super().__init__(message)
        logger.error(f"ErrorStartDateGreaterThanEndDate: {message}")

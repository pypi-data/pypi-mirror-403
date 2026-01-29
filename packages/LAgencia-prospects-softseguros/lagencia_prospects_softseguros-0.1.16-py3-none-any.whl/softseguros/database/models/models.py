from sqlalchemy import Boolean, Column, Float, Integer, String, Text, UnicodeText, BigInteger

from softseguros.database.config_db import BaseSoftseguros
from softseguros.database.config_db import engine as engine_softseguros


class ProspectsSoftin(BaseSoftseguros):
    __tablename__= "prospects_softin"
    contrato = Column(String(20), primary_key=True)
    informacion_contrato_Inmueble = Column(UnicodeText, nullable=True)
    informacion_propietario = Column(UnicodeText, nullable=True)
    informacion_inquilino = Column(UnicodeText, nullable=True)
    asignaciones_y_operaciones = Column(UnicodeText, nullable=True)
    real_state = Column(String(20), nullable=True)
    created_in_softseguros = Column(Boolean, default=False)


class ProspectsLibertador(BaseSoftseguros):
    __tablename__ = "prospects_libertador"

    solicitud = Column(String(20), primary_key=True)

    poliza = Column(String(50), nullable=False)

    nombreInquilino = Column(String(200), nullable=False)
    tipoIdentificacion = Column(String(10), nullable=False)
    identificacionInquilino = Column(String(50), nullable=False)

    fechaExpedicion = Column(String(20), nullable=True)

    ingresos = Column(Integer, nullable=True)

    estadoGeneral = Column(String(50), nullable=True)
    direccionInmueble = Column(String(255), nullable=True)
    correoInquilino = Column(String(255), nullable=True)
    telefonoInquilino = Column(String(50), nullable=True)

    canon = Column(BigInteger, nullable=True)

    destinoInmueble = Column(String(100), nullable=True)
    ciudadInmueble = Column(String(100), nullable=True)

    fechaRadicacion = Column(String(20), nullable=True)
    fechaResultado = Column(String(20), nullable=True)

    cuota = Column(String(20), nullable=True)
    nombreAsesor = Column(String(200), nullable=True)
    correoAsesor = Column(String(255), nullable=True)

    source = Column(String(20), nullable=True)


class ProspectsToSecure(BaseSoftseguros):
    __tablename__= "prospects_to_secure"

    contrato_solicitud = Column(String(20), primary_key=True)

    tipo_documento = Column(String(20), nullable=True, default="cedula")
    numero_documento = Column(String(50), nullable=False)

    nombres = Column(String(200), nullable=True)
    genero = Column(String(20), nullable=True, default="MASCULINO")

    direccion = Column(String(255), nullable=True)
    telefono = Column(String(30), nullable=True)
    celular = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)

    departamento = Column(String(100), nullable=True, default="ANTIOQUIA")
    ciudad = Column(String(100), nullable=True)

    ids_categorias = Column(String(255), nullable=True)

    fecha_expedicion_cedula = Column(String(20), nullable=True)

    ingreso_mensual = Column(Float, nullable=True)

    observaciones = Column(Text, nullable=True)

    type = Column(String(30), nullable=True)
    source = Column(String(30), nullable=True)
    real_state = Column(String(30), nullable=True)
    created_in_crm= Column(Boolean, default=False)
    notified= Column(Boolean, default=False)


def create_schemas_segutos_bolivar():
    print("Creando esquemas seguros_bolivar...")
    BaseSoftseguros.metadata.create_all(bind=engine_softseguros)
    print(BaseSoftseguros.metadata.tables.keys())
    print("✅ Esquemas creados correctamente")
    print(f"*** {engine_softseguros.url}")

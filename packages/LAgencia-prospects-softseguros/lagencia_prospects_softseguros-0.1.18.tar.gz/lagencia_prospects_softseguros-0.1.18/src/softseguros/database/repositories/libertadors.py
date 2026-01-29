from typing import List, Optional

from sqlalchemy import select

from softseguros.database.config_db import get_session_seguros_bolivar
from softseguros.database.models.models import ProspectsLibertador


def insert_records(records: List[ProspectsLibertador]):
    with get_session_seguros_bolivar() as session:
        session.add_all(records)
        session.commit()


def upsert_records(records: List[ProspectsLibertador]):
    with get_session_seguros_bolivar() as session:
        for record in records:
            session.merge(record)
        session.commit()


def select_postponed_records_liberator(source: str) -> List[Optional[ProspectsLibertador]]:
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsLibertador).where(
            ProspectsLibertador.source == source,
            ProspectsLibertador.estadoGeneral.in_(["APLAZADA", "APLAZADO-NUBE"]),
        )

        result = session.scalars(stmt).all()
        return result
    return []


def select_approved_records_liberator() -> List[Optional[ProspectsLibertador]]:
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsLibertador).where(
            ProspectsLibertador.estadoGeneral.in_(["APROBADA"]),
        )

        result = session.scalars(stmt).all()
        return result
    return []


def select_approved_records_liberator_by_source(source: str) -> List[Optional[ProspectsLibertador]]:
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsLibertador).where(
            ProspectsLibertador.source == source,
            ProspectsLibertador.estadoGeneral.in_(["APROBADA"]),
        )

        result = session.scalars(stmt).all()
        return result
    return []


def update_state_record_libertador(solicitud: int, new_state: str) -> Optional[ProspectsLibertador]:
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsLibertador).where(ProspectsLibertador.solicitud == solicitud)
        record: ProspectsLibertador = session.scalars(stmt).first()
        if record:
            record.estadoGeneral = new_state
            session.commit()
            return record
    return None

from typing import List, Optional

from sqlalchemy import select

from softseguros.database.config_db import get_session_seguros_bolivar
from softseguros.database.models.models import ProspectsToSecure


def insert_records(records: List[ProspectsToSecure]):
    with get_session_seguros_bolivar() as session:
        session.add_all(records)
        session.commit()


def upsert_records(records: List[ProspectsToSecure]):
    with get_session_seguros_bolivar() as session:
        for record in records:
            session.merge(record)
        session.commit()


def select_those_not_created_in_the_crm() -> List[Optional[ProspectsToSecure]]:
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsToSecure).where(ProspectsToSecure.created_in_crm == False)

        result = session.scalars(stmt).all()
        return result
    return []


def update_created_in_crm(contrato_solicitud: str, status: bool):
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsToSecure).where(ProspectsToSecure.contrato_solicitud == contrato_solicitud)
        prospect = session.scalars(stmt).first()
        prospect.created_in_crm = status
        session.commit()

def select_not_notified(source: str) -> List[Optional[ProspectsToSecure]]:
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsToSecure).where(ProspectsToSecure.source==source).where(ProspectsToSecure.notified == False)

        result = session.scalars(stmt).all()
        return result
    return []

def update_notified(contrato_solicitud: str, status: bool):
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsToSecure).where(ProspectsToSecure.contrato_solicitud == contrato_solicitud)
        prospect = session.scalars(stmt).first()
        prospect.notified = status
        session.commit()

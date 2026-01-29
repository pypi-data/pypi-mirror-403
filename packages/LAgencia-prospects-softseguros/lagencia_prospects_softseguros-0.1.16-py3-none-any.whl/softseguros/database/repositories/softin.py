from typing import List

from sqlalchemy import desc, select

from softseguros.database.config_db import get_session_seguros_bolivar
from softseguros.database.models.models import ProspectsSoftin


def insert_records(records: List[ProspectsSoftin]):
    with get_session_seguros_bolivar() as session:
        session.add_all(records)
        session.commit()


def upsert_records(records: List[ProspectsSoftin]):
    with get_session_seguros_bolivar() as session:
        for record in records:
            session.merge(record)
        session.commit()


def select_last_contract(real_state: str) -> int:
    match real_state:
        case "estrella":
            default = 5630
        case "castillo":
            default = 34280
        case "villacruz":
            default = 29070
        case _:
            raise ()

    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsSoftin.contrato).where(ProspectsSoftin.real_state == real_state).order_by(desc(ProspectsSoftin.contrato))
        result = session.scalars(statement=stmt).first()
        return result if result else default
    return default


def select_prospects_softin_not_notified_by_real_state(real_state: str):
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsSoftin).where(ProspectsSoftin.real_state == real_state).where(ProspectsSoftin.created_in_softseguros == False)
        result = session.scalars(statement=stmt).all()
        return result


def select_prospects_softin_not_notified():
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsSoftin).where(ProspectsSoftin.created_in_softseguros == False)
        result = session.scalars(statement=stmt).all()
        return result


def update_field_created_in_softseguros_from_prospects_softin(id: int, new_state: bool):
    with get_session_seguros_bolivar() as session:
        stmt = select(ProspectsSoftin).where(ProspectsSoftin.id == id)
        prospect = session.scalars(statement=stmt).first()
        prospect.created_in_softseguros = new_state
        session.commit()

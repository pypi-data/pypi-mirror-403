from __future__ import annotations

from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import func
from sqlmodel import SQLModel, select

from healthdatalayer.config.db import engines, get_session

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, tenant: str, model: Type[T]):
        self.tenant = tenant
        self.model = model
        if tenant not in engines:
            raise ValueError(f"Tenant {tenant} is not configured")

    def _get_session(self):
        return get_session(self.tenant)

    def _has_is_active(self) -> bool:
        return hasattr(self.model, "is_active")

    def _apply_active_filter(self, statement, active_only: bool):
        if active_only and self._has_is_active():
            return statement.where(self.model.is_active == True)
        return statement

    def create_command(self, entity: T) -> T:
        with self._get_session() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def get_by_id_command(self, entity_id: UUID) -> Optional[T]:
        with self._get_session() as session:
            return session.get(self.model, entity_id)

    def list_all_command(self, active_only: bool = True) -> List[T]:
        with self._get_session() as session:
            statement = select(self.model)
            statement = self._apply_active_filter(statement, active_only)
            results = session.exec(statement)
            return results.all()

    def update_command(self, entity: T) -> T:
        with self._get_session() as session:
            db_entity = session.merge(entity)
            session.commit()
            session.refresh(db_entity)
            return db_entity

    def delete_command(self, entity_id: UUID, soft_delete: bool = True) -> bool:
        with self._get_session() as session:
            db_entity = session.get(self.model, entity_id)
            if not db_entity:
                return False

            if soft_delete and self._has_is_active():
                db_entity.is_active = False
                session.add(db_entity)
            else:
                session.delete(db_entity)

            session.commit()
            return True

    def count_command(self, active_only: bool = True) -> int:
        with self._get_session() as session:
            statement = select(func.count()).select_from(self.model)
            statement = self._apply_active_filter(statement, active_only)
            return int(session.exec(statement).one())

    def exists_by_id_command(self, entity_id: UUID) -> bool:
        with self._get_session() as session:
            return session.get(self.model, entity_id) is not None

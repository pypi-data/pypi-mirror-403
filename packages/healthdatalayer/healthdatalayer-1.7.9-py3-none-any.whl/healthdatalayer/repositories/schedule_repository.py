from typing import List
from uuid import UUID

from sqlmodel import select

from healthdatalayer.models import Schedule
from healthdatalayer.repositories.base_repository import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, tenant: str):
        super().__init__(tenant, Schedule)

    def list_by_collaborator_speciality_id_command(
        self,
        collaborator_speciality_id: UUID,
        active_only: bool = True,
    ) -> List[Schedule]:
        with self._get_session() as session:
            statement = select(Schedule).where(
                Schedule.collaborator_speciality_id == collaborator_speciality_id
            )
            statement = self._apply_active_filter(statement, active_only)
            results = session.exec(statement)
            return results.all()

    def delete_command(
        self,
        schedule_id: UUID,
        collaborator_speciality_id: UUID | None = None,
        soft_delete: bool = True,
    ) -> bool:
        with self._get_session() as session:
            if collaborator_speciality_id is not None:
                db_schedule = session.get(
                    Schedule, (schedule_id, collaborator_speciality_id)
                )
            else:
                statement = select(Schedule).where(Schedule.schedule_id == schedule_id)
                db_schedule = session.exec(statement).first()

            if not db_schedule:
                return False

            if soft_delete and self._has_is_active():
                db_schedule.is_active = False
                session.add(db_schedule)
            else:
                session.delete(db_schedule)

            session.commit()
            return True

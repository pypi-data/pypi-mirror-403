from typing import List
from uuid import UUID

from sqlmodel import select

from healthdatalayer.models import MicrobiologyRequest
from healthdatalayer.repositories.base_repository import BaseRepository


class MicrobiologyRequestRepository(BaseRepository[MicrobiologyRequest]):
    def __init__(self, tenant: str):
        super().__init__(tenant, MicrobiologyRequest)

    def list_by_request_lab_id_command(self, request_lab_id: UUID, active_only: bool = True) -> List[MicrobiologyRequest]:
        with self._get_session() as session:
            statement = select(MicrobiologyRequest).where(MicrobiologyRequest.request_lab_id == request_lab_id)
            statement = self._apply_active_filter(statement, active_only)
            results = session.exec(statement)
            return results.all()

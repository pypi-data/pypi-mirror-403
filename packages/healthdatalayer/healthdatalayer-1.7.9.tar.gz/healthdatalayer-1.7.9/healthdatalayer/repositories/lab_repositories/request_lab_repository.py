from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from healthdatalayer.models import RequestLab
from healthdatalayer.repositories.base_repository import BaseRepository


class RequestLabRepository(BaseRepository[RequestLab]):
    def __init__(self, tenant: str):
        super().__init__(tenant, RequestLab)

    def _header_options(self):
        return (
            joinedload(RequestLab.client),
            joinedload(RequestLab.collaborator_1),
            joinedload(RequestLab.collaborator_2),
            joinedload(RequestLab.bridge_area_floor_branch),
        )

    def _detail_options(self):
        return (
            selectinload(RequestLab.blood_chemistry_request),
            selectinload(RequestLab.cardiac_vascular_markers_request),
            selectinload(RequestLab.coagulation_hemostasis_request),
            selectinload(RequestLab.cytochemical_bacteriological_liquids_request),
            selectinload(RequestLab.gases_electrolytes_request),
            selectinload(RequestLab.hematology_request),
            selectinload(RequestLab.hormones_request),
            selectinload(RequestLab.inmunology_infectious_request),
            selectinload(RequestLab.immunosuppressants_request),
            selectinload(RequestLab.microbiology_request),
            selectinload(RequestLab.molecular_biology_genetics_request),
            selectinload(RequestLab.serology_request),
            selectinload(RequestLab.service_priority_attention_request),
            selectinload(RequestLab.stool_request),
            selectinload(RequestLab.transfusion_medicine_request),
            selectinload(RequestLab.tumor_markers_request),
            selectinload(RequestLab.urine_request),
            selectinload(RequestLab.therapeutic_drug_levels_request),
        )

    def _apply_load_options(self, statement, load_header: bool, load_details: bool):
        options = []
        if load_header:
            options.extend(self._header_options())
        if load_details:
            options.extend(self._detail_options())
        if options:
            return statement.options(*options)
        return statement

    def get_by_id_command(
        self,
        request_lab_id: UUID,
        load_header: bool = False,
        load_details: bool = False,
        active_only: bool = True,
    ) -> Optional[RequestLab]:
        with self._get_session() as session:
            if not load_header and not load_details:
                return session.get(RequestLab, request_lab_id)

            statement = select(RequestLab).where(RequestLab.request_lab_id == request_lab_id)
            statement = self._apply_active_filter(statement, active_only)
            statement = self._apply_load_options(statement, load_header, load_details)
            return session.exec(statement).first()
        
    def list_all_command(
        self,
        active_only: bool = True,
        load_header: bool = False,
        load_details: bool = False,
    ) -> List[RequestLab]:
        with self._get_session() as session:
            statement = select(RequestLab)
            statement = self._apply_active_filter(statement, active_only)
            statement = self._apply_load_options(statement, load_header, load_details)
            return session.exec(statement).all()

    def list_by_client_id_command(
        self,
        client_id: UUID,
        active_only: bool = True,
        load_header: bool = False,
        load_details: bool = False,
    ) -> List[RequestLab]:
        with self._get_session() as session:
            statement = select(RequestLab).where(RequestLab.client_id == client_id)
            statement = self._apply_active_filter(statement, active_only)
            statement = self._apply_load_options(statement, load_header, load_details)
            results = session.exec(statement)
            return results.all()

    def list_by_collab_id_1_command(
        self,
        collab_id_1: UUID,
        active_only: bool = True,
        load_header: bool = False,
        load_details: bool = False,
    ) -> List[RequestLab]:
        with self._get_session() as session:
            statement = select(RequestLab).where(RequestLab.collab_id_1 == collab_id_1)
            statement = self._apply_active_filter(statement, active_only)
            statement = self._apply_load_options(statement, load_header, load_details)
            results = session.exec(statement)
            return results.all()
        
    def list_by_collab_id_2_command(
        self,
        collab_id_2: UUID,
        active_only: bool = True,
        load_header: bool = False,
        load_details: bool = False,
    ) -> List[RequestLab]:
        with self._get_session() as session:
            statement = select(RequestLab).where(RequestLab.collab_id_2 == collab_id_2)
            statement = self._apply_active_filter(statement, active_only)
            statement = self._apply_load_options(statement, load_header, load_details)
            results = session.exec(statement)
            return results.all()

    def list_by_sample_collection_date_range_command(
        self,
        start: Optional[datetime],
        end: Optional[datetime],
        active_only: bool = True,
        load_header: bool = False,
        load_details: bool = False,
    ) -> List[RequestLab]:
        with self._get_session() as session:
            statement = select(RequestLab)

            if start is not None:
                statement = statement.where(RequestLab.sample_collection_date >= start)
            if end is not None:
                statement = statement.where(RequestLab.sample_collection_date <= end)

            statement = self._apply_active_filter(statement, active_only)
            statement = self._apply_load_options(statement, load_header, load_details)
            return session.exec(statement).all()

    def list_by_registration_date_range_command(
        self,
        start: Optional[datetime],
        end: Optional[datetime],
        active_only: bool = True,
        load_header: bool = False,
        load_details: bool = False,
    ) -> List[RequestLab]:
        with self._get_session() as session:
            statement = select(RequestLab)

            if start is not None:
                statement = statement.where(RequestLab.registration_date >= start)
            if end is not None:
                statement = statement.where(RequestLab.registration_date <= end)

            statement = self._apply_active_filter(statement, active_only)
            statement = self._apply_load_options(statement, load_header, load_details)
            return session.exec(statement).all()
 

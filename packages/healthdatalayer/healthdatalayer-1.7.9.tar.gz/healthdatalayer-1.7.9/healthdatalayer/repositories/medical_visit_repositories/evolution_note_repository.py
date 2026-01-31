from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID
from sqlmodel import select, text
from sqlalchemy.orm import selectinload,joinedload
from healthdatalayer.config.db import engines, get_session
from healthdatalayer.models import EvolutionNote, MedicalVisit, Px

class EvolutionNoteRepository:
    def __init__(self, tenant: str):
        self.tenant = tenant
        if tenant not in engines:
            raise ValueError(f"Tenant {tenant} is not configured")
        
    def create_command(self, evolution_note: EvolutionNote) -> EvolutionNote:
        with get_session(self.tenant) as session:
            session.add(evolution_note)
            session.commit()
            session.refresh(evolution_note)
            return evolution_note
    
    def get_by_id_command(self, evolution_note_id: UUID, load_relations: bool = False) -> Optional[EvolutionNote]:
        with get_session(self.tenant) as session:
            
            if load_relations:
                statement = select(EvolutionNote).where(EvolutionNote.evolution_note_id == evolution_note_id).options(
                    joinedload(EvolutionNote.medical_visit),
                    joinedload(EvolutionNote.client)
                )
                medical_visit = session.exec(statement).first()
               
                return medical_visit
            else:
                return session.get(EvolutionNote, evolution_note_id)
    
    def list_all_command(self, active_only: bool = True, load_relations: bool = False)->List[EvolutionNote]:
        with get_session(self.tenant) as session:
            statement = select(EvolutionNote)
            
            if active_only:
                statement = statement.where(EvolutionNote.is_active == True)
            
            if load_relations:
                
                statement = select(EvolutionNote).options(
                    joinedload(EvolutionNote.medical_visit),
                    joinedload(EvolutionNote.client)
                )
            
            return session.exec(statement).all()
    
    def get_by_client_id_command(self, client_id: UUID, active_only: bool = True, load_relations: bool = False) -> List[EvolutionNote]:
        with get_session(self.tenant) as session:
            statement = select(EvolutionNote).where(EvolutionNote.client_id == client_id)
            if active_only:
                statement = statement.where(EvolutionNote.is_active == True)
            if load_relations:
                statement = statement.options(
                    joinedload(EvolutionNote.medical_visit),
                    joinedload(EvolutionNote.client)
                )
            
            evolution_notes = session.exec(statement).all()
            return evolution_notes
    
    def get_by_medical_visit_id_command(self, medical_visit_id: UUID, active_only: bool = True, load_relations: bool = False) -> Optional[EvolutionNote]:
        with get_session(self.tenant) as session:
            statement = select(EvolutionNote).where(EvolutionNote.medical_visit_id == medical_visit_id)
            if active_only:
                statement = statement.where(EvolutionNote.is_active == True)
            if load_relations:
                statement = statement.options(
                    joinedload(EvolutionNote.medical_visit),
                    joinedload(EvolutionNote.client)
                )
            
            evolution_notes = session.exec(statement).first()
            return evolution_notes
    
    def update_command(self, evolution_note: EvolutionNote) -> EvolutionNote:
        with get_session(self.tenant) as session:
            existing_evolution_note = session.get(MedicalVisit, evolution_note.evolution_note_id)
            if not existing_evolution_note:
                raise ValueError(f"evolution_note with id {evolution_note.evolution_note_id} does not exist")
            
            for key, value in evolution_note.dict(exclude_unset=True).items():
                setattr(existing_evolution_note, key, value)
            
            bd_evolution_note =  session.merge(existing_evolution_note)
            session.commit()
            session.refresh(bd_evolution_note)
            return bd_evolution_note
        
    def delete_command(self, evolution_note_id: UUID, soft_delete: bool = False)->None:
        with get_session(self.tenant) as session:
            existing_evolution = session.get(EvolutionNote, evolution_note_id)
            if not existing_evolution:
                raise ValueError(f"EvolutionNote with id {evolution_note_id} does not exist")

            if soft_delete:
                existing_evolution.is_active = False
                session.add(existing_evolution)
            else:
                session.delete(existing_evolution)

            session.commit()
import uuid
from datetime import datetime
from typing import Optional,TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
if TYPE_CHECKING:
    from healthdatalayer.models import MedicalVisit
    from healthdatalayer.models import Px

class EvolutionNote(SQLModel, table=True):
    __tablename__ = "evolution_note"
    evolution_note_id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    
    medical_visit_id: Optional[uuid.UUID] = Field(default=None, foreign_key="medical_visit.medical_visit_id")
    medical_visit: Optional["MedicalVisit"] = Relationship(back_populates="evolution_note")
    
    client_id:Optional[uuid.UUID]=Field(default=None,foreign_key="px.client_id")
    client: Optional["Px"] = Relationship()
    
    evolution_date: Optional[datetime] = Field(default=None)
    
    evolution: Optional[str] = Field(default=None)
    
    pharmacotherapy_and_indications: Optional[str] = Field(default=None)
    
    drug_administration_device: Optional[str] = Field(default=None)
    
    is_active: bool = Field(default=True)
import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from healthdatalayer.models.medical_visit.medical_diagnosis import MedicalDiagnosis

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class MolecularBiologyGeneticsRequest(SQLModel, table=True):
    __tablename__ = "molecular_biology_genetics_request"

    molecular_biology_genetics_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="molecular_biology_genetics_request")

    text: Optional[str] = Field(default=None) 

    is_active: bool = Field(default=True)
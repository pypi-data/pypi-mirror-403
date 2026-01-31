import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from healthdatalayer.models.medical_visit.medical_diagnosis import MedicalDiagnosis

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class ServicePriorityAttentionRequest(SQLModel, table=True):
    __tablename__ = "service_priority_attention_request"
    
    service_priority_attention_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="service_priority_attention_request")

    medical_diagnosis_id_1: Optional[uuid.UUID] = Field(default=None, foreign_key="medical_diagnosis.medical_diagnosis_id")
    medical_diagnosis_1: Optional[MedicalDiagnosis] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ServicePriorityAttentionRequest.medical_diagnosis_id_1]"}
    )

    medical_diagnosis_id_2: Optional[uuid.UUID] = Field(default=None, foreign_key="medical_diagnosis.medical_diagnosis_id")
    medical_diagnosis_2: Optional[MedicalDiagnosis] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ServicePriorityAttentionRequest.medical_diagnosis_id_2]"}
    )

    emergency: Optional[bool] = Field(default=None)
    outpatient_clinic: Optional[bool] = Field(default=None)
    hospitalization: Optional[bool] = Field(default=None)

    priority_urgent: Optional[bool] = Field(default=None) 
    priority_routine: Optional[bool] = Field(default=None) 

    specialty: Optional[str] = Field(default=None)
    ward: Optional[str] = Field(default=None)
    bed: Optional[str] = Field(default=None)

    therapeutic_treatment: Optional[str] = Field(default=None) 

    is_active: bool = Field(default=True)

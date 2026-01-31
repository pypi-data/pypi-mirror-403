import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from healthdatalayer.models.medical_visit.medical_diagnosis import MedicalDiagnosis

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class MicrobiologyRequest(SQLModel, table=True):
    __tablename__ = "microbiology_request"

    microbiology_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="microbiology_request")
    
    sample: Optional[str] = Field(default=None)  #MUESTRA
    anatomical_site: Optional[str] = Field(default=None)  #SEDE ANATÓMICA

    culture_and_antibiogram: Optional[bool] = Field(default=None)  #CULTIVO Y ANTIBIOGRAMA
    crystallography: Optional[bool] = Field(default=None)  #CRISTALOGRAFIA
    gram_stain: Optional[bool] = Field(default=None)  #GRAM
    fresh_sample: Optional[bool] = Field(default=None)  #FRESCO

    mycological_study_koh_of: Optional[str] = Field(default=None)  #ESTUDIO MICOLÓGICO (KOH) DE:
    fungal_culture_of: Optional[str] = Field(default=None)  #CULTIVO MICÓTICO DE:

    paragonimus_spp_investigation: Optional[bool] = Field(default=None)  #INVESTIGACIÓN PARAGONIMUS SPP
    histoplasma_spp_investigation: Optional[bool] = Field(default=None)  #INVESTIGACIÓN HISTOPLASMA SPP
    ziehl_neelsen_stain: Optional[bool] = Field(default=None)  #COLORACIÓN ZHIEL-NIELSSEN

    is_active: bool = Field(default=True)
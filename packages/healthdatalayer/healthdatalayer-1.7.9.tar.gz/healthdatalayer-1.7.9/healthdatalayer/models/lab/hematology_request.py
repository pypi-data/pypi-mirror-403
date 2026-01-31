import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class HematologyRequest(SQLModel, table=True):
    __tablename__ = "hematology_request"
    
    hematology_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="hematology_request")

    complete_blood_count: Optional[bool] = Field(default=None)  #BIOMETRIA HEMÁTICA
    hematocrit: Optional[bool] = Field(default=None)  #HEMATOCRITO (HCTO)
    hemoglobin: Optional[bool] = Field(default=None)  #HEMOGLOBINA (HB)
    platelets: Optional[bool] = Field(default=None)  #PLAQUETAS (PLT)
    reticulocytes: Optional[bool] = Field(default=None)  #RETICULOCITOS
    erythrosediment_rate: Optional[bool] = Field(default=None)  #VELOCIDAD DE ERITROSEDIMENTACIÓN
    seric_iron: Optional[bool] = Field(default=None)  #HIERRO SÉRICO
    iron_fixing: Optional[bool] = Field(default=None)  #FIJACIÓN DE HIERRO
    percentage_of_transferrin_saturation: Optional[bool] = Field(default=None)  #PORCENTAJE SATURACIÓN TRANSFERRINA
    transferrin: Optional[bool] = Field(default=None)  #TRANSFERRINA
    ferritin: Optional[bool] = Field(default=None)  #FERRITINA
    erythrocyte_osmotic_fragility: Optional[bool] = Field(default=None)  #FRAGILIDAD OSMÓTICA DE ERITROCITOS
    metabisulfite: Optional[bool] = Field(default=None)  #METABISULFITO
    hematozoan: Optional[bool] = Field(default=None)  #HEMATOZOANOS
    leishmania_research: Optional[bool] = Field(default=None)  #INVESTIGACIÓN DE LEISHMANIA
    eosinophil_in_nasal_mucus: Optional[bool] = Field(default=None)  #EOSINOFILOS EN MUCOSA NASAL
    peripheral_blood_smear: Optional[bool] = Field(default=None)  #FROTIS SANGRE PERIFERICA
    folic_acid: Optional[bool] = Field(default=None)  #ÁCIDO FÓLICO
    vitamin_b12: Optional[bool] = Field(default=None)  #VITAMINA B12

    is_active: bool = Field(default=True)
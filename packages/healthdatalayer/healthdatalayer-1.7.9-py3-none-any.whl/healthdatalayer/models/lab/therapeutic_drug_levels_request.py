import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class TherapeuticDrugLevelsRequest(SQLModel, table=True):
    __tablename__ = "therapeutic_drug_levels_request"

    therapeutic_drug_levels_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="therapeutic_drug_levels_request")

    valproic_acid: Optional[bool] = Field(default=None)  #ÁCIDO VALPROICO
    carbamazepine: Optional[bool] = Field(default=None)  #CARBAMAZEPINA
    phenobarbital: Optional[bool] = Field(default=None)  #FENOBARBITAL
    digoxin: Optional[bool] = Field(default=None)  #DIGOXINA
    phenytoin_sodium: Optional[bool] = Field(default=None)  #FENITOÍNA SÓDICA
    vancomycin: Optional[bool] = Field(default=None)  #VANCOMICINA
    amikacin: Optional[bool] = Field(default=None)  #AMIKACINA
    lithium: Optional[bool] = Field(default=None)  #LITIO

    is_active: bool = Field(default=True)
import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab


class CytochemicalBacteriologicalLiquidsRequest(SQLModel, table=True):
    __tablename__ = "cytochemical_bacteriological_liquids_request"

    cytochemical_bacteriological_liquids_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="cytochemical_bacteriological_liquids_request")

    cerebrospinal_fluid: Optional[bool] = Field(default=None)  #CEFALORRAQUIDEO
    synovial_fluid: Optional[bool] = Field(default=None)  #ARTICULAR / SINOVIAL
    ascitic_peritoneal_fluid: Optional[bool] = Field(default=None)  #ASCÍTICO / PERITONEAL
    pleural_fluid: Optional[bool] = Field(default=None)  #PLEURAL
    pericardial_fluid: Optional[bool] = Field(default=None)  #PERICÁRDICO
    amniotic_fluid: Optional[bool] = Field(default=None)  #LÍQUIDO AMNIÓTICO

    is_active: bool = Field(default=True)
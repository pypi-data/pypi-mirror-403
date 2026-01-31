import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class CoagulationHemostasisRequest(SQLModel, table=True):
    __tablename__ = "coagulation_hemostasis_request"

    coagulation_hemostasis_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="coagulation_hemostasis_request")

    prothrombin_time: Optional[bool] = Field(default=None)  #TIEMPO DE PROTROMBINA (TP)
    partial_thromboplastin_time: Optional[bool] = Field(default=None)  #TIEMPO DE TROMBOPLASTINA PARCIAL (TTP)
    thrombin_time: Optional[bool] = Field(default=None)  #TIEMPO DE TROMBINA (TT)
    inr: Optional[bool] = Field(default=None)  #INR
    coagulation_factor_viii: Optional[bool] = Field(default=None)  #FACTOR COAGULACIÓN VIII
    coagulation_factor_ix: Optional[bool] = Field(default=None)  #FACTOR COAGULACIÓN IX
    von_willebrand_factor: Optional[bool] = Field(default=None)  #FACTOR VON WILLEBRAND
    fibrinogen: Optional[bool] = Field(default=None)  #FIBRINOGENO
    d_dimer: Optional[bool] = Field(default=None)  #DIMERO-D
    identification_of_inhibitors: Optional[bool] = Field(default=None)  #IDENTIFICATION OF INHIBITORS

    is_active: bool = Field(default=True)
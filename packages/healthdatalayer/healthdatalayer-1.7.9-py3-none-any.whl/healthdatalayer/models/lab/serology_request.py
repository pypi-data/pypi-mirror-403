import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab


class SerologyRequest(SQLModel, table=True):
    __tablename__ = "serology_request"

    serology_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="serology_request")

    febrile_agglutinins: Optional[bool] = Field(default=None)  #AGLUTINACIONES FEBRILES
    asto: Optional[bool] = Field(default=None)  #ASTO
    rheumatoid_factor_latex: Optional[bool] = Field(default=None)  #FR-LÁTEX

    dengue_pcr: Optional[bool] = Field(default=None)  #DENGUE (PCR)
    chlamydia_pcr: Optional[bool] = Field(default=None)  #CHLAMYDIA (PCR)

    pepsinogen: Optional[bool] = Field(default=None)  #PEPSINÓGENO
    vdrl: Optional[bool] = Field(default=None)  #VDRL
    pcr_semiquantitative: Optional[bool] = Field(default=None)  #PCR SEMICUANTITATIVA

    malaria_pcr: Optional[bool] = Field(default=None)  #MALARIA (PCR)
    syphilis_pcr: Optional[bool] = Field(default=None)  #SIFILIS (PCR)

    helicobacter_pylori: Optional[bool] = Field(default=None)  #HELICOBACTER PYLORI

    is_active: bool = Field(default=True)
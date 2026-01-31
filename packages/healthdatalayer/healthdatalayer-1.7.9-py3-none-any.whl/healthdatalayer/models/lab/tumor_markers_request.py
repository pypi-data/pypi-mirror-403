import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class TumorMarekersRequest(SQLModel, table=True):
    __tablename__ = "tumor_markers_request"

    tumor_markers_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship()

    cea: Optional[bool] = Field(default=None)  #CEA
    afp: Optional[bool] = Field(default=None)  #AFP

    ca_125: Optional[bool] = Field(default=None)  #CA 125
    ca_15_3: Optional[bool] = Field(default=None)  #CA 15.3
    ca_19_9: Optional[bool] = Field(default=None)  #CA 19.9
    ca_72_4: Optional[bool] = Field(default=None)  #CA 72.4

    psa_free: Optional[bool] = Field(default=None)  #PSA LIBRE
    psa_total: Optional[bool] = Field(default=None)  #PSA TOTAL

    beta2_microglobulin: Optional[bool] = Field(default=None)  #β2 -MICROGLOBULINA

    anti_tpo: Optional[bool] = Field(default=None)  #ANTI-TPO
    anti_tg: Optional[bool] = Field(default=None)  #ANTI-TG
    thyroglobulin: Optional[bool] = Field(default=None)  #TIROGLOBULINA

    he4: Optional[bool] = Field(default=None)  #HE4

    beta_hcg_free: Optional[bool] = Field(default=None)  #B-HCG LIBRE
    beta_hcg_quantitative: Optional[bool] = Field(default=None)  #B-HCG CUANTITATIVA

    is_active: bool = Field(default=True)

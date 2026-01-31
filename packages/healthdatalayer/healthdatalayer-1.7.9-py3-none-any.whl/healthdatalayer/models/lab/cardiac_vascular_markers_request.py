import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab


class CardiacVascularMarkersRequest(SQLModel, table=True):
    __tablename__ = "cardiac_vascular_markers_request"

    cardiac_vascular_markers_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship()

    total_cpk: Optional[bool] = Field(default=None)  #CPK TOTAL
    ck_mb: Optional[bool] = Field(default=None)  #CK-MB
    cpk_nac: Optional[bool] = Field(default=None)  #CPK-NAC

    troponin_i: Optional[bool] = Field(default=None)  #TROPONINA I
    troponin_t: Optional[bool] = Field(default=None)  #TROPONINA T

    nt_probnp: Optional[bool] = Field(default=None)  #NT-proBNP
    myoglobin: Optional[bool] = Field(default=None)  #MIOGLOBINA

    is_active: bool = Field(default=True)
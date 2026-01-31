import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class TransfusionMedicineRequest(SQLModel, table=True):
    __tablename__ = "transfusion_medicine_request"

    transfusion_medicine_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="transfusion_medicine_request")

    blood_group_and_rh: Optional[bool] = Field(default=None)  #GRUPO Y FACTOR
    direct_coombs: Optional[bool] = Field(default=None)  #COOMBS DIRECTO
    indirect_coombs: Optional[bool] = Field(default=None)  #COOMBS INDIRECTO

    is_active: bool = Field(default=True)
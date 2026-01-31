import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class ImmunosuppressantsRequest(SQLModel, table=True):
    __tablename__ = "immunosuppressants_request"

    immunosuppressants_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="immunosuppressants_request")

    cyclosporine: Optional[bool] = Field(default=None)  #CYCLOSPORINA
    sirolimus: Optional[bool] = Field(default=None)  #SIROLIMUS
    tacrolimus: Optional[bool] = Field(default=None)  #TACROLIMUS
    everolimus: Optional[bool] = Field(default=None)  #EVEROLIMUS

    is_active: bool = Field(default=True)

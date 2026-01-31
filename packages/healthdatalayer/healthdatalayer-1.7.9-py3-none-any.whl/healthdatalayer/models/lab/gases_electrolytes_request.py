import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab


class GasesElectrolytesRequest(SQLModel, table=True):
    __tablename__ = "gases_electrolytes_request"

    gases_electrolytes_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="gases_electrolytes_request")

    sodium: Optional[bool] = Field(default=None)  #Na
    potassium: Optional[bool] = Field(default=None)  #K
    chloride: Optional[bool] = Field(default=None)  #Cl
    ionized_calcium: Optional[bool] = Field(default=None)  #Ca+
    total_calcium: Optional[bool] = Field(default=None)  #Ca
    phosphorus: Optional[bool] = Field(default=None)  #P
    magnesium: Optional[bool] = Field(default=None)  #Mg
    lithium: Optional[bool] = Field(default=None)  #Li

    arterial_blood_gas: Optional[bool] = Field(default=None)  #GASOMETRÍA ARTERIAL
    venous_blood_gas: Optional[bool] = Field(default=None)  #GASOMETRÍA VENOSA

    is_active: bool = Field(default=True)
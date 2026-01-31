import uuid
from sqlmodel import SQLModel,Field, Relationship
from typing import Optional, TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from healthdatalayer.models import CollaboratorSpeciality

class Schedule(SQLModel,table=True):
    __tablename__ = "schedule"

    schedule_id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)
    
    collaborator_speciality_id: uuid.UUID = Field(foreign_key="collaborator_speciality.collaborator_speciality_id", primary_key=True)
    collaborator_speciality: Optional["CollaboratorSpeciality"] = Relationship(back_populates="schedule")

    start_time: Optional[datetime.time] = Field(default=None)
    end_time: Optional[datetime.time] = Field(default=None)
    interval_minutes: Optional[int] = Field(default=None)

    monday: Optional[bool] = Field(default=None)
    tuesday: Optional[bool] = Field(default=None)
    wednesday: Optional[bool] = Field(default=None)
    thursday: Optional[bool] = Field(default=None)
    friday: Optional[bool] = Field(default=None)
    saturday: Optional[bool] = Field(default=None)
    sunday: Optional[bool] = Field(default=None)

    is_active: bool = Field(default=True)
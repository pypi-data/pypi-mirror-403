import uuid
from sqlmodel import SQLModel,Field, Relationship
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from healthdatalayer.models import Schedule

class CollaboratorSpeciality(SQLModel,table=True):
    __tablename__ = "collaborator_speciality"

    collaborator_speciality_id:uuid.UUID=Field(default_factory=uuid.uuid4,primary_key=True)

    speciality_id: uuid.UUID = Field(foreign_key="speciality.speciality_id", primary_key=False)
    collaborator_id: uuid.UUID = Field(foreign_key="collaborator.collaborator_id", primary_key=False) 

    schedule: List["Schedule"] = Relationship(back_populates="collaborator_speciality")
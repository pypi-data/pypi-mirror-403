import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from healthdatalayer.models import BridgeAreaFloorBranch
from healthdatalayer.models.collaborator.collaborator import Collaborator
from healthdatalayer.models.client.px import Px

if TYPE_CHECKING:
    from healthdatalayer.models import BloodChemistryRequest
    from healthdatalayer.models import CardiacVascularMarkersRequest
    from healthdatalayer.models import CoagulationHemostasisRequest
    from healthdatalayer.models import CytochemicalBacteriologicalLiquidsRequest
    from healthdatalayer.models import GasesElectrolytesRequest
    from healthdatalayer.models import HematologyRequest
    from healthdatalayer.models import HormonesRequest
    from healthdatalayer.models import InmunologyInfectiousRequest
    from healthdatalayer.models import ImmunosuppressantsRequest
    from healthdatalayer.models import MicrobiologyRequest
    from healthdatalayer.models import MolecularBiologyGeneticsRequest
    from healthdatalayer.models import SerologyRequest
    from healthdatalayer.models import ServicePriorityAttentionRequest
    from healthdatalayer.models import StoolRequest
    from healthdatalayer.models import TransfusionMedicineRequest
    from healthdatalayer.models import TumorMarekersRequest
    from healthdatalayer.models import UrineRequest
    from healthdatalayer.models import TherapeuticDrugLevelsRequest

class RequestLab(SQLModel, table=True):
    __tablename__ = "request_lab"
    
    request_lab_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    bridge_area_floor_branch_id: Optional[uuid.UUID] = Field(default=None, foreign_key="bridge_area_floor_branch.bridge_area_floor_branch_id")
    bridge_area_floor_branch: Optional["BridgeAreaFloorBranch"] = Relationship()
    
    client_id: Optional[uuid.UUID] = Field(default=None, foreign_key="px.client_id")
    client: Optional[Px] = Relationship() 

    #DETAILS OF THE RESPONSIBLE PROFESSIONAL

    collab_id_1: Optional[uuid.UUID] = Field(default=None, foreign_key="collaborator.collaborator_id")
    collaborator_1: Optional[Collaborator] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[RequestLab.collab_id_1]"}
    )

    collab_id_2: Optional[uuid.UUID] = Field(default=None, foreign_key="collaborator.collaborator_id")
    collaborator_2: Optional[Collaborator] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[RequestLab.collab_id_2]"}
    )

    registration_date: Optional[datetime] = Field(default=None)  
    sample_collection_date: Optional[datetime] = Field(default=None) 

    is_active: bool = Field(default=True)

    #DETAILS OF THE REQUEST

    blood_chemistry_request: Optional["BloodChemistryRequest"] = Relationship(back_populates="request_lab")
    cardiac_vascular_markers_request: Optional["CardiacVascularMarkersRequest"] = Relationship(back_populates="request_lab")
    coagulation_hemostasis_request: Optional["CoagulationHemostasisRequest"] = Relationship(back_populates="request_lab")
    cytochemical_bacteriological_liquids_request: Optional["CytochemicalBacteriologicalLiquidsRequest"] = Relationship(back_populates="request_lab")
    gases_electrolytes_request: Optional["GasesElectrolytesRequest"] = Relationship(back_populates="request_lab")
    hematology_request: Optional["HematologyRequest"] = Relationship(back_populates="request_lab")
    hormones_request: Optional["HormonesRequest"] = Relationship(back_populates="request_lab")
    inmunology_infectious_request: Optional["InmunologyInfectiousRequest"] = Relationship(back_populates="request_lab") 
    immunosuppressants_request: Optional["ImmunosuppressantsRequest"] = Relationship(back_populates="request_lab")
    microbiology_request: Optional["MicrobiologyRequest"] = Relationship(back_populates="request_lab")
    molecular_biology_genetics_request: Optional["MolecularBiologyGeneticsRequest"] = Relationship(back_populates="request_lab")
    serology_request: Optional["SerologyRequest"] = Relationship(back_populates="request_lab")
    service_priority_attention_request: Optional["ServicePriorityAttentionRequest"] = Relationship(back_populates="request_lab")
    stool_request: Optional["StoolRequest"] = Relationship(back_populates="request_lab")
    transfusion_medicine_request: Optional["TransfusionMedicineRequest"] = Relationship(back_populates="request_lab")
    tumor_markers_request: Optional["TumorMarekersRequest"] = Relationship(back_populates="request_lab")
    urine_request: Optional["UrineRequest"] = Relationship(back_populates="request_lab")
    therapeutic_drug_levels_request: Optional["TherapeuticDrugLevelsRequest"] = Relationship(back_populates="request_lab")

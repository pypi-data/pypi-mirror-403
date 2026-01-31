import uuid
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from .request_lab import RequestLab

class StoolRequest(SQLModel, table=True):
    __tablename__ = "stool_request"

    stool_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional[RequestLab] = Relationship()

    stool_exam_coprological: Optional[bool] = Field(default=None)  #COPROLÓGICO / COPROPARASITARIO
    stool_parasitology_concentration: Optional[bool] = Field(default=None)  #COPROPARASITARIO POR CONCENTRACIÓN
    stool_series_exam: Optional[bool] = Field(default=None)  #COPRO SERIADO

    stool_pmn_investigation: Optional[bool] = Field(default=None)  #INVESTIGACION DE POLIMORFONUCLEARES (PMN)
    stool_occult_blood: Optional[bool] = Field(default=None)  #SANGRE OCULTA
    stool_ph_investigation: Optional[bool] = Field(default=None)  #INVESTIGACIÓN DE pH

    rotavirus: Optional[bool] = Field(default=None)  #ROTAVIRUS
    adenovirus: Optional[bool] = Field(default=None)  #ADENOVIRIS
    cryptosporidium: Optional[bool] = Field(default=None)  #CRIPTOSPORIDIUM
    pinworms: Optional[bool] = Field(default=None)  #OXIUROS
    giardia_lamblia_antigen: Optional[bool] = Field(default=None)  #GARDIA-LAMBLIA ANTÍGENO

    stool_fat_investigation: Optional[bool] = Field(default=None)  #INVESTIGACIÓN DE GRASAS
    reducing_sugars: Optional[bool] = Field(default=None)  #AZÚCARES REDUCTORES
    helicobacter_pylori: Optional[bool] = Field(default=None)  #HELICOBACTER PYLORI

    is_active: bool = Field(default=True)
import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab


class UrineRequest(SQLModel, table=True):
    __tablename__ = "urine_request"

    urine_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="urine_request")

    urinalysis_emo: Optional[bool] = Field(default=None)  #ELEMENTAL Y MICROSCOPICO (EMO)
    fresh_drop_gram_stain: Optional[bool] = Field(default=None)  #GRAM GOTA FRESCA

    urinary_osmolality: Optional[bool] = Field(default=None)  #OSMOLARIDAD URINARIA

    urine_sodium_spot: Optional[bool] = Field(default=None)  #SODIO EN ORINA PARCIAL
    urine_potassium_spot: Optional[bool] = Field(default=None)  #POTASIO EN ORINA PARCIAL
    urine_chloride_spot: Optional[bool] = Field(default=None)  #CLORO EN ORINA PARCIAL
    urinary_calcium_spot: Optional[bool] = Field(default=None)  #CALCIO URINARIO
    urine_phosphorus_spot: Optional[bool] = Field(default=None)  #FOSFORO EN ORINA PARCIAL
    urine_magnesium_spot: Optional[bool] = Field(default=None)  #MAGNESIO EN ORINA PARCIAL
    urine_glucose_spot: Optional[bool] = Field(default=None)  #GLUCOSA EN ORINA PARCIAL
    urine_urea_spot: Optional[bool] = Field(default=None)  #UREA EN ORINA PARCIAL
    urine_creatinine_spot: Optional[bool] = Field(default=None)  #CREATINA EN ORINA PARCIAL
    urine_urea_nitrogen_spot: Optional[bool] = Field(default=None)  #NITRÓGENO UREICO EN ORINA PARCIAL
    urine_uric_acid_spot: Optional[bool] = Field(default=None)  #ÁCIDO ÚRICO EN ORINA PARCIAL
    urine_proteins_spot: Optional[bool] = Field(default=None)  #PROTEINAS EN ORINA PARCIAL

    urine_phosphorus_24h: Optional[bool] = Field(default=None)  #FÓSFORO EN ORINA 24 HORAS
    urine_potassium_24h: Optional[bool] = Field(default=None)  #POTASIO EN ORINA 24 HORAS
    urine_proteins_24h: Optional[bool] = Field(default=None)  #PROTEINAS EN ORINA 24 HORAS
    creatinine_clearance_24h: Optional[bool] = Field(default=None)  #DEPURACIÓN CREATININA (ORINA 24 HORAS)
    urine_uric_acid_24h: Optional[bool] = Field(default=None)  #ÁCIDO ÚRICO EN ORINA 24 HORAS
    urine_calcium_24h: Optional[bool] = Field(default=None)  #CALCIO EN ORINA 24 HORAS
    urine_amylase_24h: Optional[bool] = Field(default=None)  #AMILASA EN ORINA 24 HORAS
    urine_copper_24h: Optional[bool] = Field(default=None)  #COBRE EN ORINA 24 HORAS

    reducing_sugars: Optional[bool] = Field(default=None)  #AZÚCARES REDUCTORES
    urine_drugs_of_abuse: Optional[bool] = Field(default=None)  #DROGAS DE ABUSO EN ORINA
    albuminuria: Optional[bool] = Field(default=None)  #ALBUMINURIA

    is_active: bool = Field(default=True)
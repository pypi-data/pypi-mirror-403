import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class BloodChemistryRequest(SQLModel, table=True):
    __tablename__ = "blood_chemistry_request"

    blood_chemistry_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="blood_chemistry_request")

    fasting_glucose: Optional[bool] = Field(default=None)  #GLUCOSA BASAL
    postprandial_glucose_2h: Optional[bool] = Field(default=None)  #GLUCOSA POST PRANDIAL 2 HORAS
    random_glucose: Optional[bool] = Field(default=None)  #GLUCOSA AL AZAR
    glucose_tolerance_test_75g: Optional[bool] = Field(default=None)  #SOBRECARGA GLUCOSA 75  gramos
    sullivan_test_50g: Optional[bool] = Field(default=None)  #TEST DE SULLIVAN (GLUCOSA 50 gramos)
    
    urea: Optional[bool] = Field(default=None)  #UREA
    creatinine: Optional[bool] = Field(default=None)  #CREATININA
    uric_acid: Optional[bool] = Field(default=None)  #ACIDO ÚRICO
    alkaline_phosphatase: Optional[bool] = Field(default=None)  #FOSFATASA ALCALINA
    lactate_dehydrogenase: Optional[bool] = Field(default=None)  #DESHIDROGENASA LACTICA (LDH)
    aspartate_aminotransferase: Optional[bool] = Field(default=None)  #ASPARTATO AMINOTRANSFERASA (AST/TGO)
    alanine_aminotransferase: Optional[bool] = Field(default=None)  #ALANINA AMINOTRANSFERASA (ALT/TGP)
    gamma_glutamyl_transferase: Optional[bool] = Field(default=None)  #GAMMA-GLUTARIL TRANSFERASA (GGT)
    amylase: Optional[bool] = Field(default=None)  #AMILASA
    lipase: Optional[bool] = Field(default=None)  #LIPASA
    total_bilirubin: Optional[bool] = Field(default=None)  #BILIRRUBINA TOTAL
    direct_bilirubin: Optional[bool] = Field(default=None)  #BILIRRUBINA DIRECTA
    indirect_bilirubin: Optional[bool] = Field(default=None)  #BILIRRUBINA INDIRECTA
    total_cholesterol: Optional[bool] = Field(default=None)  #COLESTEROL TOTAL
    hdl_cholesterol: Optional[bool] = Field(default=None)  #LIPOPROTEÍNA DE ALTA DENSIDAD (HDL)
    ldl_cholesterol: Optional[bool] = Field(default=None)  #LIPOPROTEÍNA DE BAJA DENSIDAD (LDL)
    vldl_cholesterol: Optional[bool] = Field(default=None)  #LIPOPROTEÍNA DE MUY BAJA DENSIDAD (VLDL)
    triglycerides: Optional[bool] = Field(default=None)  #TRIGLICERIDOS
    albumin: Optional[bool] = Field(default=None)  #ALBUMINA
    total_proteins: Optional[bool] = Field(default=None)  #PROTEÍNAS TOTALES
    glycated_hemoglobin: Optional[bool] = Field(default=None)  #HEMOGLOBINA GLICOSILADA (HBA1C)
    total_cpk: Optional[bool] = Field(default=None)  #CPK TOTAL
    fructosamine: Optional[bool] = Field(default=None)  #FRUCTOSAMINA
    quantitative_pcr: Optional[bool] = Field(default=None)  #PCR CUANTITATIVO

    is_active: bool = Field(default=True)
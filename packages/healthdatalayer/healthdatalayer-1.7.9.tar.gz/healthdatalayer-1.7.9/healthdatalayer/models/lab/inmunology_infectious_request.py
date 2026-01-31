import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class InmunologyInfectiousRequest(SQLModel, table=True):
    __tablename__ = "inmunology_infectious_request"

    inmunology_infectious_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="inmunology_infectious_request")

    complement_c3: Optional[bool] = Field(default=None)  #COMPLEMENTO C3
    complement_c4: Optional[bool] = Field(default=None)  #COMPLEMENTO C4

    iga_total: Optional[bool] = Field(default=None)  #IGA TOTAL
    ige_total: Optional[bool] = Field(default=None)  #IGE TOTAL
    igg_total: Optional[bool] = Field(default=None)  #IGG TOTAL
    igm_total: Optional[bool] = Field(default=None)  #IGM TOTAL

    procalcitonin: Optional[bool] = Field(default=None)  #PROCALCITONINA
    interleukin_6: Optional[bool] = Field(default=None)  #IL-6

    ana: Optional[bool] = Field(default=None)  #ANA
    anca_c: Optional[bool] = Field(default=None)  #ANCA-C
    anca_p: Optional[bool] = Field(default=None)  #ANCA-P
    anti_dna: Optional[bool] = Field(default=None)  #ANTI-DNA
    anti_ccp: Optional[bool] = Field(default=None)  #ANTI-CCP
    anti_sm: Optional[bool] = Field(default=None)  #ANTI-SM
    anti_ro: Optional[bool] = Field(default=None)  #ANTI-RO
    anti_la: Optional[bool] = Field(default=None)  #ANTI-LA

    anti_cardiolipin_igg: Optional[bool] = Field(default=None)  #ANTI CARDIOLIPINA IgG
    anti_cardiolipin_igm: Optional[bool] = Field(default=None)  #ANTI CARDIOLIPINA IgM
    antiphospholipids_igg: Optional[bool] = Field(default=None)  #ANTIFOSFOLIPIDOS IgG
    antiphospholipids_igm: Optional[bool] = Field(default=None)  #ANTIFOSFOLIPIDOS IgM

    rheumatoid_factor_igm: Optional[bool] = Field(default=None)  #FACTOR REUMATOIDEO (IgM)

    sflt1: Optional[bool] = Field(default=None)  #SFLT1 (MARCADOR DE PREECLAMPSIA)
    pigf: Optional[bool] = Field(default=None)  #PIGF (MARCADOR DE PREECLAMPSIA)

    anti_hbc_igg: Optional[bool] = Field(default=None)  #ANTICUERPOS ANTICORE Ig-G (HBcAG)
    anti_hbc_igm: Optional[bool] = Field(default=None)  #ANTICUERPOS ANTICORE Ig-M (HBcAG)

    hepatitis_a_igm: Optional[bool] = Field(default=None)  #HEPATITIS A (IgM)
    hepatitis_a_total: Optional[bool] = Field(default=None)  #HEPATITIS A TOTAL
    hbsag: Optional[bool] = Field(default=None)  #ANTIGENO SUPERFICIE HEPATITIS B (HBSAG)
    hepatitis_c_hcv: Optional[bool] = Field(default=None)  #HEPATITIS C: HVC

    hiv_1_2_qualitative: Optional[bool] = Field(default=None)  #VIH (1+2) CUALITATIVA
    hiv_1_2_quantitative: Optional[bool] = Field(default=None)  #VIH (1+2) CUANTITATIVA

    herpes_1_igg: Optional[bool] = Field(default=None)  #HERPES 1 (IgG)
    herpes_1_igm: Optional[bool] = Field(default=None)  #HERPES 1 (IgM)
    herpes_2_igg: Optional[bool] = Field(default=None)  #HERPES 2 (IgG)
    herpes_2_igm: Optional[bool] = Field(default=None)  #HERPES 2 (IgM)

    rubella_igg: Optional[bool] = Field(default=None)  #RUBEOLA (IgG)
    rubella_igm: Optional[bool] = Field(default=None)  #RUBEOLA (IgM)

    toxoplasma_igg: Optional[bool] = Field(default=None)  #TOXOPLASMA (IgG)
    toxoplasma_igm: Optional[bool] = Field(default=None)  #TOXOPLASMA (IgM)

    cytomegalovirus_igg: Optional[bool] = Field(default=None)  #CITOMEGALOVIRUS (IgG)
    cytomegalovirus_igm: Optional[bool] = Field(default=None)  #CITOMEGALOVIRUS (IgM)

    epstein_barr_igg: Optional[bool] = Field(default=None)  #EPSTEIN BAR (IgG)
    epstein_barr_igm: Optional[bool] = Field(default=None)  #EPSTEIN BAR (IgM)

    dengue_igg: Optional[bool] = Field(default=None)  #DENGUE (IgG)
    dengue_igm: Optional[bool] = Field(default=None)  #DENGUE (IgM)

    chlamydia_iga: Optional[bool] = Field(default=None)  #CLAMIDIA (IgA)
    chlamydia_igg: Optional[bool] = Field(default=None)  #CLAMIDIA (IgG)

    fta_abs: Optional[bool] = Field(default=None)  #FTA-ABS

    is_active: bool = Field(default=True)
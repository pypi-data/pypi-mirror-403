import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from healthdatalayer.models import RequestLab

class HormonesRequest(SQLModel, table=True):
    __tablename__ = "hormones_request"

    hormones_request_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    request_lab_id: Optional[uuid.UUID] = Field(default=None, foreign_key="request_lab.request_lab_id")
    request_lab: Optional["RequestLab"] = Relationship(back_populates="hormones_request")

    t3: Optional[bool] = Field(default=None)  #T3
    ft3: Optional[bool] = Field(default=None)  #FT3
    t4: Optional[bool] = Field(default=None)  #T4
    ft4: Optional[bool] = Field(default=None)  #FT4
    tsh: Optional[bool] = Field(default=None)  #TSH
    pth: Optional[bool] = Field(default=None)  #PTH
    fsh: Optional[bool] = Field(default=None)  #FSH
    androstenedione: Optional[bool] = Field(default=None)  #ANDROSTENEDIONA

    igf_1: Optional[bool] = Field(default=None)  #FACTOR DE CRECIMIENTO INSULINOIDE TIPO 1 (IGF-1)
    igfbp3: Optional[bool] = Field(default=None)  #FACTOR DE UNION DEL FACTOR DE CRECIMIENTO T1 (IGFBP3)

    beta_hcg_qualitative: Optional[bool] = Field(default=None)  #B-HCG CUALITATIVA
    beta_hcg_quantitative: Optional[bool] = Field(default=None)  #B-HCG CUANTITATIVA

    growth_hormone: Optional[bool] = Field(default=None)  #HORMONA DE CRECIMIENTO
    progesterone: Optional[bool] = Field(default=None)  #PROGESTERONA
    insulin: Optional[bool] = Field(default=None)  #INSULINA
    acth: Optional[bool] = Field(default=None)  #ACTH
    prolactin: Optional[bool] = Field(default=None)  #PROLACTINA
    vitamin_d: Optional[bool] = Field(default=None)  #VITAMINA D
    estradiol_e2: Optional[bool] = Field(default=None)  #ESTRADIOL (E2)
    lh: Optional[bool] = Field(default=None)  #LH
    cortisol: Optional[bool] = Field(default=None)  #CORTISOL
    testosterone_total: Optional[bool] = Field(default=None)  #TESTOSTERONA TOTAL
    testosterone_free: Optional[bool] = Field(default=None)  #TESTOSTERONA LIBRE
    dhea_s: Optional[bool] = Field(default=None)  #DHEA-S

    is_active: bool = Field(default=True)
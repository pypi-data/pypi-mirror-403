from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime, time

class HeaderRecipe(BaseModel):
    visit_date : Optional[datetime] = None
    name_doctor : Optional[str] = None
    ruc : Optional[str] = None
    code : Optional[str] = None
    first_name_px : Optional[str] = None
    last_name_px : Optional[str] = None
    
class RecipeMedicalDrugData(BaseModel):
    drug_name : Optional[str] = None
    comment: Optional[str] = None
    quantity :Optional[int] = None
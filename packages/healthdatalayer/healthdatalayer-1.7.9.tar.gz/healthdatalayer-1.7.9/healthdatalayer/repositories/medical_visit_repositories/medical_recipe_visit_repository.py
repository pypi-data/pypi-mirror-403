from typing import Optional, List
from uuid import UUID
from sqlmodel import select, or_, text
from sqlalchemy.orm import selectinload,joinedload
from healthdatalayer.models import MedicalRecipeVisit, MedicalDrugRecipe, MedicalDrug
from healthdatalayer.dtos import HeaderRecipe, RecipeMedicalDrugData
from healthdatalayer.config.db import engines, get_session

class MedicalRecipeVisitRepository:
    def __init__(self, tenant: str):
        self.tenant = tenant
        if tenant not in engines:
            raise ValueError(f"Tenant {tenant} is not configured")
        
    def create_command(self, medical_recipe_visit: MedicalRecipeVisit) -> MedicalRecipeVisit:
        with get_session(self.tenant) as session:
            session.add(medical_recipe_visit)
            session.commit()
            session.refresh(medical_recipe_visit)
            return medical_recipe_visit
    
    def get_by_id_command(self, medical_recipe_visit_id: UUID, load_relations: bool = False) -> Optional[MedicalRecipeVisit]:
        with get_session(self.tenant) as session:
            
            if load_relations:
                statement = select(MedicalRecipeVisit).where(MedicalRecipeVisit.medical_recipe_visit_id == medical_recipe_visit_id).options(
                    joinedload(MedicalRecipeVisit.medical_visit),
                    selectinload(MedicalRecipeVisit.medical_drug_recipes).selectinload(MedicalDrugRecipe.medical_drug)
                )
                medical_recipe_visit = session.exec(statement).first()
               
                return medical_recipe_visit
            else:
                return session.get(MedicalRecipeVisit, medical_recipe_visit_id)
    
    def get_by_medical_visit_id_command(self, medical_visit_id: UUID, load_relations: bool = False) -> Optional[MedicalRecipeVisit]:
        with get_session(self.tenant) as session:
            statement = select(MedicalRecipeVisit).where(MedicalRecipeVisit.medical_visit_id == medical_visit_id)
            if load_relations:
                statement = statement.options(
                    selectinload(MedicalRecipeVisit.medical_visit),
                    selectinload(MedicalRecipeVisit.medical_drug_recipes).selectinload(MedicalDrugRecipe.medical_drug)
                )
            medical_recipe_visit = session.exec(statement).first()
               
            return medical_recipe_visit
            
    def list_all_command(self, active_only: bool = True, load_relations: bool = False)->List[MedicalRecipeVisit]:
        with get_session(self.tenant) as session:
            statement = select(MedicalRecipeVisit)
            
            if load_relations:
                
                statement = select(MedicalRecipeVisit).options(
                    selectinload(MedicalRecipeVisit.medical_visit),
                    selectinload(MedicalRecipeVisit.medical_drug_recipes).selectinload(MedicalDrugRecipe.medical_drug)
                )
                if active_only:
                    statement = statement.where(MedicalRecipeVisit.is_active == True)
                medical_recipe_visit = session.exec(statement).all()
              
                return medical_recipe_visit
            
            statement = select(MedicalRecipeVisit)
            return session.exec(statement).all()
    
    def update_command(self, medical_recipe_visit: MedicalRecipeVisit) -> MedicalRecipeVisit:
        with get_session(self.tenant) as session:
            existing_medical_recipe_visit = session.get(MedicalRecipeVisit, medical_recipe_visit.medical_recipe_visit_id)
            if not existing_medical_recipe_visit:
                raise ValueError(f"medical_recipe_visit with id {medical_recipe_visit.medical_recipe_visit_id} does not exist")
            
            for key, value in medical_recipe_visit.dict(exclude_unset=True).items():
                setattr(existing_medical_recipe_visit, key, value)
            
            bd_medical_recipe_visit =  session.merge(existing_medical_recipe_visit)
            session.commit()
            session.refresh(bd_medical_recipe_visit)
            return bd_medical_recipe_visit
        
    def delete_command(self, medical_recipe_visit_id: UUID, soft_delete: bool = False)->None:
        with get_session(self.tenant) as session:
            existing_medical_recipe_visit = session.get(MedicalRecipeVisit, medical_recipe_visit_id)
            if not existing_medical_recipe_visit:
                raise ValueError(f"MedicalRecipeVisit with id {medical_recipe_visit_id} does not exist")

            if soft_delete:
                existing_medical_recipe_visit.is_active = False
                session.add(existing_medical_recipe_visit)
            else:
                session.delete(existing_medical_recipe_visit)

            session.commit()
            
    def get_header_recipe_data(self, med_recipe_visit_id : str) ->Optional[HeaderRecipe]:
        with get_session(self.tenant) as session:
            query= text("""
                select mv.visit_date, c."name"  as name_doctor,
                c.ruc, c.code,
                px.first_name as first_name_px , px.last_name as last_name_px
                from medical_recipe_visit mrv 
                join medical_visit mv on mv.medical_visit_id  = mrv.medical_visit_id
                join collaborator c  on c.collaborator_id  = mv.collaborator_id 
                join px on px.client_id  = mv.client_id 
                where mrv.medical_recipe_visit_id  = :med_recipe_visit_id
            """)
            result = session.exec(query, params={"med_recipe_visit_id": med_recipe_visit_id})
            
            row = result.fetchone()

            if not row:
                raise ValueError(f"No se encontró la visita médica con ID: {med_recipe_visit_id}")
            
            return HeaderRecipe(
                visit_date=row[0],
                name_doctor=row[1],
                ruc=row[2],
                code=row[3],
                first_name_px=row[4],
                last_name_px=row[5]
            )
    
    def get_recipe_drugs_data(self, med_recipe_visit_id : str) ->List[RecipeMedicalDrugData]:
        with get_session(self.tenant) as session:
            query = text("""
                select md.drug_name, mdr."comment", mdr.quantity  from medical_recipe_visit mrv 
                left join medical_drug_recipe mdr on mrv.medical_recipe_visit_id = mdr.medical_recipe_visit_id 
                left join medical_drug md on md.medical_drug_id  = mdr.medical_drug_id 
                where mrv.medical_recipe_visit_id  = :med_recipe_visit_id
            """)
            
            result = session.exec(query, params={"med_recipe_visit_id": med_recipe_visit_id})
            rows = result.fetchall()
            
            # Convertir cada fila a DiagnosisDTO
            recipe_list = []
            for row in rows:
                diagnosis = RecipeMedicalDrugData(
                    drug_name=row[0],
                    comment=row[1],
                    quantity=row[2]
                )
                recipe_list.append(diagnosis)
            
            return recipe_list
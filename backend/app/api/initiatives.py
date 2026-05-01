# app/api/initiatives.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.models.initiative import Initiative
from app.schemas.initiative import InitiativeCreate, InitiativeUpdate, InitiativeResponse

router = APIRouter(prefix="/initiatives", tags=["initiatives"])

@router.get("/{company_id}", response_model=List[InitiativeResponse])
def get_initiatives(company_id: int, db: Session = Depends(get_db)):
    return db.query(Initiative).filter(Initiative.company_id == company_id).all()

@router.post("/", response_model=InitiativeResponse)
def create_initiative(payload: InitiativeCreate, db: Session = Depends(get_db)):
    initiative = Initiative(**payload.model_dump())
    db.add(initiative)
    db.commit()
    db.refresh(initiative)
    return initiative

@router.patch("/{initiative_id}", response_model=InitiativeResponse)
def update_initiative(initiative_id: int, payload: InitiativeUpdate, db: Session = Depends(get_db)):
    initiative = db.query(Initiative).filter(Initiative.id == initiative_id).first()
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(initiative, k, v)
    db.commit()
    db.refresh(initiative)
    return initiative

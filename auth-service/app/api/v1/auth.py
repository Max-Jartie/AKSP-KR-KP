from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    # TODO: захешировать пароль
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=user_in.password,  
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

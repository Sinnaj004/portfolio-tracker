from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...models.models import User
from app.schemas.user import UserCreate, UserOut, Token  # Präziser Import
from ...core.security import get_password_hash, create_access_token, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from ...api.deps import get_db, get_current_user

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.email == user.email) | (User.username == user.username)).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = User(username=user.username, email=user.email, password=get_password_hash(user.password), is_admin=False)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login_user(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
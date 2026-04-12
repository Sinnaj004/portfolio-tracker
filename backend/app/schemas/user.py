from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

# Gemeinsame Felder für User
class UserBase(BaseModel):
    email: EmailStr
    username: str

# Felder, die beim Erstellen (POST) benötigt werden
class UserCreate(UserBase):
    password: str

# Felder, die wir nach außen zeigen (GET/POST Response)
# Das Passwort-Feld fehlt hier bewusst aus Sicherheitsgründen!
class UserOut(UserBase):
    id: UUID
    is_admin: bool
    created_at: datetime

    # Erlaubt Pydantic, Daten direkt von SQLAlchemy-Modellen zu lesen
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[UUID] = None
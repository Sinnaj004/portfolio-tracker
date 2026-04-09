from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.models import User
from ..core.security import ALGORITHM, SECRET_KEY
from app.schemas.user import TokenData

# Definiert, wo das Token herkommt
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    print("\n--- DEBUG START: get_current_user ---")
    print(f"DEBUG: Token erhalten (erste 15 Zeichen): {token[:15]}...")

    try:
        # 1. Decoding Versuch
        print(f"DEBUG: Versuche Decode mit ALGORITHM: {ALGORITHM}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id: str = payload.get("sub")
        print(f"DEBUG: Payload erfolgreich extrahiert. 'sub' (user_id): {user_id}")

        if user_id is None:
            print("DEBUG ERROR: 'sub' Claim nicht im Token gefunden!")
            raise credentials_exception

        # 2. Schema Validierung
        token_data = TokenData(user_id=user_id)
        print(f"DEBUG: TokenData Objekt erstellt: {token_data}")

    except JWTError as e:
        print(f"DEBUG ERROR: JWT Error beim Decodieren: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"DEBUG ERROR: Unerwarteter Fehler: {str(e)}")
        raise credentials_exception

    # 3. Datenbank Abfrage
    try:
        print(f"DEBUG: Suche User in DB mit ID: {token_data.user_id}")
        user = db.query(User).filter(User.id == token_data.user_id).first()

        if user is None:
            print(f"DEBUG ERROR: Kein User mit ID {token_data.user_id} in der Datenbank gefunden!")
            raise credentials_exception

        print(f"DEBUG SUCCESS: User gefunden: {user.username}")
        print("--- DEBUG ENDE: Erfolgreich ---\n")
        return user

    except Exception as e:
        print(f"DEBUG ERROR: Datenbank-Fehler: {str(e)}")
        raise credentials_exception
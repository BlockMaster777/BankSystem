import binascii
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from banksystem.logic import (UserDontExistException, InvalidTokenException)
import banksystem.logic as logic
import banksystem.db_manager as db_manager

db_man = db_manager.DBManager()
auth_service = logic.AuthService(db_man)
inter_service = logic.InteractionService(db_man, auth_service)

app = FastAPI(
    title="Bank System",
    description="Simple bank system for bank accounts",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

@app.get("/")
def ping():
    return {"message": "ok"}

@app.get("/status")
def staus():
    return {"message": "ok"}

@app.get("/users/{user_id}/balance", responses={400: {"description": "Invalid token"},
                                             404: {"description": "User dont exist"},
                                             500: {"description": "Internal server error"}})
def balance(user_id: int, token: str):
    try:
        balance = inter_service.get_balance(user_id, token)
        return {"balance": balance}
    except InvalidTokenException, binascii.Error, UnicodeError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except UserDontExistException:
        raise HTTPException(status_code=404, detail="User dont exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error {e}")

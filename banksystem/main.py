#coding=utf-8
"""
Bank System Main Module
Copyright (C) 2025  BlockMaster

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
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

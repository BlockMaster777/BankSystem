import sqlite3
from typing import Any, Optional, List

import config


class TokenAlreadyExistsException(Exception): pass


class UserAlreadyExistsException(Exception): pass


class UserDontExistException(Exception): pass


class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, sql: str, *params: Any) -> None:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()

    def _select_one(self, sql: str, *params: Any) -> Optional[sqlite3.Row]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchone()

    def _select_all(self, sql: str, *params: Any) -> List[sqlite3.Row]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()

    def _exists(self, sql: str, *params: Any) -> bool:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchone() is not None

    def create_tables(self) -> None:
        self._execute(
            """CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT NOT NULL UNIQUE,
               password TEXT NOT NULL,
               balance INTEGER NOT NULL DEFAULT 0
            );"""
        )
        self._execute(
            """CREATE TABLE IF NOT EXISTS tokens (
               token TEXT NOT NULL UNIQUE,
               expire_time REAL NOT NULL
            );"""
        )

    def add_user(self, username: str, password_hash: str) -> None:
        if self._exists("SELECT id FROM users WHERE username = ?", username):
            raise UserAlreadyExistsException()
        self._execute(
            "INSERT INTO users(username, password) VALUES (?, ?)", username, password_hash
        )

    def get_id(self, username: str) -> int:
        row = self._select_one("SELECT id FROM users WHERE username = ?", username)
        if not row:
            raise UserDontExistException()
        return int(row["id"])

    def get_username(self, user_id: int) -> str:
        row = self._select_one("SELECT username FROM users WHERE id = ?", user_id)
        if not row:
            raise UserDontExistException()
        return str(row["username"])

    def get_balance(self, user_id: int) -> int:
        row = self._select_one("SELECT balance FROM users WHERE id = ?", user_id)
        if not row:
            raise UserDontExistException()
        return int(row["balance"])

    def check_username_exists(self, username: str) -> bool:
        return self._exists("SELECT username FROM users WHERE username = ?", username)

    def check_password(self, user_id: int, password_hash: str) -> bool:
        return self._exists(
            "SELECT id FROM users WHERE id = ? AND password = ?", user_id, password_hash
        )

    def set_username(self, user_id: int, new_username: str) -> None:
        if self._exists("SELECT id FROM users WHERE username = ?", new_username):
            raise UserAlreadyExistsException()
        self._execute("UPDATE users SET username = ? WHERE id = ?", new_username, user_id)

    def set_balance(self, user_id: int, new_balance: int) -> None:
        self._execute("UPDATE users SET balance = ? WHERE id = ?", new_balance, user_id)

    def delete_user(self, user_id: int) -> None:
        if not self._exists("SELECT id FROM users WHERE id = ?", user_id):
            raise UserDontExistException()
        self._execute("DELETE FROM users WHERE id = ?", user_id)

    def create_token(self, token: str, expire_time: float) -> None:
        if self._exists("SELECT token FROM tokens WHERE token = ?", token):
            raise TokenAlreadyExistsException()
        self._execute("INSERT INTO tokens(token, expire_time) VALUES (?, ?)", token, expire_time)

    def check_token_exists(self, token: str) -> bool:
        return self._exists("SELECT token FROM tokens WHERE token = ?", token)

    def delete_expired_tokens(self, current_time: float) -> None:
        self._execute("DELETE FROM tokens WHERE expire_time <= ?", current_time)


if __name__ == '__main__':
    db_manager = DBManager(config.DB_PATH)
    db_manager.create_tables()

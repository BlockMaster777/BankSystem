import base64
import hashlib
import secrets
import time
import config
import banksystem.db_manager as db_manager
from banksystem.db_manager import UserAlreadyExistsException


class WrongPasswordException(Exception): pass


class AuthService:
    def __init__(self, db_path: str = config.DB_PATH, token_ttl: int = 60) -> None:
        self._db = db_manager.DBManager(db_path)
        self._token_ttl = int(token_ttl)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode(), usedforsecurity=True).hexdigest()

    def check_password(self, user_id: int, password: str) -> bool:
        return self._db.check_password(user_id, self._hash_password(password))

    @staticmethod
    def _gen_token(user_id: int) -> str:
        raw = f"{user_id}:{secrets.token_urlsafe(32)}"
        return base64.urlsafe_b64encode(raw.encode()).decode()

    def get_token(self, user_id: int, password: str) -> str:
        if not self.check_password(user_id, password):
            raise WrongPasswordException()
        token = self._gen_token(user_id)
        while self._db.check_token_exists(token):
            token = self._gen_token(user_id)
        self._db.create_token(token, time.time() + self._token_ttl)
        return token

    def register_user_and_get_id(self, username: str, password: str) -> int:
        if self._db.check_username_exists(username):
            raise UserAlreadyExistsException()
        self._db.add_user(username, self._hash_password(password))
        return self._db.get_id(username)


if __name__ == '__main__':
    name = "block"
    psw = "123"

    auth = AuthService()
    my_id = auth.register_user_and_get_id(name, psw)
    my_token = auth.get_token(my_id, psw)

    print(my_id)
    print(my_token)
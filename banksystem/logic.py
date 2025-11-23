import base64
import hashlib
import secrets
import time
import config
import banksystem.db_manager as db_manager
from banksystem.db_manager import UserAlreadyExistsException
from banksystem.db_manager import UserDontExistException


class WrongPasswordException(Exception): pass
class InvalidTokenException(Exception): pass
class NotEnoughFundsException(Exception): pass
class NoAccessException(Exception): pass

db_man = db_manager.DBManager()


class AuthService:
    def __init__(self, db: db_manager.DBManager, token_ttl: int = config.TOKEN_TTL) -> None:
        self._db = db
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
        self._db.delete_expired_tokens(time.time())
        while self._db.check_token_exists(token, time.time()):
            token = self._gen_token(user_id)
        self._db.create_token(token, time.time() + self._token_ttl)
        return token

    def get_id(self, username: str) ->  int:
        if self._db.check_username_exists(username):
            return self._db.get_id(username)
        raise UserDontExistException

    def register_user_and_get_id(self, username: str, password: str) -> int:
        if self._db.check_username_exists(username):
            raise UserAlreadyExistsException()
        self._db.add_user(username, self._hash_password(password))
        return self._db.get_id(username)

    def verify_token(self, user_id: int, token: str) -> bool:
        token_data = base64.urlsafe_b64decode(token.encode()).decode().split(":")
        if len(token_data) != 0:
            if token_data[0].isnumeric():
                self._db.delete_expired_tokens(time.time())
                if self._db.check_token_exists(token, time.time()):
                    if int(token_data[0]) == user_id:
                        return True
        return False


class InteractionService:
    def __init__(self, db: db_manager.DBManager, auth_service: AuthService) -> None:
        self._db = db
        self._auth = auth_service

    def edit_username(self, user_id: int, new_username: str, token: str) -> None:
        if self._auth.verify_token(user_id, token):
            self._db.set_username(user_id, new_username)
        else:
            raise InvalidTokenException

    def send_money(self, user_id: int, amount: int, to_id: int, token: str):
        if self._auth.verify_token(user_id, token):
            if (balance := self._db.get_balance(user_id)) > amount:
                if self._db.check_id_exists(to_id):
                    receiver_balance = self._db.get_balance(to_id)
                    self._db.set_balance(user_id, balance - amount)
                    self._db.set_balance(to_id, receiver_balance + amount)
                else:
                    raise UserDontExistException()
            else:
                raise NotEnoughFundsException()
        else:
            raise InvalidTokenException()

    def get_balance(self, user_id: int, token: str) -> int:
        if self._auth.verify_token(user_id, token):
            return self._db.get_balance(user_id)
        else:
            raise InvalidTokenException()

    def get_uid(self, username: str) -> int:
        return self._db.get_id(username)

    def delete_user(self, user_id: int, token: str) -> None:
        if self._auth.verify_token(user_id, token):
            self._db.delete_user(user_id)
        else:
            raise InvalidTokenException()

    def set_balance(self, user_id: int, amount: int, token: str) -> None:
        if user_id != 1:
            raise NoAccessException()
        if self._auth.verify_token(user_id, token):
            self._db.set_balance(user_id, amount)
        else:
            raise InvalidTokenException()

    def register_user(self, username: str, password: str) -> int:
        try:
            return self._auth.register_user_and_get_id(username, password)
        except UserAlreadyExistsException:
            raise UserAlreadyExistsException()


if __name__ == '__main__':
    usn1 = "block"
    usn2 = "roma"
    psw1 = "123"
    psw2 = "111"

    auth = AuthService(db_man)
    my_token = auth.get_token(1, psw1)
    print(my_token)
    print(auth.verify_token(1, my_token))
    inter = InteractionService(db_man, auth)
    inter.send_money(1, 100, 2, my_token)
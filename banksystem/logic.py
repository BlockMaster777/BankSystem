import hashlib
import dotenv
import os
import time
import config
import jwt
import banksystem.db_manager as db_manager
from banksystem.db_manager import UserAlreadyExistsException
from banksystem.db_manager import UserDontExistException


class WrongPasswordException(Exception): pass
class InvalidTokenException(Exception): pass
class NotEnoughFundsException(Exception): pass
class NoAccessException(Exception): pass

db_man = db_manager.DBManager()
dotenv.load_dotenv()

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
        payload = {
            "user_id": user_id,
            "exp": time.time() + config.TOKEN_TTL,
            "iss": "bank_system",
        }
        return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")

    def get_token(self, user_id: int, password: str) -> str:
        if not self.check_password(user_id, password):
            raise WrongPasswordException()
        return self._gen_token(user_id)

    def get_id(self, username: str) ->  int:
        if self._db.check_username_exists(username):
            return self._db.get_id(username)
        raise UserDontExistException

    def register_user_and_get_id(self, username: str, password: str) -> int:
        if self._db.check_username_exists(username):
            raise UserAlreadyExistsException()
        self._db.add_user(username, self._hash_password(password))
        return self._db.get_id(username)

    @staticmethod
    def verify_token(user_id: int, token: str) -> bool:
        try:
            decoded = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=["HS256"])
        except jwt.ExpiredSignatureError, jwt.InvalidTokenError:
            raise InvalidTokenException()
        if decoded.get("user_id") != user_id:
            return False
        return True


class InteractionService:
    def __init__(self, db: db_manager.DBManager, auth_service: AuthService) -> None:
        self._db = db
        self._auth = auth_service

    @staticmethod
    def _is_admin(user_id: int) -> bool:
        return user_id in config.ADMIN_UIDS

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

    def admin_get_balance(self, user_id: int, of_user_id: int, token: str) -> int:
        if not self._is_admin(user_id):
            raise NoAccessException()
        if self._auth.verify_token(user_id, token):
            return self._db.get_balance(of_user_id)
        else:
            raise InvalidTokenException()

    def get_uid(self, username: str) -> int:
        return self._db.get_id(username)

    def delete_user(self, user_id: int, token: str) -> None:
        if self._auth.verify_token(user_id, token):
            self._db.delete_user(user_id)
        else:
            raise InvalidTokenException()

    def admin_delete_user(self, user_id: int, to_delete_user_id: int, token: str) -> None:
        if not self._is_admin(user_id):
            raise NoAccessException()
        if self._auth.verify_token(user_id, token):
            self._db.delete_user(to_delete_user_id)
        else:
            raise InvalidTokenException()

    def set_balance(self, user_id: int, amount: int, to_uid: int, token: str) -> None:
        if not self._is_admin(user_id):
            raise NoAccessException()
        if self._auth.verify_token(user_id, token):
            self._db.set_balance(to_uid, amount)
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

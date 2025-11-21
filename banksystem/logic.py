import base64
import hashlib
import random
import time
import config
import banksystem.db_manager as db_manager
from banksystem.db_manager import UserAlreadyExistsException
import schedule


class WrongPasswordException(Exception): pass


db_manager = db_manager.DBManager(config.DB_PATH)


def get_password_hash(password):
    return hashlib.sha256(password.encode(), usedforsecurity=True).hexdigest()


def check_password(user_id, password):
    return db_manager.check_password(user_id, get_password_hash(password))


def gen_token(user_id):
    return base64.b64encode((str(user_id) + str(random.randint(-9999999999, 999999999))).encode())


def get_token(user_id, password):
    if check_password(user_id, password):
        token = gen_token(user_id)
        while db_manager.check_token_exists(token):
            token = gen_token(user_id)
        db_manager.create_token(token, time.time() + 60)
        return token
    else:
        raise WrongPasswordException


def register_user_and_get_id(username, password) -> int:
    if not db_manager.check_username_exists(username):
        db_manager.add_user(username, get_password_hash(password))
        return db_manager.get_id(username)
    raise UserAlreadyExistsException


if __name__ == '__main__':
    name = "block"
    psw = "123"

    my_id = register_user_and_get_id(name, psw)
    my_token = get_token(my_id, psw)

    print(my_id)
    print(my_token)
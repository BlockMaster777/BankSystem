import sqlite3

import config


class TokenAlreadyExistsException(Exception): pass


class UserAlreadyExistsException(Exception): pass


class UserDontExistException(Exception): pass


class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def __execute(self, sql, *data):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()

    def __select_one(self, sql, *data):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchone()

    def __select_all(self, sql, *data):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def __check_if_exists(self, sql, *data):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return bool(cur.fetchone())

    def create_tables(self):
        self.__execute("""CREATE TABLE IF NOT EXISTS "users" (
	                      "id"	      INTEGER NOT NULL UNIQUE,
	                      "username"  TEXT NOT NULL UNIQUE,
	                      "password"  TEXT NOT NULL,
	                      "balance"	  INTEGER NOT NULL DEFAULT 0,
	                      PRIMARY KEY("id" AUTOINCREMENT));""")
        self.__execute("""CREATE TABLE IF NOT EXISTS "tokens" (
	                      "token"	    INTEGER NOT NULL UNIQUE,
	                      "expire_time" INTEGER NOT NULL);""")

    def add_user(self, username, password_hash):
        if self.__check_if_exists("SELECT id FROM users WHERE username = ?", username):
            raise UserAlreadyExistsException
        self.__execute("INSERT INTO users(username, password) VALUES (?, ?)", username, password_hash)

    def get_id(self, username):
        return self.__select_one("SELECT id FROM users WHERE username = ?", username)[0]

    def get_username(self, user_id):
        return self.__select_one("SELECT username FROM users WHERE id = ?", user_id)[0]

    def get_balance(self, user_id):
        return self.__select_one("SELECT balance FROM users WHERE id = ?", user_id)[0]

    def check_username_exists(self, username):
        return self.__check_if_exists("SELECT username FROM users WHERE username = ?",
                                      username)

    def check_password(self, user_id, password_hash):
        return self.__check_if_exists("SELECT id FROM users WHERE id = ? AND password = ?",
                                      user_id, password_hash)

    def set_username(self, user_id, new_username):
        if self.__check_if_exists("SELECT id FROM users WHERE username = ?", new_username):
            raise UserAlreadyExistsException
        self.__execute("UPDATE users SET username = ? WHERE id = ?", new_username, user_id)

    def set_balance(self, user_id, new_balance):
        self.__execute("UPDATE users SET balance = ? WHERE id = ?", new_balance, user_id)

    def delete_user(self, user_id):
        if not self.__check_if_exists("SELECT id FROM users WHERE id = ?", user_id):
            raise UserDontExistException
        self.__execute("DELETE FROM users WHERE id = ?", user_id)

    def create_token(self, token, expire_time):
        if self.__check_if_exists("SELECT token FROM tokens WHERE token = ?", token):
            raise TokenAlreadyExistsException
        self.__execute("INSERT INTO tokens VALUES (?, ?)", token, expire_time)

    def check_token_exists(self, token):
        return self.__check_if_exists("SELECT token FROM tokens WHERE token = ?", token)

    def delete_expired_tokens(self, time):
        self.__execute("DELETE FROM tokens WHERE expire_time <= ?", time)


if __name__ == '__main__':
    db_manager = DBManager(config.DB_PATH)
    db_manager.create_tables()

#coding=utf-8
"""
Bank System Database test Module
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
import sqlite3

import pytest

import banksystem.db_manager


@pytest.fixture
def temp_db():
    return "./test_database.db"


@pytest.fixture
def temp_conn(temp_db):
    with sqlite3.connect(temp_db) as conn:
        return conn


@pytest.fixture
def temp_cursor(temp_conn):
    return temp_conn.cursor()


@pytest.fixture
def temp_manager(temp_db, temp_cursor, temp_conn):
    manager = banksystem.db_manager.DBManager(temp_db)
    temp_cursor.execute("DROP TABLE IF EXISTS users")
    temp_cursor.execute("DROP TABLE IF EXISTS tokens")
    manager.create_tables()
    return manager


def test_add_user(temp_conn, temp_cursor, temp_manager):
    temp_manager.add_user("test", "hash")
    temp_cursor.execute("SELECT username, password FROM users WHERE username = 'test' AND password = 'hash'")
    assert temp_cursor.fetchall() == [("test", "hash")]

def test_add_existing_user(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    with pytest.raises(banksystem.db_manager.UserAlreadyExistsException):
        temp_manager.add_user("test", "another")

def test_get_id(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    assert temp_manager.get_id("test") == 1

def test_get_username(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    assert temp_manager.get_username(1) == "test"

def test_get_balance(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    assert temp_manager.get_balance(1) == 0

def test_check_username(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    assert (temp_manager.check_username_exists("test") == True and
            temp_manager.check_username_exists("dont exist") == False)

def test_check_id(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    assert (temp_manager.check_id_exists(1) == True and
            temp_manager.check_id_exists(84) == False)

def test_check_password(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    assert (temp_manager.check_password(1, "hash") == True and
            temp_manager.check_password(1, "wrong") == False)

def test_set_username(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    temp_manager.set_username(1, "new")
    assert temp_manager.get_username(1) == "new"

def test_set_existing_username(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    temp_manager.add_user("test2", "hash")
    with pytest.raises(banksystem.db_manager.UserAlreadyExistsException):
        temp_manager.set_username(1, "test2")

def test_set_balance(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    temp_manager.set_balance(1, 1000)
    assert temp_manager.get_balance(1) == 1000

def test_delete_user(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    temp_manager.add_user("test2", "hash")
    temp_manager.delete_user(1)
    assert (temp_manager.check_username_exists("test") == False and
            temp_manager.check_username_exists("test2") == True)

def test_deleting_non_existing_user(temp_conn, temp_manager):
    temp_manager.add_user("test", "hash")
    with pytest.raises(banksystem.db_manager.UserDontExistException):
        temp_manager.delete_user(84)

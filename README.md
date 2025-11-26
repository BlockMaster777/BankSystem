# Bank System
This is a simple bank system with accounts and transactions made in Python
with fastAPI and database integration.

## How to start
First, you need to register an account with a unique username and password.
```HTTP REQUEST
POST /users HTTP/1.1
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```
Then you will need to get JWT token to authenticate your requests.
```HTTP REQUEST
GET /token HTTP/1.1
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
``` 
The response will contain the access token.
```JSON
{
    "access_token": "your_jwt_token"
}
```
You will need to include this token in the Authorization header of your requests.
```HTTP REQUEST
GET <request_endpoint> HTTP/1.1
Authorization: Bearer your_jwt_token
# other data...
```

## Endpoints

- `POST /users`: Create a new user account.
- `GET /token`: Get JWT token for authentication.
- `GET /id/<username>`: Get id of a user by their username.
- `GET /users/<your_id>/balance`: Get the balance of your account.
- `POST /users/<your_id>/username`: Change your username.
- `DELETE /users/<your_id>`: Delete your user account.

## How to run
First, make sure you have Python installed on your machine.
Then, clone this repository
```bash
git clone https://github.com/BlockMaster777/BankSystem.git
```
Next, download the required packages
```bash
pip install -r requirements.txt
```
Finally, run the application
```bash
uvicorn main:app --reload
```

# License

```
Bank System
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
```

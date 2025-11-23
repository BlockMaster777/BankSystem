import binascii
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs
from banksystem.logic import (UserAlreadyExistsException, UserDontExistException, InvalidTokenException,
                   NotEnoughFundsException, WrongPasswordException)
import config
import banksystem.logic as logic
import banksystem.db_manager as db_manager

db_man = db_manager.DBManager()
auth_service = logic.AuthService(db_man)
inter_service = logic.InteractionService(db_man, auth_service)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status_code=200, content_type="application/json"):
        body = json.dumps(obj).encode()
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        match parsed_path.path:
            case "/status":
                self._handle_status()
            case "/ping":
                self._handle_ping()
            case "/balance":
                self._handle_balance(parsed_path)
            case "/uid":
                self._handle_uid(parsed_path)
            case "/token":
                self._handle_get_token(parsed_path)
            case "/transfer":
                self._handle_transfer_funds(parsed_path)
            case "/register":
                self._register_user(parsed_path)
            case _:
                self._send_json({"error": "Not Found"}, status_code=404)

    def _handle_status(self):
        self._send_json({"status": "ok"})

    def _handle_ping(self):
        self._send_json({"ping": "ok"})

    def _handle_balance(self, parsed_path):
        query_params = parse_qs(parsed_path.query)
        uid = self._get_qs_param(query_params, "uid")
        token = self._get_qs_param(query_params, "token")

        if uid is None:
            self._send_json({"error": "Missing uid"}, status_code=400)
            return
        if token is None:
            self._send_json({"error": "Missing token"}, status_code=400)
            return

        try:
            uid_int = int(uid)
        except ValueError:
            self._send_json({"error": "Invalid uid"}, status_code=400)
            return

        try:
            balance = inter_service.get_balance(uid_int, token)
            self._send_json({"balance": balance})
        except InvalidTokenException, binascii.Error, UnicodeError:
            self._send_json({"error": "Invalid token"}, status_code=403)
        except UserDontExistException:
            self._send_json({"error": "User does not exist"}, status_code=404)
        except Exception as e:
            self._send_json({"error": f"Internal server error: {e}"}, status_code=500)

    def _handle_uid(self, parsed_path):
        query_params = parse_qs(parsed_path.query)
        username = self._get_qs_param(query_params, "username")

        if username is None:
            self._send_json({"error": "Missing username"}, status_code=400)
            return

        try:
            uid = inter_service.get_uid(username)
        except UserDontExistException:
            self._send_json({"error": "User does not exist"}, status_code=404)
            return

        self._send_json({"uid": uid})

    def _handle_get_token(self, parsed_path):
        query_params = parse_qs(parsed_path.query)
        uid = self._get_qs_param(query_params, "uid")
        password = self._get_qs_param(query_params, "password")

        if uid is None:
            self._send_json({"error": "Missing uid"}, status_code=400)
            return
        if password is None:
            self._send_json({"error": "Missing password"}, status_code=400)
            return

        try:
            uid_int = int(uid)
        except ValueError:
            self._send_json({"error": "Invalid uid"}, status_code=400)
            return

        try:
            token = auth_service.get_token(uid_int, password)
            self._send_json({"token": token})
        except WrongPasswordException:
            self._send_json({"error": "Wrong password"}, status_code=403)

    def _handle_transfer_funds(self, parsed_path):
        query_params = parse_qs(parsed_path.query)
        from_uid = self._get_qs_param(query_params, "uid")
        to_uid = self._get_qs_param(query_params, "to_uid")
        amount = self._get_qs_param(query_params, "amount")
        token = self._get_qs_param(query_params, "token")

        if from_uid is None or to_uid is None or amount is None or token is None:
            self._send_json({"error": "Missing parameters"}, status_code=400)
            return

        try:
            from_uid_int = int(from_uid)
            to_uid_int = int(to_uid)
            amount_int = int(amount)
        except ValueError:
            self._send_json({"error": "Invalid parameters"}, status_code=400)
            return

        try:
            inter_service.send_money(from_uid_int, amount_int, to_uid_int, token)
            self._send_json({"status": "success"})
        except InvalidTokenException, binascii.Error, UnicodeError:
            self._send_json({"error": "Invalid token"}, status_code=403)
        except UserDontExistException:
            self._send_json({"error": "User does not exist"}, status_code=404)
        except NotEnoughFundsException:
            self._send_json({"error": "Not enough funds"}, status_code=400)
        except Exception as e:
            self._send_json({"error": f"Internal server error: {e}"}, status_code=500)

    def _register_user(self, parsed_path):
        query_params = parse_qs(parsed_path.query)
        username = self._get_qs_param(query_params, "username")
        password = self._get_qs_param(query_params, "password")

        if username is None:
            self._send_json({"error": "Missing username"}, status_code=400)
            return
        if password is None:
            self._send_json({"error": "Missing password"}, status_code=400)
            return

        try:
            user_id = inter_service.register_user(username, password)
            self._send_json({"uid": user_id})
        except UserAlreadyExistsException:
            self._send_json({"error": "User already exists"}, status_code=400)
        except Exception as e:
            self._send_json({"error": f"Internal server error: {e}"}, status_code=500)

    @staticmethod
    def _get_qs_param(params, name):
        return params.get(name, [None])[0]


def run(host=config.HOST, port=config.PORT):
    srv = HTTPServer((host, port), Handler)
    print(f"Listening on http://{host}:{port}")
    srv.serve_forever()

if __name__ == '__main__':
    run()

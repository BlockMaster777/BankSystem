from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs
from logic import (UserAlreadyExistsException, UserDontExistException, InvalidTokenException,
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
        except InvalidTokenException:
            self._send_json({"error": "Invalid token"}, status_code=403)
        except UserDontExistException:
            self._send_json({"error": "User does not exist"}, status_code=404)

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

    @staticmethod
    def _get_qs_param(params, name):
        return params.get(name, [None])[0]
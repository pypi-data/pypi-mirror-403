import bcrypt
import uuid
from Radium.outputs import Outputs

class AccountSystem:
    def __init__(self):
        self.users = {}     # email -> hashed password
        self.sessions = {}  # session_id -> email

    def create_account(self, email, password):
        if email in self.users:
            return Outputs.JSONResponse({
                "message": "User already exists"},
                status= "409 Conflict"
            )

        self.users[email] = self.hash_password(password)

        return Outputs.JSONResponse({
            "message": "Account created"},
            status= "201 Created"
        )

    def login(self, email, password):
        if email not in self.users:
            return Outputs.JSONResponse({
                "message": "User not found"},
                status= "404 Not Found"
            )

        if not self.verify_password(password, self.users[email]):
            return Outputs.JSONResponse({
                "message": "Invalid credentials"},
                status= "401 Unauthorized"
            )

        session_id = uuid.uuid4().hex
        self.sessions[session_id] = email

        return Outputs.RedirectResponse(
            '/',
            cookies={"session_id": session_id},
            status="302 Found"
        )

    def logout(self, request):
        session_id = request.cookies.get("session_id")

        if session_id and session_id in self.sessions:
            del self.sessions[session_id]

        return Outputs.RedirectResponse(
            '/',
            cookies={"session_id": ""},
            status="302 Found"
        )

    def get_session(self, request):
        session_id = request.cookies.get("session_id")

        if not session_id or session_id not in self.sessions:
            return Outputs.JSONResponse(
                {"message": "Not logged in"},
                cookies={"session_id": ""},
                status="401 Unauthorized"
            )

        email = self.sessions[session_id]

        return Outputs.JSONResponse(
            {"email": email},
            cookies={"session_id": ""},
            status="200 OK"
        )
        

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            password.encode(),
            hashed.encode()
        )

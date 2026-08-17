import threading
import uuid
from typing import Optional

from app.config import settings
from app.schemas import BookingMode, Session


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self) -> Session:
        session_id = str(uuid.uuid4())
        default_mode = BookingMode(settings.booking_mode.lower())
        session = Session(id=session_id, booking_mode=default_mode)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(session_id)

    def update(self, session: Session) -> Session:
        with self._lock:
            self._sessions[session.id] = session
        return session

    def delete(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False


session_store = SessionStore()

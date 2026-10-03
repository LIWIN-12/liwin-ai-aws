import sqlite3
from threading import Lock

from backend.config import get_settings


class ConversationMemory:

    def __init__(self, max_messages: int | None = None):
        settings = get_settings()
        self.db_path = settings.memory_path
        self.max_messages = max_messages or settings.memory_max_messages
        self.retention_days = settings.memory_retention_days
        self.lock = Lock()

        self._initialize_database()

    def _connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _initialize_database(self):

        with self._connect() as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_created_at
                ON messages(created_at)
            """)

            conn.commit()

    def add_message(self, session_id, role, content):

        with self.lock:

            with self._connect() as conn:

                conn.execute(
                    """
                    INSERT INTO messages
                    (session_id, role, content)
                    VALUES (?, ?, ?)
                    """,
                    (
                        session_id,
                        role,
                        content
                    )
                )

                conn.execute(
                    """
                    DELETE FROM messages
                    WHERE created_at < datetime('now', ?)
                    """,
                    (f"-{self.retention_days} days",),
                )

                conn.commit()

    def get_history(self, session_id):

        with self.lock:

            with self._connect() as conn:

                cursor = conn.execute(
                    """
                    SELECT role, content
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (
                        session_id,
                        self.max_messages
                    )
                )

                messages = cursor.fetchall()

        # Return chronological order
        messages.reverse()

        return [
            {
                "role": role,
                "content": content
            }
            for role, content in messages
        ]

    def format_history(self, session_id):

        history = self.get_history(session_id)

        if not history:
            return ""

        formatted = []

        for message in history:

            role = message["role"].upper()
            content = message["content"]

            formatted.append(
                f"{role}: {content}"
            )

        return "\n".join(formatted)

    def clear(self, session_id):

        with self.lock:

            with self._connect() as conn:

                conn.execute(
                    """
                    DELETE FROM messages
                    WHERE session_id = ?
                    """,
                    (session_id,)
                )

                conn.commit()

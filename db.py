import os
import base64
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()  # reads .env file into environment variables

def _resolve_lakebase_url() -> str:
    """
    Local dev: read LAKEBASE_URL directly from .env.
    Deployed (Databricks Apps): fetch the secret at runtime using the
    scope/key names injected as env vars, via the Databricks SDK.
    """
    if os.environ.get("LAKEBASE_URL"):
        return os.environ["LAKEBASE_URL"]

    from databricks.sdk import WorkspaceClient

    scope = os.environ["LAKEBASE_SECRET_SCOPE"]
    key = os.environ["LAKEBASE_SECRET_KEY"]

    w = WorkspaceClient()
    secret_response = w.secrets.get_secret(scope=scope, key=key)
    return base64.b64decode(secret_response.value).decode("utf-8")


LAKEBASE_URL = _resolve_lakebase_url()


def get_connection():
    """
    Opens a new connection to Lakebase.
    Simple approach for this homework's scale — one connection per request.
    (A connection pool would be the production-grade upgrade, not required here.)
    """
    return psycopg2.connect(LAKEBASE_URL)


def get_all_tickets():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT ticket_id, title, status, priority, created_by, created_at
                FROM tickets
                ORDER BY created_at DESC
            """)
            return cur.fetchall()


def get_ticket(ticket_id: str):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT ticket_id, title, status, priority, created_by, created_at
                FROM tickets
                WHERE ticket_id = %s
            """, (ticket_id,))
            return cur.fetchone()


def get_messages(ticket_id: str):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT message_id, ticket_id, message_text, author, created_at
                FROM ticket_messages
                WHERE ticket_id = %s
                ORDER BY created_at ASC
            """, (ticket_id,))
            return cur.fetchall()


def create_ticket(title: str, created_by: str, priority: str = "medium"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tickets (title, created_by, priority)
                VALUES (%s, %s, %s)
                RETURNING ticket_id
            """, (title, created_by, priority))
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id


def add_message(ticket_id: str, message_text: str, author: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ticket_messages (ticket_id, message_text, author)
                VALUES (%s, %s, %s)
            """, (ticket_id, message_text, author))
            conn.commit()


def update_ticket_status(ticket_id: str, status: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE tickets SET status = %s WHERE ticket_id = %s
            """, (status, ticket_id))
            conn.commit()

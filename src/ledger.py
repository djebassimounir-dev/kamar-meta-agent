import hashlib
import hmac
import json
import secrets
import sqlite3
from pathlib import Path


class TokenLedger:
    def __init__(self, db_path="kamar_ledger.db", key_path=".kamar_master.key",
                 secret_key=None):
        self.db_path = str(db_path)
        self.key_path = Path(key_path)

        if secret_key is not None:
            self.secret_key = secret_key
        else:
            if self.key_path.exists():
                self.secret_key = self.key_path.read_bytes()
            else:
                self.secret_key = secrets.token_bytes(32)
                self.key_path.write_bytes(self.secret_key)

        if len(self.secret_key) < 32:
            raise ValueError("MASTER_KEY_TOO_SHORT")

        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    token_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    revoked INTEGER NOT NULL,
                    used INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    row_signature TEXT NOT NULL
                )
            """)

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=15)

    def _signature(self, token_id, agent_id, revoked, used, created_at):
        payload = json.dumps(
            [token_id, agent_id, revoked, used, created_at],
            separators=(",", ":")
        ).encode("utf-8")
        return hmac.new(
            self.secret_key, payload, hashlib.sha256
        ).hexdigest()

    def issue_token(self, agent_id):
        import time
        token_id = secrets.token_hex(16)
        created_at = time.time()
        revoked, used = 0, 0
        signature = self._signature(
            token_id, agent_id, revoked, used, created_at
        )

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO tokens
                VALUES (?, ?, ?, ?, ?, ?)
            """, (token_id, agent_id, revoked, used, created_at, signature))

        return token_id

    def _read_valid_row(self, conn, token_id):
        row = conn.execute("""
            SELECT agent_id, revoked, used, created_at, row_signature
            FROM tokens WHERE token_id = ?
        """, (token_id,)).fetchone()

        if row is None:
            return None

        agent_id, revoked, used, created_at, stored_sig = row
        expected = self._signature(
            token_id, agent_id, revoked, used, created_at
        )

        if not hmac.compare_digest(stored_sig, expected):
            raise ValueError("LEDGER_TAMPERING_DETECTED")

        return agent_id, revoked, used, created_at

    def verify_token(self, token_id):
        with self._connect() as conn:
            row = self._read_valid_row(conn, token_id)
            return bool(row and row[1] == 0 and row[2] == 0)

    def revoke_token(self, token_id):
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._read_valid_row(conn, token_id)
            if row is None:
                conn.rollback()
                return False

            agent_id, revoked, used, created_at = row
            if revoked == 1:
                conn.rollback()
                return True

            signature = self._signature(
                token_id, agent_id, 1, used, created_at
            )
            conn.execute("""
                UPDATE tokens
                SET revoked = 1, row_signature = ?
                WHERE token_id = ?
            """, (signature, token_id))
            conn.commit()
            return True

    def consume_token(self, token_id):
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._read_valid_row(conn, token_id)

            if row is None:
                conn.rollback()
                return False

            agent_id, revoked, used, created_at = row
            if revoked or used:
                conn.rollback()
                return False

            signature = self._signature(
                token_id, agent_id, revoked, 1, created_at
            )
            cursor = conn.execute("""
                UPDATE tokens
                SET used = 1, row_signature = ?
                WHERE token_id = ? AND used = 0 AND revoked = 0
            """, (signature, token_id))

            if cursor.rowcount != 1:
                conn.rollback()
                return False

            conn.commit()
            return True

import sqlite3
import threading

import pytest

from src.ledger import TokenLedger


@pytest.fixture
def ledger(tmp_path):
    return TokenLedger(
        db_path=tmp_path / "test.db",
        key_path=tmp_path / "test.key",
        secret_key=b"KAMAR_TEST_SECRET_KEY_32_BYTES!!"
    )


def test_token_validity_and_revocation(ledger):
    token = ledger.issue_token("agent_alpha")
    assert ledger.verify_token(token) is True
    assert ledger.revoke_token(token) is True
    assert ledger.verify_token(token) is False


def test_sql_tampering_detected(ledger):
    token = ledger.issue_token("agent_beta")
    assert ledger.revoke_token(token)

    with sqlite3.connect(ledger.db_path) as conn:
        conn.execute(
            "UPDATE tokens SET revoked = 0 WHERE token_id = ?",
            (token,)
        )

    with pytest.raises(ValueError, match="LEDGER_TAMPERING_DETECTED"):
        ledger.verify_token(token)


def test_single_use_concurrency(ledger):
    token = ledger.issue_token("agent_gamma")
    results = []
    lock = threading.Lock()

    def worker():
        value = ledger.consume_token(token)
        with lock:
            results.append(value)

    threads = [
        threading.Thread(target=worker),
        threading.Thread(target=worker)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sum(results) == 1


def test_token_persistence_between_instances(tmp_path):
    db = tmp_path / "persistent.db"
    key = tmp_path / "persistent.key"
    secret = b"KAMAR_TEST_SECRET_KEY_32_BYTES!!"

    first = TokenLedger(db, key, secret)
    token = first.issue_token("agent_delta")

    second = TokenLedger(db, key, secret)
    assert second.verify_token(token) is True

import hashlib

from src.inspector import KamarInspector
from src.engine import KamarEngine


def valid_payload():
    return {
        "claims": [
            {"text": "Claim supported", "evidence_ids": ["E1"]}
        ],
        "evidence": [{"id": "E1", "description": "Test evidence"}],
        "contradictions": [],
        "trace": [{"action": "inspect", "timestamp": "2026-11-03T00:00:00Z"}]
    }


def test_evidence_inspection():
    result = KamarInspector().inspect_evidence(valid_payload())
    assert result[0]["supported"] is True


def test_missing_evidence_causes_review():
    payload = valid_payload()
    payload["claims"][0]["evidence_ids"] = ["UNKNOWN"]
    assert KamarEngine().process(payload)["decision"] == "REVIEW"


def test_contradiction_causes_review():
    payload = valid_payload()
    payload["contradictions"] = [{"description": "Conflict detected"}]
    assert KamarEngine().process(payload)["decision"] == "REVIEW"


def test_trace_audit():
    result = KamarInspector().audit_trace(valid_payload())
    assert result["valid"] is True
    assert result["event_count"] == 1


def test_artifact_integrity(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("KAMAR", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    result = KamarInspector().verify_artifact(artifact, digest)
    assert result["exists"] is True
    assert result["integrity"] is True


def test_reportability():
    result = KamarEngine().process(valid_payload())
    assert result["decision"] == "ALLOW"
    assert "evidence_inspection" in result
    assert "trace_audit" in result

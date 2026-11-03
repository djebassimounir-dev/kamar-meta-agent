import hashlib
import json
from pathlib import Path


class KamarInspector:
    def inspect_evidence(self, payload):
        evidence = payload.get("evidence", [])
        evidence_ids = {
            item.get("id") for item in evidence if item.get("id")
        }
        findings = []

        for claim in payload.get("claims", []):
            missing = [
                ref for ref in claim.get("evidence_ids", [])
                if ref not in evidence_ids
            ]
            findings.append({
                "claim": claim.get("text", ""),
                "supported": bool(claim.get("evidence_ids")) and not missing,
                "missing_evidence": missing
            })

        return findings

    def detect_contradictions(self, payload):
        return payload.get("contradictions", [])

    def audit_trace(self, payload):
        trace = payload.get("trace", [])
        valid = all(
            isinstance(event, dict)
            and "action" in event
            and "timestamp" in event
            for event in trace
        )
        return {"valid": valid, "event_count": len(trace)}

    def verify_artifact(self, file_path, expected_sha256=None):
        path = Path(file_path)
        if not path.is_file():
            return {"exists": False, "integrity": False}

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "exists": True,
            "sha256": digest,
            "integrity": (
                expected_sha256 is None or digest == expected_sha256
            )
        }

    def inspect(self, payload):
        evidence = self.inspect_evidence(payload)
        contradictions = self.detect_contradictions(payload)
        trace = self.audit_trace(payload)

        unsupported = [item for item in evidence if not item["supported"]]
        status = (
            "REVIEW" if unsupported or contradictions or not trace["valid"]
            else "ALLOW"
        )

        return {
            "decision": status,
            "evidence_inspection": evidence,
            "contradictions": contradictions,
            "trace_audit": trace
        }

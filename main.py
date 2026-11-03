#!/usr/bin/env python3
"""
KAMAR Meta-Agent — Evidence-Aware AI Audit Framework
Main Demonstration and Validation Script
"""

import json
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timezone

PROJECT_NAME = "KAMAR-META-AGENT"
VERSION = "1.0.0"
OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class KamarInspector:
    def inspect(self, payload):
        findings = []
        if not isinstance(payload, dict):
            return {"decision": "REVIEW", "reasons": ["payload_must_be_object"], "claims": [], "contradictions": [], "trace": {"valid": False, "event_count": 0}, "artifacts": []}

        reasons = []
        evidence = payload.get("evidence", [])
        claims = payload.get("claims", [])
        contradictions = payload.get("contradictions", [])
        trace = payload.get("trace", [])
        if not isinstance(evidence, list): evidence = []; reasons.append("evidence_must_be_list")
        if not isinstance(claims, list): claims = []; reasons.append("claims_must_be_list")
        if not isinstance(contradictions, list): contradictions = []; reasons.append("contradictions_must_be_list")
        if not isinstance(trace, list): trace = []; reasons.append("trace_must_be_list")

        ids = [item.get("id") for item in evidence if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates: reasons.append("duplicate_evidence_ids")
        evidence_ids = set(ids)
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                findings.append({"claim_index": index, "supported": False, "missing_evidence": [], "issue": "claim_must_be_object"})
                reasons.append("invalid_claim")
                continue
            refs = claim.get("evidence_ids", [])
            valid_refs = isinstance(refs, list) and all(isinstance(ref, str) and ref.strip() for ref in refs)
            missing = [ref for ref in refs if ref not in evidence_ids] if valid_refs else []
            supported = valid_refs and bool(refs) and not missing and bool(str(claim.get("text", "")).strip())
            issue = None if supported else ("invalid_evidence_references" if not valid_refs else "missing_or_empty_evidence")
            findings.append({"claim_id": claim.get("id", f"claim_{index+1}"), "text": claim.get("text", ""), "supported": bool(supported), "missing_evidence": missing, "issue": issue})
            if not supported: reasons.append("unsupported_claim")

        if contradictions: reasons.append("reported_contradictions")
        trace_valid = bool(trace) and all(isinstance(event, dict) and isinstance(event.get("action"), str) and event["action"].strip() and self._valid_timestamp(event.get("timestamp")) for event in trace)
        if not trace_valid: reasons.append("invalid_or_empty_trace")
        artifact_results = []
        for artifact in payload.get("artifacts", []):
            result = self.verify_artifact(artifact)
            artifact_results.append(result)
            if not result["integrity"]: reasons.append("artifact_integrity_failure")

        reasons = list(dict.fromkeys(reasons))
        return {"decision": "REVIEW" if reasons else "ALLOW", "reasons": reasons, "claims": findings, "contradictions": contradictions, "trace": {"valid": trace_valid, "event_count": len(trace)}, "duplicate_evidence_ids": duplicates, "artifacts": artifact_results}

    @staticmethod
    def _valid_timestamp(value):
        if not isinstance(value, str): return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False

    @staticmethod
    def verify_artifact(artifact):
        if not isinstance(artifact, dict) or not artifact.get("path"):
            return {"path": None, "exists": False, "integrity": False, "error": "invalid_artifact_spec"}
        path = Path(artifact["path"])
        if not path.is_file():
            return {"path": str(path), "exists": False, "integrity": False, "error": "file_not_found"}
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = artifact.get("sha256")
        ok = isinstance(expected, str) and digest.lower() == expected.lower()
        return {"path": str(path), "exists": True, "sha256": digest, "integrity": ok, "error": None if ok else "hash_missing_or_mismatch"}

def main():
    print("=" * 65)
    print(f"{PROJECT_NAME} v{VERSION} — DEMONSTRATION & VALIDATION")
    print("=" * 65)

    inspector = KamarInspector()

    # 1. REVIEW CASE: unsupported claim
    payload_review = {
        "claims": [
            {"id": "C1", "text": "The document indicates a 12% increase.", "evidence_ids": ["E1"]},
            {"id": "C2", "text": "The result is guaranteed in all cases.", "evidence_ids": []},
        ],
        "evidence": [
            {"id": "E1", "description": "Excerpt from user-provided report."}
        ],
        "contradictions": [],
        "trace": [
            {"action": "request_received", "timestamp": "2026-11-03T09:00:00Z"},
            {"action": "audit_completed", "timestamp": "2026-11-03T09:00:02Z"},
        ],
    }

    review_result = inspector.inspect(payload_review)
    assert review_result["decision"] == "REVIEW", "FAIL: incomplete payload should require REVIEW"
    assert "unsupported_claim" in review_result["reasons"], "FAIL: unsupported claim was not detected"

    print("\n[PASS] REVIEW scenario")
    print("Decision:", review_result["decision"])
    print("Reasons:", review_result["reasons"])

    # Write audit report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "framework": PROJECT_NAME,
        "version": VERSION,
        "scope_note": "Structural consistency of provided elements; no external semantic validation.",
        "result": review_result,
    }
    report_path = OUTPUT_DIR / "audit_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Audit report written: {report_path.resolve()}")

    # 2. ALLOW CASE: fully referenced claim and valid trace
    allow_payload = {
        "claims": [
            {
                "id": "C1",
                "text": "The report indicates a 12 percent increase.",
                "evidence_ids": ["E1"]
            }
        ],
        "evidence": [
            {
                "id": "E1",
                "description": "Reference excerpt from the supplied report."
            }
        ],
        "contradictions": [],
        "trace": [
            {"action": "request_received", "timestamp": "2026-11-03T09:00:00Z"},
            {"action": "audit_completed", "timestamp": "2026-11-03T09:00:02Z"}
        ]
    }

    allow_result = inspector.inspect(allow_payload)
    assert allow_result["decision"] == "ALLOW", f"FAIL: expected ALLOW, got {allow_result}"
    assert allow_result["claims"][0]["supported"] is True, "FAIL: valid evidence reference was not accepted"
    assert allow_result["trace"]["valid"] is True, "FAIL: valid trace was rejected"

    print("\n[PASS] ALLOW scenario")
    print("Decision:", allow_result["decision"])
    print("Claim supported:", allow_result["claims"][0]["supported"])
    print("Trace valid:", allow_result["trace"]["valid"])

    # 3. ARTIFACT INTEGRITY TEST
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "kamar_integrity_test.txt"
        test_file.write_text("KAMAR integrity validation", encoding="utf-8")

        expected_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()

        valid_artifact = inspector.verify_artifact({
            "path": str(test_file),
            "sha256": expected_hash
        })

        invalid_artifact = inspector.verify_artifact({
            "path": str(test_file),
            "sha256": "0" * 64
        })

        assert valid_artifact["integrity"] is True, "FAIL: valid artifact hash rejected"
        assert invalid_artifact["integrity"] is False, "FAIL: incorrect artifact hash accepted"

    print("\n[PASS] Artifact integrity")
    print("Valid hash accepted:", valid_artifact["integrity"])
    print("Incorrect hash rejected:", not invalid_artifact["integrity"])

    # 4. FINAL DEMO SUMMARY
    summary = {
        "framework": PROJECT_NAME,
        "version": VERSION,
        "validation": {
            "review_scenario": review_result["decision"] == "REVIEW",
            "allow_scenario": allow_result["decision"] == "ALLOW",
            "valid_artifact": valid_artifact["integrity"],
            "invalid_hash_rejected": not invalid_artifact["integrity"]
        },
        "all_checks_passed": True
    }

    summary["all_checks_passed"] = all(summary["validation"].values())
    summary_path = OUTPUT_DIR / "final_demo_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")

    print("\n" + "=" * 65)
    print("FINAL RESULTS")
    print("=" * 65)
    for name, passed in summary["validation"].items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    print("\nAll checks passed:", summary["all_checks_passed"])
    print(f"Summary written: {summary_path.resolve()}")
    print("\nKAMAR DEMONSTRATION COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    main()
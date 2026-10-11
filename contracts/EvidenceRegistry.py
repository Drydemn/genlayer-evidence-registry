# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""Multi-source claim attestations secured by GenLayer consensus.

Each case records a claim and two independent web sources. A leader extracts a
structured verdict, while validators repeat the same source-grounded analysis
and compare only the stable categorical fields. Free-form rationale is stored
for readers but is deliberately excluded from consensus comparison.
"""

import json
from dataclasses import dataclass

from genlayer import *
import genlayer.gl.vm as glvm


@allow_storage
@dataclass
class EvidenceCase:
    case_id: str
    creator: Address
    claim: str
    source_a: str
    source_b: str
    status: str
    verdict: str
    source_a_assessment: str
    source_b_assessment: str
    rationale: str


def normalize_result(raw_result) -> dict:
    """Validate the model response without capturing contract state."""
    if isinstance(raw_result, str):
        result = json.loads(raw_result)
    else:
        result = raw_result

    verdict = result.get("verdict", "")
    source_a = result.get("source_a", "")
    source_b = result.get("source_b", "")
    rationale = result.get("rationale", "")

    if verdict not in ("supported", "contradicted", "mixed", "insufficient"):
        raise Exception("Invalid verdict")
    if source_a not in ("supports", "contradicts", "unclear"):
        raise Exception("Invalid source A assessment")
    if source_b not in ("supports", "contradicts", "unclear"):
        raise Exception("Invalid source B assessment")
    if len(rationale) == 0 or len(rationale) > 800:
        raise Exception("Invalid rationale")

    return {
        "verdict": verdict,
        "source_a": source_a,
        "source_b": source_b,
        "rationale": rationale,
    }


class EvidenceRegistry(gl.Contract):
    cases: TreeMap[str, EvidenceCase]
    case_count: u256

    def __init__(self):
        self.cases = TreeMap()
        self.case_count = u256(0)

    def _validate_url(self, url: str) -> None:
        if len(url) < 12 or len(url) > 500:
            raise Exception("Source URL length is invalid")
        if not (url.startswith("https://") or url.startswith("http://")):
            raise Exception("Source URL must use HTTP or HTTPS")

    def _evaluate_sources(self, claim: str, source_a: str, source_b: str) -> dict:
        def leader_fn() -> dict:
            evidence_a = gl.nondet.web.render(source_a, mode="text")
            evidence_b = gl.nondet.web.render(source_b, mode="text")
            prompt = f"""
You are verifying one factual claim against two independent web sources.

Claim:
{claim}

Source A:
{evidence_a}

Source B:
{evidence_b}

Return JSON only with this schema:
{{
  "verdict": "supported" | "contradicted" | "mixed" | "insufficient",
  "source_a": "supports" | "contradicts" | "unclear",
  "source_b": "supports" | "contradicts" | "unclear",
  "rationale": "A concise source-grounded explanation"
}}

Rules:
- Judge only from the supplied source text.
- Use "supported" only when both sources support the claim.
- Use "contradicted" only when both sources contradict the claim.
- Use "mixed" when the sources materially disagree.
- Use "insufficient" when neither source provides enough evidence.
- Do not infer missing facts.
"""
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return normalize_result(raw)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, glvm.Return):
                return False
            independent = leader_fn()
            proposed = leader_result.calldata
            return (
                proposed["verdict"] == independent["verdict"]
                and proposed["source_a"] == independent["source_a"]
                and proposed["source_b"] == independent["source_b"]
            )

        return glvm.run_nondet_unsafe(leader_fn, validator_fn)

    @gl.public.write
    def create_case(
        self, case_id: str, claim: str, source_a: str, source_b: str
    ) -> None:
        if len(case_id) < 3 or len(case_id) > 80:
            raise Exception("Case ID length is invalid")
        if case_id in self.cases:
            raise Exception("Case already exists")
        if len(claim) < 10 or len(claim) > 500:
            raise Exception("Claim length is invalid")
        self._validate_url(source_a)
        self._validate_url(source_b)
        if source_a == source_b:
            raise Exception("Sources must be different")

        self.cases[case_id] = EvidenceCase(
            case_id=case_id,
            creator=gl.message.sender_address,
            claim=claim,
            source_a=source_a,
            source_b=source_b,
            status="pending",
            verdict="",
            source_a_assessment="",
            source_b_assessment="",
            rationale="",
        )
        self.case_count = u256(int(self.case_count) + 1)

    @gl.public.write
    def resolve_case(self, case_id: str) -> dict:
        if case_id not in self.cases:
            raise Exception("Case not found")
        case = self.cases[case_id]
        if case.status == "resolved":
            raise Exception("Case already resolved")

        result = self._evaluate_sources(case.claim, case.source_a, case.source_b)
        case.status = "resolved"
        case.verdict = result["verdict"]
        case.source_a_assessment = result["source_a"]
        case.source_b_assessment = result["source_b"]
        case.rationale = result["rationale"]
        return result

    @gl.public.view
    def get_case(self, case_id: str) -> dict:
        if case_id not in self.cases:
            raise Exception("Case not found")
        case = self.cases[case_id]
        return {
            "case_id": case.case_id,
            "creator": case.creator.as_hex,
            "claim": case.claim,
            "source_a": case.source_a,
            "source_b": case.source_b,
            "status": case.status,
            "verdict": case.verdict,
            "source_a_assessment": case.source_a_assessment,
            "source_b_assessment": case.source_b_assessment,
            "rationale": case.rationale,
        }

    @gl.public.view
    def get_case_count(self) -> int:
        return int(self.case_count)

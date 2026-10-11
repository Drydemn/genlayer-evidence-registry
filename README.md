# Evidence Registry

`EvidenceRegistry.py` is a reusable Intelligent Contract primitive for creating
source-backed claim attestations.

## Why it exists

Many applications need more than an LLM opinion. They need a durable record of
what was checked, which sources were used, and which fields validators agreed
on. Evidence Registry separates those concerns:

- deterministic code validates inputs and stores case state;
- the leader reads two independent web sources and proposes structured output;
- validators independently repeat the source-grounded task;
- consensus compares only the stable categorical decision fields;
- the human-readable rationale is preserved without requiring identical prose.

## Verdict model

| Verdict | Meaning |
| --- | --- |
| `supported` | Both sources support the claim. |
| `contradicted` | Both sources contradict the claim. |
| `mixed` | The sources materially disagree. |
| `insufficient` | Neither source contains enough evidence. |

Each source is also classified as `supports`, `contradicts`, or `unclear`.

## Public methods

- `create_case(case_id, claim, source_a, source_b)` creates an immutable pending
  case. URLs must be distinct HTTP(S) sources.
- `resolve_case(case_id)` runs the multi-source consensus workflow and stores
  the result. Resolution is permissionless and one-time.
- `get_case(case_id)` returns the complete source and verdict record.
- `get_case_count()` returns the number of registered cases.

## Consensus design

The validator never trusts the leader's formatting or conclusion. It fetches
the same sources, runs an independent extraction, validates the response schema,
and compares `verdict`, `source_a`, and `source_b`. Rationale may vary because it
is explanatory rather than consensus-critical.

## Testing

```powershell
.venv\Scripts\python.exe -m pytest tests\direct\test_evidence_registry.py -v
```

The direct-mode suite covers storage, duplicate protection, URL validation,
consensus-backed resolution, one-time finality, and malformed model output.

## Deployment

```powershell
genlayer network set testnet-bradbury
genlayer deploy --contract contracts/EvidenceRegistry.py
```

Deployment creates a consensus transaction and requires a funded testnet
account. Review current network configuration before deploying.

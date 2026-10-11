"""Direct-mode tests for the multi-source EvidenceRegistry contract."""

import json


CONTRACT_PATH = "contracts/EvidenceRegistry.py"
SOURCE_A = "https://source-a.example/report"
SOURCE_B = "https://source-b.example/report"


def _mock_sources(vm, result):
    vm.mock_web(
        r".*source-a\.example.*",
        {"status": 200, "body": "Source A confirms the launch date was 10 May."},
    )
    vm.mock_web(
        r".*source-b\.example.*",
        {"status": 200, "body": "Source B also lists the launch date as 10 May."},
    )
    vm.mock_llm(r".*verifying one factual claim.*", json.dumps(result))


def test_create_case_records_creator_and_sources(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice

    contract.create_case(
        "launch-date",
        "The product launched on 10 May 2026.",
        SOURCE_A,
        SOURCE_B,
    )

    case = contract.get_case("launch-date")
    assert case["status"] == "pending"
    assert case["claim"] == "The product launched on 10 May 2026."
    assert case["source_a"] == SOURCE_A
    assert case["source_b"] == SOURCE_B
    assert contract.get_case_count() == 1


def test_duplicate_case_is_rejected(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT_PATH)
    contract.create_case("case-001", "A sufficiently long factual claim.", SOURCE_A, SOURCE_B)

    with direct_vm.expect_revert("Case already exists"):
        contract.create_case(
            "case-001", "Another sufficiently long claim.", SOURCE_A, SOURCE_B
        )


def test_sources_must_be_distinct_and_http(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT_PATH)

    with direct_vm.expect_revert("Sources must be different"):
        contract.create_case(
            "same-source", "A sufficiently long factual claim.", SOURCE_A, SOURCE_A
        )

    with direct_vm.expect_revert("Source URL must use HTTP or HTTPS"):
        contract.create_case(
            "bad-source",
            "A sufficiently long factual claim.",
            "file:///private/report",
            SOURCE_B,
        )


def test_resolve_case_stores_consensus_fields(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT_PATH)
    contract.create_case(
        "launch-date",
        "The product launched on 10 May 2026.",
        SOURCE_A,
        SOURCE_B,
    )
    _mock_sources(
        direct_vm,
        {
            "verdict": "supported",
            "source_a": "supports",
            "source_b": "supports",
            "rationale": "Both sources independently report the same launch date.",
        },
    )

    result = contract.resolve_case("launch-date")
    case = contract.get_case("launch-date")

    assert result["verdict"] == "supported"
    assert case["status"] == "resolved"
    assert case["source_a_assessment"] == "supports"
    assert case["source_b_assessment"] == "supports"
    assert "independently" in case["rationale"]


def test_resolved_case_cannot_be_resolved_twice(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT_PATH)
    contract.create_case(
        "launch-date",
        "The product launched on 10 May 2026.",
        SOURCE_A,
        SOURCE_B,
    )
    _mock_sources(
        direct_vm,
        {
            "verdict": "supported",
            "source_a": "supports",
            "source_b": "supports",
            "rationale": "Both sources report the same date.",
        },
    )
    contract.resolve_case("launch-date")

    with direct_vm.expect_revert("Case already resolved"):
        contract.resolve_case("launch-date")


def test_invalid_llm_schema_is_rejected(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT_PATH)
    contract.create_case(
        "launch-date",
        "The product launched on 10 May 2026.",
        SOURCE_A,
        SOURCE_B,
    )
    _mock_sources(
        direct_vm,
        {
            "verdict": "probably",
            "source_a": "supports",
            "source_b": "supports",
            "rationale": "This enum is deliberately invalid.",
        },
    )

    with direct_vm.expect_revert("Invalid verdict"):
        contract.resolve_case("launch-date")

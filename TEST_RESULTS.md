# Verification Results

- Date: 2026-10-11 (Asia/Seoul)
- Python: 3.12.12
- GenLayer test plugin: 0.29.2
- GenVM runner: v0.2.16
- Official runner bundle SHA-256: `4f0b358ec98ec148be9b95cdfb0f0e1a6cbe64da0194fdfac3fffc6f5d1d93e2`
- Syntax compilation: passed
- Direct-mode contract tests: **6 passed**

Command used:

```powershell
.venv\Scripts\python.exe -m pytest -p no:cacheprovider tests\direct\test_evidence_registry.py -v
```

Covered behavior:

1. Case creation and storage
2. Duplicate-case rejection
3. Source URL and distinctness validation
4. Consensus-backed resolution and persistence
5. One-time resolution finality
6. Invalid model-response rejection

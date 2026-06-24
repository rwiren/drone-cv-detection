# Contributing

## Branching Strategy

- **`main`**: Protected, stable code only. Push via merge requests.
- **`develop`**: Integration branch for testing before merge to main.
- **`feature/*`**: New capabilities (e.g., `feature/obb-training`).
- **`fix/*`**: Bug fixes (e.g., `fix/thermal-alignment`).

## Development Setup

```bash
python3 -m venv ~/cv_env
source ~/cv_env/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip install -e ".[dev]"          # test + tooling extras
# pip install -e ".[mqtt]"        # optional: live MQTT monitor support
```

## Code Standards

- Python 3.11+ (3.12 recommended)
- Docstrings on all public functions
- Type hints where practical
- No credentials or tokens in code — use environment variables or CLI arguments

## Data Policy

- **Video files** (`.MP4`): Never committed. Keep in `data/` (gitignored, symlinked locally).
- **Model weights** (`.pt`): Not in git. Document training procedure so they can be reproduced.
- **SRT telemetry**: Can be committed (small text files) — place in `data/`.
- **Sample images** in `docs/samples/`: Keep under 1MB each. Only commit factual, verified results.
- **Large artifacts** (`data/`, `outputs/`, `models/`): keep only reproducibility-critical, small examples in git. Store large experiment outputs in GitHub Releases/LFS or external storage and link them from docs.

## Merge Request Checklist

- [ ] Code runs without errors
- [ ] Sample outputs are factually correct (no misleading visualizations)
- [ ] README/CHANGELOG updated if adding features
- [ ] No large binary files committed (check with `git diff --stat`)
- [ ] New artifacts follow repository storage policy (LFS/releases/external for large files)
- [ ] Limitations documented for any new capability

## Accuracy Standards

When adding new detection/analysis capabilities:
1. Document what confidence threshold was used
2. Report false positive rate if measured
3. Note altitude/distance limitations
4. Do not present proof-of-concept results as production-ready

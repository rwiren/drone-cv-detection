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
pip install ultralytics opencv-python-headless sahi pymupdf pytesseract
```

## Code Standards

- Python 3.12+
- Docstrings on all public functions
- Type hints where practical
- No credentials or tokens in code — use environment variables or CLI arguments

## Data Policy

- **Video files** (`.MP4`): Never committed. Keep in `data/` (gitignored, symlinked locally).
- **Model weights** (`.pt`): Not in git. Document training procedure so they can be reproduced.
- **SRT telemetry**: Can be committed (small text files) — place in `data/`.
- **Sample images** in `docs/samples/`: Keep under 1MB each. Only commit factual, verified results.

## Merge Request Checklist

- [ ] Code runs without errors
- [ ] Sample outputs are factually correct (no misleading visualizations)
- [ ] README/CHANGELOG updated if adding features
- [ ] No large binary files committed (check with `git diff --stat`)
- [ ] Limitations documented for any new capability

## Accuracy Standards

When adding new detection/analysis capabilities:
1. Document what confidence threshold was used
2. Report false positive rate if measured
3. Note altitude/distance limitations
4. Do not present proof-of-concept results as production-ready

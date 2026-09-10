# student-ml-api

A minimal ML inference service used to demonstrate a production-style MLOps workflow:

```
feature branch → Pull Request → CI (tests + Docker build) → review → merge to main
→ semantic version tag → release workflow → versioned image in GHCR
```

## Development policy

- `main` is protected. All changes arrive through Pull Requests.
- Every Pull Request must pass CI (unit tests and Docker build validation) before merging.
- Releases are created by pushing a semantic-version tag (`vX.Y.Z`). The release workflow
  builds the image and publishes it to `ghcr.io`. Images are never pushed by hand.

## API

| Method | Path | Example response |
|---|---|---|
| `GET` | `/health` | `{"status": "healthy", "application": "student-ml-api", "application_version": "1.1.0", "model_version": "model-1"}` |
| `POST` | `/predict` | `{"value": 10}` → `{"input": 10, "prediction": 20}` |

Interactive docs are served at `/docs`.

## Run a released image

```bash
docker pull ghcr.io/abdullah8168/student-ml-api:1.1.0
docker run -d --name student-ml-api -p 5000:5000 ghcr.io/abdullah8168/student-ml-api:1.1.0
curl http://localhost:5000/health
```

Available tags: `1.0.0`, `1.1.0`, `latest`, plus one short-commit-SHA tag per release.
Roll back by running an earlier version tag, e.g. `:1.0.0`.

## Develop locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
uvicorn app:app --host 0.0.0.0 --port 5000
```

## Release a new version

1. Bump `VERSION` in a feature-branch PR and merge it after CI passes.
2. `git checkout main && git pull`
3. `git tag -a vX.Y.Z -m "Release X.Y.Z" && git push origin vX.Y.Z`

The workflow refuses to publish if the tag does not match `VERSION`.

See [docs/REPORT.md](docs/REPORT.md) for the full assignment report and evidence.

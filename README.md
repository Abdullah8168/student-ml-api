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

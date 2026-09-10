# student-ml-api: MLOps CI/CD Assignment Report

| | |
|---|---|
| Repository | https://github.com/Abdullah8168/student-ml-api |
| Registry | `ghcr.io/abdullah8168/student-ml-api` (public GHCR package) |
| Framework | FastAPI + uvicorn, Python 3.12 |
| Releases | [`v1.0.0`](https://github.com/Abdullah8168/student-ml-api/releases/tag/v1.0.0), [`v1.1.0`](https://github.com/Abdullah8168/student-ml-api/releases/tag/v1.1.0) |

Raw command output for every section is kept in [`docs/evidence/`](evidence/).

---

## 1. Delivery pipeline

```
feature/* branch ──► Pull Request ──► CI (ci.yml) ──► review ──► merge commit on main
                                       │ Unit Tests                     │
                                       │ Docker Build Validation        ▼
                                       └ (never pushes)          git tag vX.Y.Z
                                                                        │
                                                          Release (release.yml)
                                                          test → derive version → GHCR login
                                                          → build → tag → push → GitHub Release
                                                                        │
                                                                        ▼
                                          ghcr.io/abdullah8168/student-ml-api:{X.Y.Z, latest, <sha7>}
```

## 2. Application and tests (Parts 1–2)

| Endpoint | Behaviour |
|---|---|
| `GET /health` (1.0.0) | `{"status":"healthy","application":"student-ml-api","version":"1.0.0"}` |
| `GET /health` (1.1.0) | `{"status":"healthy","application":"student-ml-api","application_version":"1.1.0","model_version":"model-1"}` |
| `POST /predict` | `{"value": 10}` → `{"input": 10, "prediction": 20}` (placeholder model `y = 2x`) |

- The application version is read from the `VERSION` file at startup, so the file is the single source of truth. The release workflow refuses to publish when the git tag and `VERSION` disagree.
- The request model uses `StrictInt | StrictFloat`, so `"10"`, `"abc"`, `true`, `null` and lists are rejected with **422** rather than silently coerced.
- `tests/test_app.py`: 14 test cases (13 in 1.0.0) covering health, successful prediction (several values), missing input, invalid input, and a missing body.
- Runtime dependencies are in `requirements.txt`. Test tools (`pytest`, `httpx`) are in `requirements-dev.txt` so they never ship in the image.

## 3. Git workflow (Parts 3, 8, 18)

- No development commit was pushed to `main`. The only non-merge commit on `main` is GitHub's own `Initial commit`, created when the repository was made. Every other change arrived through a PR.
- Commits follow Conventional Commits (`feat:`, `test:`, `fix:`, `build:`, `ci:`, `docs:`, `chore:`).

```
*   1cfb504 Merge pull request #2 from Abdullah8168/feature/model-metadata   ← tag v1.1.0
|\
| * 03c5d51 ci: upgrade GitHub Actions to Node 24 majors
| * c8dfd19 chore(release): bump version to 1.1.0
| * 1c0d4f5 test: update health tests for model metadata
| * 1885b86 feat: add model metadata to health endpoint
|/
*   a7fc195 Merge pull request #1: prediction API v1.0.0                     ← tag v1.0.0
|\
| * 0f1271b fix: correct health endpoint test
| * 31fc9cc test: deliberately break health assertion to demonstrate CI gate
| * a35b5f5 ci: add tag-triggered release workflow
| * 210f7d0 ci: add pull request CI workflow
| * a2a809e build: add production Dockerfile and .dockerignore
| * 3541de8 test: add API unit tests
| * 231ae53 feat: add prediction endpoint
| * ee2ca8a chore: enforce LF line endings via .gitattributes
| * c043bbf docs: document development policy in README and add .gitignore
|/
* c0e584f Initial commit
```

### Merge strategy: **Merge Commit**

The repository is configured to allow **only** merge commits (squash and rebase are disabled). Reasons:

1. **Traceability.** Each release corresponds to exactly one merge commit on `main`, which carries the PR number (`#1` → `a7fc195`, `#2` → `1cfb504`). That commit is what the `vX.Y.Z` tag points to and what the image's `revision` label records.
2. **History stays honest.** The individual feature commits are kept, including the deliberately failing commit `31fc9cc` and its fix `0f1271b`. Squashing would erase the evidence that CI blocked a broken change.
3. **No rewritten SHAs.** Rebase-merging creates new SHAs on `main` that differ from the ones CI tested on the PR branch.

The trade-off is a non-linear history. It is acceptable because each feature is bracketed by one merge commit and branches are short-lived.

## 4. Pull Requests (Part 4)

| PR | Branch | Result |
|---|---|---|
| [#1](https://github.com/Abdullah8168/student-ml-api/pull/1) | `feature/prediction-api` | Merged → `a7fc195` → `v1.0.0` |
| [#2](https://github.com/Abdullah8168/student-ml-api/pull/2) | `feature/model-metadata` | Merged → `1cfb504` → `v1.1.0` |
| #3 | `docs/assignment-report` | This report |

Every PR description has **Summary, Changes, Testing Performed, Docker Impact, Checklist** (template: `.github/pull_request_template.md`). Each PR was reviewed before merge. GitHub does not let an author formally approve their own PR, so reviews were recorded as review comments.

## 5. CI workflow and deliberate failure (Parts 5–6)

`.github/workflows/ci.yml` runs on `pull_request → main` (and manually via `workflow_dispatch`). It has two independent jobs, and both are required status checks:

| Job | Steps |
|---|---|
| **Unit Tests** | Code checkout → Python setup (3.12, pip cache) → Dependency installation → `pytest -v` |
| **Docker Build Validation** | Code checkout → Buildx → `docker build` with `push: false` → run container and smoke-test `/health` and `/predict` |

If either `pytest` or `docker build` fails, that job fails, the PR's checks are red, and branch protection blocks the merge.

**Deliberate failure (PR #1):**

| Run | Commit | Result |
|---|---|---|
| [34450848641](https://github.com/Abdullah8168/student-ml-api/actions/runs/34450848641) | `a35b5f5` initial push | ✅ success |
| [34450923188](https://github.com/Abdullah8168/student-ml-api/actions/runs/34450923188) | `31fc9cc` `assert data["status"] == "wrong"` | ❌ **Unit Tests failed**. PR `mergeStateStatus = BLOCKED` |
| [34451013287](https://github.com/Abdullah8168/student-ml-api/actions/runs/34451013287) | `0f1271b` `fix: correct health endpoint test` | ✅ success. PR `mergeStateStatus = CLEAN` |

Failure log excerpt ([full log](evidence/part06-failed-ci-log.txt)):
```
tests/test_app.py::test_health_returns_status_and_version FAILED
>       assert data["status"] == "wrong"
E       AssertionError: assert 'healthy' == 'wrong'
```

## 6. Branch protection on `main` (Part 7)

Configured through the branch-protection API before the first PR was opened:

| Setting | Value | Why |
|---|---|---|
| Require a pull request before merging | ✅ | No change reaches `main` without a PR |
| Required approvals | 0 | Single-developer repository: GitHub forbids approving your own PR, so 1 would deadlock. In a team this should be ≥ 1. |
| Dismiss stale approvals on new commits | ✅ | A review applies to the code that was reviewed |
| Require status checks to pass | ✅ `Unit Tests`, `Docker Build Validation` | CI must be green |
| Require branches to be up to date (strict) | ✅ | Checks must have run against the latest `main` |
| Require conversation resolution | ✅ | Review comments cannot be ignored |
| **Do not allow bypassing (enforce for admins)** | ✅ | Even the repository owner cannot push to `main` directly |
| Allow force pushes | ❌ | History on `main` is immutable |
| Allow deletions | ❌ | `main` cannot be deleted |
| Allowed merge methods (repo setting) | Merge commit only | See §3 |
| Automatically delete head branches | ✅ | Merged feature branches are cleaned up |

## 7. Dockerfile (Part 9)

| Practice | Implementation |
|---|---|
| Explicit base version | `FROM python:3.12.8-slim`, never `latest` |
| `WORKDIR` | `/app` |
| Correct `COPY` ordering | `COPY requirements.txt` → `RUN pip install` → `COPY VERSION app.py` |
| `--no-cache-dir` | `pip install --no-cache-dir -r requirements.txt` (no pip cache in the image) |
| `EXPOSE` | `5000` |
| Appropriate `CMD` | exec form: `["uvicorn","app:app","--host","0.0.0.0","--port","5000"]` |
| Extras | non-root `appuser` (uid 10001), `HEALTHCHECK` on `/health`, `PYTHONUNBUFFERED`, OCI labels declared **last** so per-build values don't invalidate the cache |

`.dockerignore` excludes `.git`, `.github`, `__pycache__`, `*.pyc`, `.venv`, `.env*`, tests, docs, dev requirements and editor files. The build context is about 1.5 kB.

## 8. Local build and inspection (Parts 10–11)

```
docker build -t student-ml-api:1.0.0 .
docker run -d --name student-ml-api -p 5000:5000 student-ml-api:1.0.0
curl http://localhost:5000/health
{"status":"healthy","application":"student-ml-api","version":"1.0.0"}
```

| Item | Value | Source |
|---|---|---|
| Container ID | `ce8a0f6058cd8d58428ebf602666f429888e176328badeab79e13a3f4fdfe38b` | `docker ps` / `docker inspect .Id` |
| Image ID | `sha256:d72a2c08dc12de9ca16b166d23c46e8c4c532b5a5361e8fa122132bc7c0da3b5` | `docker images` / `docker inspect .Image` |
| Exposed port | `5000/tcp`, published as `0.0.0.0:5000->5000/tcp` | `.Config.ExposedPorts`, `.NetworkSettings.Ports` |
| Running command | `uvicorn app:app --host 0.0.0.0 --port 5000` (PID 1) | `.Config.Cmd`, `docker exec … ps` |
| Working directory | `/app` | `.Config.WorkingDir`, `docker exec … pwd` |
| User | `appuser` | `.Config.User`, `whoami` |
| Health | `healthy` | `.State.Health.Status` |

Evidence: [`part11-*`](evidence/).

## 9. Release workflow (Parts 12–16)

`.github/workflows/release.yml` triggers **only** on `push: tags: ["v*.*.*"]`.

| Stage | Implementation |
|---|---|
| Checkout | `actions/checkout` |
| Run tests | separate `Unit Tests` job. `publish` has `needs: test` |
| Derive version | `VERSION="${GITHUB_REF_NAME#v}"` turns `v1.1.0` into `1.1.0`. It is validated against `^[0-9]+\.[0-9]+\.[0-9]+$` and must equal the `VERSION` file. **No version is hard-coded in YAML.** |
| Authenticate | `docker/login-action` → `ghcr.io` with the short-lived `secrets.GITHUB_TOKEN` (job permission `packages: write`). No stored password. |
| Build | `docker/build-push-action` with build args `APP_VERSION`, `VCS_REF`, `BUILD_DATE`, `SOURCE_URL` |
| Apply tags | `docker/metadata-action`: `type=semver,pattern={{version}}`, `latest`, `type=sha,format=short` |
| Push | `push: true` |
| Verify | pull the pushed image, print labels, run it, `curl /health`, check it returns the version |
| Record | job summary and GitHub Release containing tags, commit and digest |

**Registry after `v1.0.0`** ([run 34451569007](https://github.com/Abdullah8168/student-ml-api/actions/runs/34451569007)):

```
student-ml-api
├── 1.0.0    sha256:9737f81291ff8ffe11808c811e169540dc460cff7c3e5997eff19a10e068ec10
├── latest   sha256:9737f81291ff8ffe11808c811e169540dc460cff7c3e5997eff19a10e068ec10
└── a7fc195  sha256:9737f81291ff8ffe11808c811e169540dc460cff7c3e5997eff19a10e068ec10
```

## 10. Artifact reproducibility (Part 17)

```
docker rm -f student-ml-api
docker rmi student-ml-api:1.0.0                     # local build deleted
docker pull ghcr.io/abdullah8168/student-ml-api:1.0.0
  Digest: sha256:9737f81291ff8ffe11808c811e169540dc460cff7c3e5997eff19a10e068ec10
docker run -d --name student-ml-api -p 5000:5000 ghcr.io/abdullah8168/student-ml-api:1.0.0
curl http://localhost:5000/health
  {"status":"healthy","application":"student-ml-api","version":"1.0.0"}
```

The image was built on a GitHub-hosted runner, stored in GHCR, and run on a different machine without rebuilding. The digest proves it is byte-for-byte the artifact CI produced. Evidence: [`part17-reproducibility.txt`](evidence/part17-reproducibility.txt).

## 11. Release 1.1.0 (Part 19)

After PR #2 was merged, `v1.1.0` was tagged ([run 34452635821](https://github.com/Abdullah8168/student-ml-api/actions/runs/34452635821)):

```
student-ml-api
├── 1.0.0    sha256:9737f812…68ec10   ← still available
├── a7fc195  sha256:9737f812…68ec10
├── 1.1.0    sha256:703c620d09e42cdbfafebe0f57343f6af9444225ec8fc1a896d7c30df08c9ff9
├── 1cfb504  sha256:703c620d…c9ff9
└── latest   sha256:703c620d…c9ff9    ← latest → 1.1.0
```

## 12. Rollback (Part 20)

1.1.0 was running as "production". Assume it has an issue:

```
docker stop student-ml-api && docker rm student-ml-api
docker pull ghcr.io/abdullah8168/student-ml-api:1.0.0      # local copy had been deleted
docker run -d --name student-ml-api -p 5000:5000 ghcr.io/abdullah8168/student-ml-api:1.0.0
curl http://localhost:5000/health
  {"status":"healthy","application":"student-ml-api","version":"1.0.0"}
```

The rollback took **12 s** wall-clock, with no source change and no rebuild. The running container reports digest `sha256:9737f812…` and label `revision=a7fc195…`. Evidence: [`part20-rollback.txt`](evidence/part20-rollback.txt).

**Why this is easier than `git clone && pip install && python app.py`:**

- **No rebuild, no drift.** The old image is the exact artifact that was tested and ran before. Re-installing from source re-resolves dependencies (transitive packages are not pinned here, e.g. `pydantic`) and can pull different versions than last time. It also depends on PyPI being reachable and on the host's Python version and OS libraries.
- **One atomic operation.** Changing an image tag is a single step that can be repeated. A source deployment has many steps that can each fail halfway, leaving a mixed environment.
- **Speed.** The rollback only pulls cached layers. It doesn't clone, compile or install anything.
- **Known identity.** A tag or digest identifies exactly what is running. With `python app.py`, what is running depends on whatever state the server was in.

## 13. Traceability for 1.1.0 (Part 21)

| Link | Value |
|---|---|
| Pull Request | [#2](https://github.com/Abdullah8168/student-ml-api/pull/2) `feature/model-metadata` |
| CI run on the PR | [34451945446](https://github.com/Abdullah8168/student-ml-api/actions/runs/34451945446) ✅ |
| Merge commit SHA | `1cfb504d66b6e1fad5face58a20f313bcc313137` |
| Git tag | `v1.1.0` → `1cfb504d66b6e1fad5face58a20f313bcc313137` |
| Release run | [34452635821](https://github.com/Abdullah8168/student-ml-api/actions/runs/34452635821) ✅ |
| Docker image tags | `ghcr.io/abdullah8168/student-ml-api:1.1.0`, `:1cfb504`, `:latest` |
| Image digest | `sha256:703c620d09e42cdbfafebe0f57343f6af9444225ec8fc1a896d7c30df08c9ff9` |
| Label inside the image | `org.opencontainers.image.revision=1cfb504d66b6e1fad5face58a20f313bcc313137` |

The chain can be walked in both directions. From a running container, `docker inspect` gives the revision, which leads to the merge commit and then to PR #2. From PR #2, the merge commit leads to the tag and then the image.

## 14. CI vs. release separation (Part 22)

| | CI (`ci.yml`) | Release (`release.yml`) |
|---|---|---|
| Trigger | Pull Request → `main` | `v*.*.*` tag push |
| Does | test, validate, build-check | test, build, version, publish |
| Registry | no login, `push: false` | login with `GITHUB_TOKEN`, push |
| Permissions | `contents: read` | `packages: write`, `contents: write` |

**Why not publish images from every Pull Request:**

- **Unreviewed code would become deployable.** A PR is a proposal. Publishing it would place unapproved and possibly broken code in the same registry that production pulls from.
- **Security.** Publishing needs write credentials. PRs (especially from forks) run code the maintainers haven't reviewed, so giving them registry write access invites supply-chain attacks. GitHub deliberately gives fork PRs a read-only token.
- **Registry clutter and cost.** Every push to every PR would create images that nobody will ever run, which makes retention and clean-up harder.
- **Ambiguous versions.** A PR build has no release version. Only a tag on reviewed code in `main` should create `X.Y.Z`, so a version number always means "reviewed, merged, tested".
- **Build once, promote.** The release image is built once from the merge commit and the same digest is promoted everywhere. PR images would be built from a pre-merge state that never exists on `main`.

## 15. OCI image metadata (Part 23)

The Dockerfile declares `org.opencontainers.image.{title,description,version,revision,created,source,url}` from build args, and the release workflow fills them in:

```
$ docker inspect ghcr.io/abdullah8168/student-ml-api:1.0.0 --format '{{json .Config.Labels}}'
{"org.opencontainers.image.created":"2026-09-10T07:46:22Z",
 "org.opencontainers.image.description":"ML inference API (FastAPI)",
 "org.opencontainers.image.revision":"a7fc195fd385e2ca143d4e87696a56e30cadc122",
 "org.opencontainers.image.source":"https://github.com/Abdullah8168/student-ml-api",
 "org.opencontainers.image.title":"student-ml-api",
 "org.opencontainers.image.url":"https://github.com/Abdullah8168/student-ml-api",
 "org.opencontainers.image.version":"1.0.0"}
```

`org.opencontainers.image.source` also links the GHCR package to the repository.

## 16. Commit-SHA image tag (Part 24)

Each release also publishes `:<short-sha>` (`:a7fc195`, `:1cfb504`) through `type=sha,format=short`.

Benefits:

- **Stable.** `latest` moves with every release, but a SHA tag always refers to the build of one specific commit, so "what's running?" has an exact answer.
- **Direct lookup.** `git show 1cfb504` shows the exact source of the `:1cfb504` image, with no need to map version to tag to commit.
- **Works for non-release builds.** The same scheme can tag builds from `main` or hotfix candidates that have no semantic version yet, so they can be tested and promoted by SHA.
- **Easy to read.** Unlike a digest (`sha256:…`), the tag is human-readable and meaningful to developers, while still being unique.

## 17. Build cache experiment (Part 25)

Three builds with `--progress=plain` ([evidence](evidence/)):

| Step | Build 1: only `app.py` changed | Build 2: `requirements.txt` changed |
|---|---|---|
| `FROM python:3.12.8-slim` | cached | cached |
| `WORKDIR /app` | CACHED | CACHED |
| `RUN useradd …` | CACHED | CACHED |
| `COPY requirements.txt .` | CACHED | **rebuilt** |
| `RUN pip install …` | **CACHED** | **rebuilt: 13.9 s** |
| `COPY VERSION app.py ./` | **rebuilt** | rebuilt |

Each layer's cache key depends on its parent layer and its own inputs. When a layer changes, every layer after it is rebuilt.

With the order used here:
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
```
a code-only change (the common case) invalidates only the final `COPY`. The expensive `pip install` layer is reused, so rebuilds take under a second instead of about 14 s, and CI with a `type=gha` layer cache benefits the same way.

With `COPY . .` followed by `RUN pip install …`, **any** file change (a single line of `app.py`, even a README if it isn't ignored) changes the `COPY . .` layer. That forces `pip install` to run again on every build. It wastes CI minutes and network, and each rebuild can resolve slightly different transitive dependency versions, which undermines reproducibility.

## 18. Failure analysis (Part 26)

Five failures were reproduced deliberately. Evidence: [`part06-failed-ci-log.txt`](evidence/part06-failed-ci-log.txt), [`part26-f1-f2.txt`](evidence/part26-f1-f2.txt), [`part26-f3-f4.txt`](evidence/part26-f3-f4.txt).

### 18.1 Failed pytest (in CI)
- **Symptom:** PR #1 showed a red ❌ "Unit Tests" check and the merge button was blocked (`mergeStateStatus: BLOCKED`).
- **Root cause:** commit `31fc9cc` changed the assertion to `data["status"] == "wrong"`, but the API correctly returns `"healthy"`.
- **Evidence:** run 34450923188: `AssertionError: assert 'healthy' == 'wrong'`, `1 failed, 12 passed`.
- **Correction:** `0f1271b fix: correct health endpoint test` restored `== "healthy"`, run 34451013287 passed, and the PR became mergeable.

### 18.2 Application bound to 127.0.0.1
- **Symptom:** the container is `Up` and `docker ps` shows `0.0.0.0:5002->5000/tcp`, but `curl http://localhost:5002/health` gives `curl: (52) Empty reply from server`.
- **Root cause:** uvicorn was started with `--host 127.0.0.1`, which is the loopback interface *inside the container's network namespace*. Docker's port forwarding arrives on the container's `eth0` interface, where nothing is listening.
- **Evidence:** `docker logs` shows `Uvicorn running on http://127.0.0.1:5000`. A request from *inside* the container (`docker exec … urllib …/health`) succeeds, which shows the app itself works.
- **Correction:** bind to all interfaces: `--host 0.0.0.0` (this is what the Dockerfile's `CMD` does).

### 18.3 Wrong container port
- **Symptom:** `docker run -p 5003:8000 …` starts fine, but `curl localhost:5003/health` gives `Empty reply from server`.
- **Root cause:** the mapping sends host port 5003 to container port **8000**, but the app listens on **5000**.
- **Evidence:** `docker ps` shows `5000/tcp, 0.0.0.0:5003->8000/tcp`. `.Config.ExposedPorts` = `{"5000/tcp":{},"8000/tcp":{}}`. The logs show `running on http://0.0.0.0:5000`.
- **Correction:** map to the port the app actually uses: `-p <host>:5000`. `EXPOSE 5000` documents that port.

### 18.4 Missing dependency
- **Symptom:** `docker build` **succeeds**, but `docker run` fails immediately: `exec: "uvicorn": executable file not found in $PATH`. The container stays in `Created` state with `ExitCode=127`.
- **Root cause:** `uvicorn` was removed from `requirements.txt`. Nothing at build time imports or runs the server, so the build cannot detect it.
- **Evidence:** [`part26-f3-f4.txt`](evidence/part26-f3-f4.txt), `docker inspect` `.State.Error`.
- **Correction:** restore `uvicorn==0.34.0`. Prevention: the CI **Docker Build Validation** job doesn't stop at `docker build`. It *runs* the image and curls `/health`, so this failure would turn the PR red.

### 18.5 Incorrect image tag
- **Symptom:** `docker pull ghcr.io/abdullah8168/student-ml-api:v1.0.0` gives `manifest unknown`, and `docker pull ghcr.io/Abdullah8168/…` gives `invalid reference format: repository name must be lowercase`.
- **Root cause:** (a) the *git* tag is `v1.0.0`, but the *image* tag is the derived version `1.0.0`. (b) Docker image references must be lowercase, but the GitHub username contains capitals.
- **Evidence:** registry tag list: `1.0.0, latest, a7fc195, 1.1.0, 1cfb504`.
- **Correction:** pull `ghcr.io/abdullah8168/student-ml-api:1.0.0`. The workflow prevents both problems: `${GITHUB_REF_NAME#v}` strips the `v` and `${GITHUB_REPOSITORY_OWNER,,}` lowercases the owner.

## 19. Core principle

> Git manages the evolution of source code. Pull Requests control how changes enter `main`. CI verifies those changes. Docker converts approved source code into a reproducible artifact. The container registry stores and distributes versioned artifacts that can later be delivered consistently to staging and production.

In this repository:

- **Git:** conventional commits on `feature/*` branches.
- **Pull Requests:** protected `main` with PR-only merges (#1, #2).
- **CI:** the tests plus the Docker build and smoke test must be green.
- **Docker:** the tag builds one immutable image, labelled with its commit.
- **Registry:** GHCR holds `1.0.0`, `1.1.0`, `latest` and SHA tags. Rollback is `docker run …:1.0.0`.

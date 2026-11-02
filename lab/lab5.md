# Lab 5 — CI/CD with GitHub Actions

Implementation uses the supplied requirements: `lab5-ci-cd.md` was not present.

## Current verified state — final review fixes (2026-11-02)

- Original implementation `b070cb69f185072b751cd1d668c74b8dbdb701d1` was committed
  and pushed. Its [GitHub Actions run](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41484869788)
  passed `test` (24 tests) and `smoke`; publication was correctly skipped on the
  feature branch. Older “not committed/pushed” and missing-data statements below
  describe earlier attempts, not the current state.
- Final review fixes now use a Docker context allowlist, bounded smoke requests,
  MLflow health-based Compose readiness, and evaluation revision checks.
- Local Ruff, frozen sync and **34 tests** pass. Both actual and synthetic Docker
  context exports exclude credential files. Image build passes. Final smoke and
  Compose evidence is recorded in the final-fix verification section below.
- Original DVC data stays unchanged: 3,292 images with **43 cross-split duplicate
  pairs**, all retained in the complete failure evidence below. The separate
  `/tmp/food11-lab5-clean-05n8bP/dataset` derivative has 3,249 images, all 11 classes
  in all three splits, and preserves every one of the 1,096 evaluation images.
- **Question 6 is complete** with two exact-commit CI attempts and measured
  step/cache evidence; no cache-driven speedup is claimed. **Question 10 still
  requires real model-comparison evidence. Question 9 is complete**: PR #1
  demonstrated a blocked merge with a failing check, then successful checks after
  restoring the assertion; the PR remains unmerged.
  Main protection is already configured; GHCR publication still needs its first
  approved main push. No manual image publication or real promotion was run.


## Lab questions

1. **Why avoid real MLflow in unit tests?** Loading the champion couples tests to
   server availability, registry state, network access, model artifacts, and heavy
   initialization. Tests could change behavior when an alias moves. Tests use
   `SKIP_MODEL=1` and patch the loader to fail if called.
2. **What does the fake model prove?** It verifies image upload, preprocessing shape,
   prediction invocation, logits interpretation, category mapping, and confidence
   serialization. It does not establish accuracy, artifact compatibility, registry
   connectivity, or real model inference. The generated test image is explicitly
   synthetic. The real Food-11 fixture is now present and its test runs without a skip.
3. **Why are duplicates dangerous?** Content shared between training and evaluation
   lets a classifier memorize examples and inflates accuracy. MD5 detects identical
   file contents across splits, but cannot detect re-encoded or near-duplicate images.
4. **Where should validation run?** Run it on a trusted workstation or private runner
   after `dvc pull`, before training and promotion. Public CI unit and smoke tests
   need neither data credentials nor an MLflow server. Validation is read-only.
   The distribution check compares per-class proportions in training and validation,
   using absolute differences and inclusive tolerance `tau`.
5. **What does `needs: test` do?** It makes smoke wait for successful tests. Publishing
   waits for smoke. Failed upstream checks prevent dependent jobs from running.
6. **First versus second execution time?** **Completed with measured execution.**
   Compared attempts 1 and 2 of CI run `41495964607` at the exact same commit
   `9dd2acf`, with unchanged workflow, uv.lock and 34 tests. `test` took **35 s in
   both** attempts; `smoke` took **127 s → 128 s**. `setup-uv` (including restore)
   stayed **2 s → 2 s** and `uv sync --frozen` changed **6 s → 5 s**. Both attempts
   restored the same 315,451-byte pruned dependency cache and still downloaded
   wheels, including PyTorch, and prepared/installed 173 packages. Thus the cache
   restoration works, but this warm-cache pair does **not** establish cache-driven
   acceleration. The test job did not get faster and the workflow span increased
   from 164 s to 168 s. Caching can reuse eligible files; it does not guarantee a
   faster run or restore the complete virtual environment. The full measured
   per-step table, immutable attempt/job links, limitations and log evidence are
   recorded in the Question 6 experiment below.
7. **Why SHA tags?** The full Git SHA identifies the exact source revision of an image.
   `latest` moves and is ambiguous for rollback. Select the code by SHA (or image
   digest for immutable image identity). Select the model independently by registry
   version or alias; a SHA-tagged image using `champion` can load a different model
   after the alias moves.
8. **Token permissions?** All jobs receive `contents: read`. Only the main-push
   publication job receives `packages: write`. GHCR login uses the short-lived
   `GITHUB_TOKEN`, never a committed personal token. Pull requests cannot publish.
9. **Branch protection and failing PRs?** **Completed with real execution.**
   Existing main rules require a pull request and successful `test` and `smoke`
   checks. [Temporary PR #1](https://github.com/ayaelkhalil1015/mlops-lab-1/pull/1)
   was opened from `test/lab5-failing-ci` into `main`, based on the latest feature
   commit. Changing only `assert len(CLASSES) == 11` to `== 12` produced one failed
   test and 33 passes. The PR's `test` check failed, `smoke` was skipped, and GitHub
   reported `mergeStateStatus: BLOCKED` while `mergeable: MERGEABLE` and draft was
   false. Thus the block was not a draft/conflict artifact. Restoring 11 on the
   same branch produced 34 passing tests and successful Docker/smoke checks.
   GitHub then reported `mergeStateStatus: CLEAN`. No merge or bypass was attempted.
   Main and its rules were unchanged. Full commit/run evidence is recorded below.
10. **Actual promotion decisions?** **Further experimental evidence required.** TODO: requires real execution. No real aliases
    were changed. Existing training records `test_accuracy`; new runs also record
    `test_size`. The gate uses incumbent accuracy p and computes
    `se = sqrt(p * (1-p) / n)`, promoting if candidate accuracy is at least
    `p + 2*se`, otherwise assigning `challenger`. This is the lab's approximate
    gate, not a full paired significance test. Compare runs evaluated on the same
    held-out data revision. New runs record `evaluation_revision` (content and
    label/path SHA-256). The gate rejects differing revisions; missing provenance
    allows a clearly marked numerical dry-run only and blocks `--apply`.
    Supply verified `--n` for historical runs lacking size;
    missing metrics or run IDs fail rather than inventing values. The script checks
    for a changed champion before writes, but registry alias updates are not atomic
    compare-and-swap: simultaneous promotion operations **require coordination**,
    such as one shared external lock/queue across all operators and runners.
    A single-process recheck is not a distributed lock.
    Use a table of candidate/champion version, run ID, data revision, accuracies, n,
    se, threshold, and decision when collecting actual evidence.
11. **Automate promotion with local MLflow?** Use a trusted private runner on the
    MLflow network or a local scheduled process after validation and evaluation.
    GitHub-hosted localhost refers to the runner, not your workstation. Keep
    credentials private, serialize promotions, review the dry-run result, and invoke
    `--apply` only after approval. The current CI deliberately does not train,
    register, promote, or deploy models. To collect evidence, use existing registered
    versions with comparable evaluation records, or manually train and register
    a baseline and candidate on the same DVC revision; no retraining was executed.
12. **Complete pipeline and responsibilities:**

```mermaid
flowchart TD
    A[Manual Git commit and push or PR] --> B[Automatic uv sync and cached dependencies]
    B --> C[Automatic Ruff and pytest: test]
    C --> D[Automatic Docker build: smoke]
    D --> E[Automatic API health check with SKIP_MODEL=1]
    E --> F{Push to main?}
    F -->|Yes| G[Automatic GHCR publication with full code SHA]
    F -->|No| H[Checks available for manual PR review]
    G --> I[Optional manual deployment selecting code SHA or digest]
    J[Manual DVC pull and data validation] --> K[Manual training and evaluation]
    K --> L[Manual registration of model version]
    L --> M[Quality gate dry run with verified evaluation size]
    M --> N[Approved apply selects champion or challenger model alias]
    N --> I
    I --> O[Real startup loads models:/food11@champion]
```

## Local commands and remaining evidence

```bash
uv sync --frozen
uv run ruff check src tests
uv run pytest -q
uv run dvc pull
find data/food11_processed_mini/training/Bread -type f -name '*.jpg' -print -quit
# Copy the actual path printed above:
# cp 'data/food11_processed_mini/training/Bread/<actual-file>.jpg' tests/fixtures/bread.jpg
uv run pytest -q
uv run python src/food11/validate_data.py data/food11_processed_mini
docker build -t food11-api:ci .
docker run -d --name food11-lab5-smoke -p 8000:8000 -e SKIP_MODEL=1 food11-api:ci
curl --fail http://localhost:8000/health
docker logs food11-lab5-smoke
docker rm -f food11-lab5-smoke
# Set VERSION to an existing candidate and N to its verified shared evaluation size.
# Dry run only; requires the local MLflow server:
# uv run python src/food11/promote.py --version "$VERSION" --n "$N"
```

Publication, branch protection, PR evidence, cache timing measurements, and real
promotion results require manual execution. Real Food-11 validation was executed;
its duplicate failures and a separately validated clean derivative are recorded below.
No commits, pushes, GitHub setting changes, or real alias writes were performed.

References: [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[MLflow client API](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.client.html).

## Historical record — initial implementation before commit b070cb6

The following attempts are historical and are superseded by the current status
and final-fix verification sections. Failure evidence is retained intentionally.

Read-only inspection of the local SQLite registry found `food11` version 1 as
champion, produced by run `433ecb2fd112425ba68a0ef2c9968bec`, with recorded
`test_accuracy=0.6706204379562044`. Only one registered version exists. No
`test_size` parameter was found in existing runs, and the mini dataset is absent.
Therefore n, standard error, threshold, and an actual candidate decision remain
`TODO: requires real execution`. Another existing run,
`1bd8a656153344b9b4b08da8c7156491`, records accuracy `0.6715328467153284`;
it is not a registered candidate, and comparable evaluation data must be verified
before registration or comparison. No new training is necessary if those
artifacts and evaluation provenance can be recovered; otherwise manually create
a baseline and candidate with recorded evaluation size and shared data revision.

### Initial local implementation attempts (historical)

- `uv add --dev pytest ruff httpx`: completed; lockfile updated.
- `uv sync --frozen`: PASS (using `UV_CACHE_DIR=/tmp/food11-uv-cache`
  because the default cache is read-only in this execution sandbox).
- `uv run ruff check src tests`: PASS.
- `uv run pytest -q`: 21 passed, 1 skipped. The skipped test needs the real
  Food-11 fixture. Tests required sandbox network permission for TestClient;
  no MLflow server or actual model was used. Dependency deprecation warnings remain.
- Temporary generated-dataset duplicate injection, detection, removal, and
  revalidation: PASS; no DVC-managed data was modified.
- `uv run python src/food11/validate_data.py data/food11_processed_mini`:
  FAIL, exit 1, because the dataset is absent.
- Workflow YAML parsing and assertions on triggers, dependencies and permissions:
  PASS. GitHub execution remains unverified.
- `git diff --check`: PASS; final status and tracked diff reviewed. New files
  were reviewed separately because plain `git diff` excludes untracked files.
- First `docker build -t food11-api:ci .`: FAIL due to PyPI download timeout
  for `packaging==26.3`; container PyPI connectivity probes subsequently returned 200.
- Fallback Docker runtime check: PASS. Started existing `food11-api:latest` with
  current `src` mounted read-only, `SKIP_MODEL=1`, and port `18005`; `/health`
  returned HTTP 200 with `{"status":"ok"}`. The temporary container was removed.
  This verifies changed source in the existing runtime, not a newly built image.

- Second `docker build -t food11-api:ci .`: FAIL due to a PyPI download
  timeout for `graphene==3.4.3` after retries. A freshly built image and its
  smoke test remain unverified. Resolve Docker Desktop build-network connectivity
  to `files.pythonhosted.org` and retry; standalone container HTTP probes worked.

### Original proposed GitHub sequence (historical)

After restoring and validating data and adding the real fixture, review changes,
then run these commands yourself (none was run by the implementation assistant):

```bash
git diff --check
git add Dockerfile README.md pyproject.toml uv.lock src/food11/deduplicate_data.py src/food11/data.py src/food11/serve.py src/food11/train.py src/food11/validate_data.py src/food11/promote.py tests lab/lab5.md .github/workflows/ci.yml
git commit -m "Implement Lab 5 CI/CD and model quality gate"
git push -u origin feature/lab5-ci-cd
gh pr create --base main --head feature/lab5-ci-cd --title "Implement Lab 5 CI/CD" --body "Add isolated tests, data validation, Docker CI/GHCR publishing, and an approval-controlled model quality gate."
```

Review the Actions results and configure the required checks manually as described
in answer 9. Once this implementation is merged, demonstrate branch protection
with a separate branch:

```bash
git switch main
git pull --ff-only
git switch -c demo/lab5-failing-ci
printf 'def test_branch_protection_demo():\n    assert False\n' > tests/test_branch_protection_demo.py
git add tests/test_branch_protection_demo.py
git commit -m "Demonstrate failing required CI check"
git push -u origin demo/lab5-failing-ci
gh pr create --base main --head demo/lab5-failing-ci --title "Demonstrate Lab 5 branch protection" --body "Intentional failure for branch protection evidence; fix before merging."
# Capture failed checks and blocked merge in GitHub before continuing.
printf 'def test_branch_protection_demo():\n    assert True\n' > tests/test_branch_protection_demo.py
git add tests/test_branch_protection_demo.py
git commit -m "Fix branch protection demonstration test"
git push
# Capture successful test and smoke checks; close the demo PR if not needed.
```

Record real CI durations, GHCR SHA tag, and PR evidence in this file. Real MLflow
promotion remains a separate, explicitly approved operation after verified data
and model-version selection. Do not pass `--apply` until that approval exists.

### Earlier follow-up execution (historical, 2026-11-02)

- Confirmed branch `feature/lab5-ci-cd`.
- `UV_CACHE_DIR=/tmp/food11-uv-cache uv run dvc pull`: FAIL, exit 1.
  DagsHub's S3 endpoint returned HTTP 401 Unauthorized while retrieving the DVC
  directory manifest. Local credentials are present but were rejected. Refresh
  credentials privately in `.dvc/config.local` using a valid DagsHub token; do not
  commit or paste credentials into the lab report.
- No real Bread fixture could be copied because restoration failed.
- Ruff: PASS. Pytest: 21 passed, 1 skipped, 4 dependency/lifecycle deprecation
  warnings. The skipped case still requires the real Food-11 fixture.
- Real-data validation: FAIL, exit 1, because the three splits are unavailable.
- Standalone uv and minimal BuildKit probes successfully installed
  `packaging==26.3`. The full default-download build stalled and was interrupted
  (exit 130) to test a build-only adjustment: `UV_CONCURRENT_DOWNLOADS=4` and
  `UV_HTTP_TIMEOUT=120` in the existing Dockerfile. Its stages and runtime behavior
  are preserved. See [uv environment settings](https://docs.astral.sh/uv/configuration/environment/).

- Tuned `docker build -t food11-api:ci .`: PASS, exit 0. The dependency stage
  completed in 913.3 seconds, including `torch==2.14.0+cpu` and
  `torchvision==0.29.0+cpu`. No dependency version change was needed.
- Fresh-image smoke test: PASS, exit 0. Ran:

  ```bash
  docker run -d --name food11-lab5-fresh-check -p 127.0.0.1:18005:8000 -e SKIP_MODEL=1 food11-api:ci
  curl --silent --output /tmp/food11-lab5-health.json --write-out '%{http_code}' http://127.0.0.1:18005/health
  docker logs food11-lab5-fresh-check
  docker rm -f food11-lab5-fresh-check
  ```

  Retried up to 20 times with a two-second delay. Attempt 6 returned HTTP 200
  and `{"status":"ok"}`. Startup logs confirmed successful application startup;
  the temporary container was removed. No source mount or pre-existing image was
  used for this final smoke test.
- `git diff --check`: PASS. `Dockerfile.single` SHA-256 remained
  `eba857ec83f115981f19cef53bade1fc02374a22aa3e309232de469d8af48df6`.
- At the end of that attempt, valid DagsHub credentials were still needed to restore
  data, create the real fixture, and pass real-data validation. Fresh Docker build
  and smoke verification are now complete. No commits, pushes, GitHub settings
  changes, or real MLflow alias changes were performed.

## Restored real-data verification (2026-11-02)

This section supersedes the earlier missing-data and fixture limitations. The user
completed DVC pull (reported 32,033 files fetched, 36,578 added). The mini dataset
was verified locally on `feature/lab5-ci-cd`.

- Copied real `training/Bread/0_0.jpg` to `tests/fixtures/bread.jpg`, 5,087 bytes,
  RGB 128×128. SHA-256:
  `43a8d524fa9befcb74a761d82c59fb38e5052ac3915a6d650da81a1aa83d46d7`.
  Confirmed the fixture matches its source byte-for-byte.
- `UV_CACHE_DIR=/tmp/food11-uv-cache uv run ruff check src tests`: PASS.
- `UV_CACHE_DIR=/tmp/food11-uv-cache uv run pytest -q`: **24 passed, no skips**,
  4 deprecation warnings. This includes two new tests covering safe clean-copy
  behavior, evaluation preservation, source immutability, and overwrite guards.
- The mini dataset contains 3,292 images: training 1,100, evaluation 1,096,
  validation 1,096. Every class has 100 images except Rice in evaluation and
  validation, which has 96. All exceed the default minimum of 50.
- `uv run python src/food11/validate_data.py data/food11_processed_mini`:
  **FAIL, exit 1**. All structural, image readability, RGB, size, minimum-count,
  and class-proportion checks pass; only cross-split duplication fails.
- Found 43 cross-split duplicate groups, each containing two files (86 files).
  Compared bytes in addition to MD5: every pair is truly identical. All 43 pairs
  also have byte-identical counterparts in `data/food11_raw`, confirming leakage
  already exists in the source data. This is not a validator false positive or a
  resizing collision. There are 3 training/evaluation, 2 training/validation,
  and 38 evaluation/validation duplicate groups.
- Improved validator reporting to print each criterion separately, after all
  splits have been scanned. It now marks leakage in **both** affected splits;
  the earlier premature training PASS did not imply training had no duplicates.

### Complete original-dataset PASS/FAIL output

```text
PASS: training: 11 class directories
PASS: training: minimum images per class
PASS: training: readable images
PASS: training: RGB images
PASS: training: 128x128 images
FAIL: training: no cross-split duplicates
PASS: evaluation: 11 class directories
PASS: evaluation: minimum images per class
PASS: evaluation: readable images
PASS: evaluation: RGB images
PASS: evaluation: 128x128 images
FAIL: evaluation: no cross-split duplicates
PASS: validation: 11 class directories
PASS: validation: minimum images per class
PASS: validation: readable images
PASS: validation: RGB images
PASS: validation: 128x128 images
FAIL: validation: no cross-split duplicates
PASS: training/validation class proportions (tau=0.05)
FAIL: duplicate across splits: data/food11_processed_mini/evaluation/Bread/0_131.jpg and data/food11_processed_mini/training/Bread/0_106.jpg
FAIL: duplicate across splits: data/food11_processed_mini/evaluation/Bread/0_139.jpg and data/food11_processed_mini/training/Bread/0_186.jpg
FAIL: duplicate across splits: data/food11_processed_mini/evaluation/Fried food/4_123.jpg and data/food11_processed_mini/training/Fried food/4_167.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Bread/0_11.jpg and data/food11_processed_mini/evaluation/Bread/0_13.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Bread/0_129.jpg and data/food11_processed_mini/evaluation/Bread/0_138.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Bread/0_150.jpg and data/food11_processed_mini/evaluation/Bread/0_17.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Bread/0_152.jpg and data/food11_processed_mini/evaluation/Bread/0_149.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Bread/0_167.jpg and data/food11_processed_mini/evaluation/Bread/0_105.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Bread/0_174.jpg and data/food11_processed_mini/evaluation/Bread/0_1.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dairy product/1_123.jpg and data/food11_processed_mini/training/Dairy product/1_185.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_12.jpg and data/food11_processed_mini/evaluation/Dessert/2_14.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_120.jpg and data/food11_processed_mini/evaluation/Dessert/2_112.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_129.jpg and data/food11_processed_mini/evaluation/Dessert/2_117.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_132.jpg and data/food11_processed_mini/evaluation/Dessert/2_129.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_133.jpg and data/food11_processed_mini/evaluation/Dessert/2_134.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_141.jpg and data/food11_processed_mini/evaluation/Dessert/2_139.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_150.jpg and data/food11_processed_mini/evaluation/Dessert/2_158.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_154.jpg and data/food11_processed_mini/training/Dessert/2_1046.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_155.jpg and data/food11_processed_mini/evaluation/Dessert/2_160.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_164.jpg and data/food11_processed_mini/evaluation/Dessert/2_166.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_176.jpg and data/food11_processed_mini/evaluation/Dessert/2_174.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Dessert/2_18.jpg and data/food11_processed_mini/evaluation/Dessert/2_16.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Fried food/4_103.jpg and data/food11_processed_mini/evaluation/Fried food/4_147.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Fried food/4_13.jpg and data/food11_processed_mini/evaluation/Fried food/4_159.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Meat/5_107.jpg and data/food11_processed_mini/evaluation/Meat/5_166.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Meat/5_123.jpg and data/food11_processed_mini/evaluation/Meat/5_13.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Meat/5_174.jpg and data/food11_processed_mini/evaluation/Meat/5_119.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_102.jpg and data/food11_processed_mini/evaluation/Seafood/8_100.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_110.jpg and data/food11_processed_mini/evaluation/Seafood/8_108.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_125.jpg and data/food11_processed_mini/evaluation/Seafood/8_123.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_130.jpg and data/food11_processed_mini/evaluation/Seafood/8_134.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_133.jpg and data/food11_processed_mini/evaluation/Seafood/8_137.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_134.jpg and data/food11_processed_mini/evaluation/Seafood/8_138.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_139.jpg and data/food11_processed_mini/evaluation/Seafood/8_139.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_141.jpg and data/food11_processed_mini/evaluation/Seafood/8_140.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_167.jpg and data/food11_processed_mini/evaluation/Seafood/8_164.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_183.jpg and data/food11_processed_mini/evaluation/Seafood/8_177.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Seafood/8_187.jpg and data/food11_processed_mini/evaluation/Seafood/8_186.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Soup/9_151.jpg and data/food11_processed_mini/evaluation/Soup/9_148.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Soup/9_152.jpg and data/food11_processed_mini/evaluation/Soup/9_150.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Soup/9_166.jpg and data/food11_processed_mini/evaluation/Soup/9_162.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Soup/9_172.jpg and data/food11_processed_mini/evaluation/Soup/9_170.jpg
FAIL: duplicate across splits: data/food11_processed_mini/validation/Vegetable-Fruit/10_138.jpg and data/food11_processed_mini/evaluation/Vegetable-Fruit/10_106.jpg
FAIL: dataset validation
```

### Safe remediation tested without changing the DVC dataset

Added `src/food11/deduplicate_data.py`. It creates a new destination and refuses
to overwrite an existing directory or use nested source/destination paths. It
keeps the evaluation copy first, validation second, and training last, excluding
only byte-confirmed duplicates from later splits. It does not move images between
splits, relabel images, pad class counts, relax thresholds, or modify source files.

Executed:

```bash
uv run python src/food11/deduplicate_data.py data/food11_processed_mini /tmp/food11-lab5-clean-05n8bP/dataset
uv run python src/food11/validate_data.py /tmp/food11-lab5-clean-05n8bP/dataset
```

The command excluded 43 files **from the copy only**, retaining 3,249 files:
training 1,095, evaluation 1,096, validation 1,058. Evaluation is byte-for-byte
preserved. The smallest class contains 89 images, above the required 50.

Complete standalone clean-copy validation output (exit 0):

```text
PASS: training: 11 class directories
PASS: training: minimum images per class
PASS: training: readable images
PASS: training: RGB images
PASS: training: 128x128 images
PASS: training: no cross-split duplicates
PASS: evaluation: 11 class directories
PASS: evaluation: minimum images per class
PASS: evaluation: readable images
PASS: evaluation: RGB images
PASS: evaluation: 128x128 images
PASS: evaluation: no cross-split duplicates
PASS: validation: 11 class directories
PASS: validation: minimum images per class
PASS: validation: readable images
PASS: validation: RGB images
PASS: validation: 128x128 images
PASS: validation: no cross-split duplicates
PASS: training/validation class proportions (tau=0.05)
PASS: dataset validation (including class proportions)
```

Compared before/after SHA-256 manifests for all 3,292 original mini files: every
path and content hash is unchanged. `Dockerfile.single` also retained its original
SHA-256. No original DVC-managed file was changed.

The clean copy is a temporary local artifact under `/tmp`, not a new DVC revision,
not a replacement for `data/food11_processed_mini`, and not used by existing
training or serving. To reproduce, pass any new, separate destination to the
clean-copy command. Review the cleanup policy and version a derivative explicitly
before using it for training. Existing trained models may already have seen leaked
images, so fixing the copy alone does not repair their evaluation results.

**Remaining:** the original DVC revision correctly fails the leakage gate.
Publishing/adopting a reviewed clean data revision and retraining/evaluating on it
have not been performed. GitHub checks/publication, branch protection and PR
demonstration, CI timing measurements, and real model-promotion evidence remain
manual work. The restored evaluation count is 1,096, but it is not automatically
assumed to be the evaluation size of any historical MLflow run without provenance.
No commits, pushes, GitHub setting changes, or MLflow alias changes were made.

Final preservation checks: `uv run dvc status` returned **“Data and pipelines are
up to date.”** (exit 0). The sandbox-only attempt initially could not open DVC's
state database; rerunning with local state access succeeded. All 1,096 original
evaluation images were separately compared against the derivative by path and
bytes and matched. Final Ruff and `git diff --check` both passed.

Files added or updated in this restored-data step: `tests/fixtures/bread.jpg`,
`tests/fixtures/README.md`, `src/food11/validate_data.py`,
`src/food11/deduplicate_data.py`, `tests/test_deduplicate_data.py`, and this report.
At that stage the Docker image had not been rebuilt after the validator/cleanup
changes. The final verification below records the subsequent rebuild and smoke test.

## Clean-copy audit and original commit preparation (historical, 2026-11-02)

The cleaned dataset remains separate at `/tmp/food11-lab5-clean-05n8bP/dataset`.
It has exactly `training`, `evaluation`, and `validation` at its root, with exactly
the same 11 Food-11 class directories in each split. The complete original-dataset
failure log above preserves all 43 duplicate pairs. Rechecked every pair against
both processed and raw bytes; all remain genuine source-data duplicates.

Cleanup keeps evaluation first, then validation, then training, dropping the
later occurrence from the derivative only. No images are moved between splits,
no labels or image bytes are changed, no samples are fabricated, and validation
thresholds stay at `--min-per-class 50 --tau 0.05`. Every retained image has the
same relative path and SHA-256 as its source; the removed paths represent exactly
one occurrence from each of the 43 duplicate pairs. This policy protects the
held-out split for future training, but does not make past trained models free
of leakage. The cleaned copy has not been adopted, DVC-tracked, pushed, or used
for training or promotion.

Reviewed class counts:

| Class | Training | Evaluation | Validation |
|---|---:|---:|---:|
| Bread | 98 | 100 | 94 |
| Dairy product | 99 | 100 | 100 |
| Dessert | 99 | 100 | 89 |
| Egg | 100 | 100 | 100 |
| Fried food | 99 | 100 | 98 |
| Meat | 100 | 100 | 97 |
| Noodles-Pasta | 100 | 100 | 100 |
| Rice | 100 | 96 | 96 |
| Seafood | 100 | 100 | 89 |
| Soup | 100 | 100 | 96 |
| Vegetable-Fruit | 100 | 100 | 99 |
| **Total** | **1,095** | **1,096** | **1,058** |

All 1,096 evaluation images are preserved byte-for-byte, with identical paths.
All 3,292 original mini-dataset files match the pre-cleaning SHA-256 manifest;
`uv run dvc status` reports “Data and pipelines are up to date.” The `/tmp` copy
is temporary and reproducible using the cleanup command above; no dataset is
included in the proposed Git commit except the 5,087-byte real Bread test fixture.

Manifest fingerprints (SHA-256 of sorted JSON mapping relative paths to file
SHA-256 digests, using Python `json.dumps(manifest, sort_keys=True)`):

- Original: `dba71f538e0a8c5caa8e4c0e18ea2174c7697116a49c0c9f3169d907f4193418`.
- Clean copy: `4893d5a88aa8e66bf9702e64ece4b8210205fac4282692c80afde6427703786e`.

Final commands executed (uv uses `/tmp/food11-uv-cache` in this sandbox):

- `uv sync --frozen`: PASS.
- `uv run ruff check src tests`: PASS.
- `uv run pytest -q`: **24 passed, no skips**, 4 deprecation warnings.
- `uv run python src/food11/validate_data.py /tmp/food11-lab5-clean-05n8bP/dataset`:
  PASS for all criteria and all splits, exit 0.
- Workflow YAML and embedded Bash syntax checks: PASS; triggers, dependencies,
  main-only publication condition and token permissions checked locally.
- `uv run dvc status`: PASS; original data unchanged.
- `docker build -t food11-api:ci .`: PASS, exit 0; rebuilt after the validator
  and cleanup additions, reusing the frozen dependency layer.
- Fresh rebuilt-image smoke test: PASS, exit 0. Started with
  `docker run -d --name food11-lab5-final-smoke -p 127.0.0.1:18005:8000 -e SKIP_MODEL=1 food11-api:ci`.
  The 20-attempt/two-second retry loop returned HTTP 200 on attempt 7, body
  `{"status":"ok"}`. Startup completed successfully; logs were inspected and
  the temporary container was removed. No source mount or model server was used.
- `git diff --check` and final staged-diff checks: PASS.
- `Dockerfile.single` remains untouched, SHA-256
  `eba857ec83f115981f19cef53bade1fc02374a22aa3e309232de469d8af48df6`.

The original DVC revision still correctly fails leakage validation. A separate
approval is needed to adopt/version a clean dataset. GitHub CI execution, GHCR
publication, branch protection and the failing/passing PR demonstration, CI timing
measurements, and real MLflow promotion evidence remain incomplete. No real
MLflow aliases or GitHub settings were changed.

Proposed commit title: `Implement Lab 5 CI/CD and model quality gate`.
After reviewing the staged diff and obtaining commit/push approval, run manually:

```bash
git switch feature/lab5-ci-cd
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m "Implement Lab 5 CI/CD and model quality gate"
git push -u origin feature/lab5-ci-cd
```

These commit and push commands are proposals only; neither was executed.

The proposed commit stages 19 Lab 5 files: `.github/workflows/ci.yml`, `Dockerfile`,
`README.md`, `pyproject.toml`, `uv.lock`, `lab/lab5.md`, `src/food11/data.py`,
`src/food11/serve.py`, `src/food11/train.py`, `src/food11/validate_data.py`,
`src/food11/deduplicate_data.py`, `src/food11/promote.py`, `tests/test_data.py`,
`tests/test_api.py`, `tests/test_validate_data.py`, `tests/test_deduplicate_data.py`,
`tests/test_promote.py`, `tests/fixtures/README.md`, and `tests/fixtures/bread.jpg`.
`Dockerfile.single` remains untracked and excluded. No original or cleaned DVC
images, data pointers, credentials, or MLflow artifacts are staged. Preparing the
index does not create a commit; HEAD remains unchanged.

## Final-fix methodology and verification (2026-11-02)

### Docker context security

`.dockerignore` excludes everything by default, then admits only `Dockerfile`,
`.dockerignore`, `pyproject.toml`, `uv.lock`, `README.md`, and `src/`. Additional
exclusions cover credential/secret filenames, `.dvc`, `.aws`, `.ssh`, environment
files, private keys and caches even when nested under `src`. No credential value
is copied into this report. `.dvc/config.local` is neither modified nor exposed.

Verified the context with a disposable `FROM scratch; COPY . /context/` build and
local-only BuildKit export. The actual exported context includes all required
serving inputs and excludes DVC/AWS configuration, local environment files, data,
MLflow artifacts/registry, tests, and `Dockerfile.single`. A separate synthetic
fixture verifies nested secret/environment/credential/key filenames are excluded
by Docker itself. This checks actual context filtering, not only file patterns.

### Provenance and promotion coordination

`food11.provenance.evaluation_revision()` hashes a canonical manifest of relative
evaluation paths (including class labels) and each file's SHA-256. The result is
independent of the checkout location and modification times. New training runs
record the actual evaluation revision alongside `test_size` before training
starts. Keep that evaluation split fixed throughout training/evaluation. No
historical run has been backfilled and no training was executed for these fixes.

The gate still computes `se = sqrt(p * (1-p) / n)` from champion accuracy and
selects champion only when candidate accuracy is at least `p + 2*se`:

- Matching recorded evaluation revisions: comparison permitted; `--apply` also
  records `quality_gate.evaluation_revision` and `quality_gate.provenance_status`.
- Different recorded revisions: fail before any alias/tag write, even in dry-run.
- Either revision missing: dry-run reports **UNVERIFIED** provenance; `--apply`
  fails without writing tags or aliases. Explicit `--n` does not bypass this.

Equal evaluation revisions do not certify the absence of training/evaluation
leakage: run data validation before training. The unchanged original data still
fails that gate. Historical evidence must be recovered and verified, or new
comparable runs created after separately approved clean-data adoption.

**Simultaneous promotion operations require coordination across every operator
and runner**, for example a shared lock or single promotion queue. The existing
champion recheck reduces stale decisions but is not atomic compare-and-swap;
it does not eliminate a race between the recheck and alias write. Dry-run is
still the default. No real promotion command or alias write was executed.

### Compose readiness and smoke behavior

MLflow has a stdlib-Python `/health` check (5-second interval/timeout, 12 retries,
15-second start period). Inference depends on `mlflow: service_healthy` rather
than mere startup order. Image build definitions, service names, ports, volume semantics,
tracking URI and frontend API behavior remain unchanged. The health command needs
neither curl nor an additional package. Health readiness does not create a model
registry or champion: the existing Lab 4 prerequisite of a valid champion remains.

The GitHub smoke loop retains 20 attempts and a 2-second delay and now calls
`curl --connect-timeout 3 --max-time 5`. The main-only publication condition,
minimal token permissions, full-SHA tag and build cache configuration are unchanged.

References: [Docker build-context filtering](https://docs.docker.com/build/concepts/context/),
[Compose health-based startup](https://docs.docker.com/compose/how-tos/startup-order/).

### Local verification results before committing the fixes

- `uv sync --frozen`: PASS.
- `uv run ruff check src tests`: PASS.
- `uv run pytest -q`: **34 passed, no skips**, 4 existing deprecation warnings.
- Real and synthetic Docker context export checks: PASS.
- `docker build -t food11-api:ci .`: PASS with the hardened build context.
- `docker compose config --quiet`: PASS.

The commands use `UV_CACHE_DIR=/tmp/food11-uv-cache` in this execution sandbox.
No credential or dataset file will be staged. The new CI run will be checked
following the approved commit/push and reported separately; it is not presumed
successful before it runs.

Final integration/preservation results:

- Fresh `SKIP_MODEL=1` container: `/health` returned HTTP 200 with
  `{"status":"ok"}` on attempt 6 using the bounded health loop; container removed.
- Started the entire disposable Compose stack in one `up -d --no-build` operation,
  using a copied SQLite registry and copied model artifacts. Compose explicitly
  waited for MLflow **Healthy** before starting inference. No manual startup
  ordering or restart was needed. Normal inference (without `SKIP_MODEL`) loaded
  the copied champion and predicted `Bread` with confidence `0.8107056894018525`.
  Frontend-to-inference HTTP over service DNS returned 200.
- The disposable MLflow container started at `17:53:56 UTC`; inference started at
  `17:54:19 UTC`, after the health check succeeded. All test containers/network
  were removed; the real Compose volume was not used.
- Before/after hashes confirm `.dvc/config.local`, the real MLflow database,
  original model artifacts, every original mini image, and `Dockerfile.single`
  are unchanged. `uv run dvc status`: “Data and pipelines are up to date.”
- The original and cleaned evaluation splits produce identical evaluation
  fingerprints. No historical MLflow parameter was added or changed.
- Workflow YAML/Bash checks confirm the exact curl timeouts, unchanged retry
  count/delay, main-only publication guard, and healthy Compose dependency.
- `git diff --check`: PASS. Only the nine reviewed configuration, source, test,
  and documentation files are included in this fix commit; no credential file,
  dataset, registry, artifact, or `Dockerfile.single` is staged.

Question 10 remains pending; Questions 6 and 9 are completed below. Matching provenance is not a
replacement for data-quality validation, and this change does not authorize
clean-data adoption or a real model promotion.

## Question 9 — completed branch-protection experiment (2026-11-02)

PR: [#1 — Lab 5 Q9: branch protection experiment (do not merge)](https://github.com/ayaelkhalil1015/mlops-lab-1/pull/1).
It remains **open and unmerged**. This was a normal PR, not a draft. No merge API
or administrative bypass was invoked. The observations below were obtained from
GitHub Actions logs and the PR's GitHub CLI/API check and merge-state fields.

### Controlled test change

- Baseline: latest `feature/lab5-ci-cd`,
  `9dd2acfc6eeaccd094209020ca2fd33286384787`, verified against origin before branching.
- Temporary branch: `test/lab5-failing-ci`; PR target: `main`.
- Failing commit: `017b044efa8366a4fc157cc3f2181cd3926f0b46`,
  message `Demonstrate Lab 5 required-check failure`.
- Its only changed file is `tests/test_data.py`: change the class-count assertion
  from `assert len(CLASSES) == 11` to the intentionally incorrect `== 12`.
  Local targeted pytest confirmed `1 failed, 3 passed` before pushing.
- Restoring commit: `8a5a0f4e9e78cc7f0a08014d69982ed9314d4df5`,
  message `Restore passing assertion after Lab 5 protection experiment`.
  Its only change restores the original assertion; local targeted pytest returned
  `4 passed`. The final tracked tree of the temporary branch exactly matches the
  baseline feature branch: no broken test or net production-code change remains.

Because the temporary branch starts from the Lab 5 feature branch, its PR into
main carries the underlying feature changes as well. The **two experiment commits**
change only that test assertion. This temporary PR must not be merged.

### Observed failing and passing checks

| Phase | Event | Workflow run | test | smoke | publication job |
|---|---|---|---|---|---|
| Intentional failure | push | [41498838786](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41498838786) | FAIL | SKIPPED | SKIPPED |
| Intentional failure | pull_request | [41498917515](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41498917515) | FAIL | SKIPPED | SKIPPED |
| Assertion restored | push | [41499293408](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41499293408) | PASS | PASS | SKIPPED |
| Assertion restored | pull_request | [41499302131](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41499302131) | PASS | PASS | SKIPPED |

Failure log from the PR's test job:

```text
FAILED tests/test_data.py::test_classes - AssertionError: assert 11 == 12
1 failed, 33 passed, 4 warnings in 10.84s
```

Frozen sync and Ruff passed; only pytest failed. `smoke` was skipped because it
has `needs: test`. The recorded failing PR state was:

```json
{
  "headRefOid": "017b044efa8366a4fc157cc3f2181cd3926f0b46",
  "isDraft": false,
  "mergeable": "MERGEABLE",
  "mergeStateStatus": "BLOCKED",
  "state": "OPEN",
  "mergedAt": null
}
```

After restoring the assertion, the PR's test job recorded:

```text
34 passed, 4 warnings in 11.09s
```

The passing PR test job took 32 seconds; smoke took 2 minutes 3 seconds. Docker
build completed, and the container health check returned `{"status":"ok"}` with
`GET /health HTTP/1.1` **200 OK**. The post-fix PR state was:

```json
{
  "headRefOid": "8a5a0f4e9e78cc7f0a08014d69982ed9314d4df5",
  "isDraft": false,
  "mergeable": "MERGEABLE",
  "mergeStateStatus": "CLEAN",
  "state": "OPEN",
  "mergedAt": null
}
```

The failed required check blocked the normal merge path; restoring the assertion
and passing both required checks cleared that block. `MERGEABLE` describes the
absence of textual merge conflicts, while `BLOCKED`/`CLEAN` captured the change
in PR merge eligibility. No actual merge was attempted in either state.

### Preservation and experiment outcome

- Main SHA remained `b3f1ac5cccc6c7d6422724e15f7f31055acb145e`.
- Read-only before/after rule snapshots match: pull requests and successful
  `test`/`smoke` checks remain required; no ruleset was changed.
- No DVC data or MLflow alias was changed. `Dockerfile.single` stayed untouched.
- Publication was skipped for both event types: neither push was to main.
- Returned to `feature/lab5-ci-cd` to record this evidence. The demonstration PR
  remains open/unmerged and must not be used to merge the feature implementation.

**Question 9: complete.** Question 6 measurements follow below. Question 10
still requires its separate experimental evidence. The existing 43 duplicate-pair records remain preserved.

## Question 6 — measured comparable CI execution times (2026-11-02)

### Experiment and controls

- Measurement A: [run 41495964607, attempt 1](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41495964607/attempts/1).
- Measurement B: [same run, attempt 2](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41495964607/attempts/2),
  explicitly triggered with `gh run rerun 41495964607` for this experiment.
- Both use **exactly** commit `9dd2acfc6eeaccd094209020ca2fd33286384787`, the
  same push event/feature branch, same workflow, uv.lock, dependency declarations,
  and 34 tests. No empty commit or source change was necessary. The uncommitted
  Q9 report was local and could not change either remote run's inputs.
- Both complete successfully; publication is skipped because this is not main.
- Both test-job logs report Ubuntu 26.04 image `20261025.179.1` and identical
  resolved `checkout`/`setup-uv` action SHAs; the hosted machines themselves differ.
- This is a **warm-cache versus warm-cache** comparison. Attempt 1 already had a
  cache hit; it is not a deliberately cold baseline. No caches were deleted or
  modified to manufacture an improvement. Different hosted VMs/network conditions
  and one pair of measurements limit causal conclusions.

Timings below are computed from GitHub's job/step `started_at` and `completed_at`
API fields, saved separately for each attempt before rerunning. Units are seconds;
the timestamps have one-second resolution. A zero means both timestamps were in
the same second, not literally zero work. Job totals include overhead not captured
by the listed individual steps; do not infer totals by summing step rows.

| Job / measured step | Attempt 1 (s) | Attempt 2 (s) | Change B − A (s) |
|---|---:|---:|---:|
| test: total job | 35 | 35 | +0 |
| test: Set up job | 1 | 2 | +1 |
| test: Run actions/checkout@v4 | 1 | 1 | +0 |
| test: Run astral-sh/setup-uv@v6 | 2 | 2 | +0 |
| test: Run uv sync --frozen | 6 | 5 | -1 |
| test: Run uv run ruff check src tests | 0 | 1 | +1 |
| test: Run uv run pytest -q | 13 | 10 | -3 |
| test: Post Run astral-sh/setup-uv@v6 | 1 | 0 | -1 |
| test: Post Run actions/checkout@v4 | 0 | 0 | +0 |
| test: Complete job | 0 | 1 | +1 |
| smoke: total job | 127 | 128 | +1 |
| smoke: Set up job | 0 | 1 | +1 |
| smoke: Run actions/checkout@v4 | 1 | 1 | +0 |
| smoke: Run docker build -t food11-api:ci . | 112 | 112 | +0 |
| smoke: Start API and check health | 10 | 10 | +0 |
| smoke: Container logs and cleanup | 0 | 0 | +0 |
| smoke: Post Run actions/checkout@v4 | 0 | 0 | +0 |
| smoke: Complete job | 0 | 0 | +0 |
| Workflow span: first test job start → smoke completion | 164 | 168 | +4 |

The workflow span is defined as first test-job start through smoke-job completion.
It includes scheduling gaps between those jobs, but excludes initial queue delay
and the skipped publication job. Attempt 1 spans 164 seconds; attempt 2 spans 168
seconds, so the second measured workflow was **4 seconds slower** on that definition.

Immutable job evidence:

- Attempt 1: [test job 125450861344](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41495964607/job/125450861344),
  [smoke job 125451180510](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41495964607/job/125451180510).
- Attempt 2: [test job 125470976867](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41495964607/job/125470976867),
  [smoke job 125471316636](https://github.com/ayaelkhalil1015/mlops-lab-1/actions/runs/41495964607/job/125471316636).

### uv dependency-cache observations

Both test-job logs contain the same successful dependency-cache restoration:

```text
Cache hit for: setup-uv-1-x86_64-unknown-linux-gnu-unknown-pruned-eac721c105094802dc2de81c1e76c11f4c94a71776c3ae028b9e807aa8c3a42f
Cache Size: ~0 MB (315451 B)
Cache restored successfully
```

This is the dependency cache restored by `setup-uv`, not merely a cached uv binary.
The 315,451-byte pruned cache is not the whole virtual environment or a complete
wheel archive. Both runs explicitly download `torch (187.2MiB)` and other wheels,
then prepare and install 173 packages. The uv log reports:

| Internal uv operation | Attempt 1 | Attempt 2 |
|---|---:|---:|
| Prepare 173 packages | 3.96 s | 2.63 s |
| Install 173 packages | 487 ms | 1.96 s |

**Conclusion:** a cache hit was verified in both runs. The frozen-sync step was
one second faster in attempt 2 at API resolution, but installation itself was
slower, the total test-job time was unchanged, and the workflow span was longer.
These measurements do **not** demonstrate a cache-caused speedup. A separate
controlled cold/miss versus warm/hit experiment and repeated measurements would
be needed to quantify such a benefit; no improvement is invented here.

The smoke job has its own fresh Docker build, not the test job's uv environment.
Its build step took 112 seconds in both attempts. GHA Docker caching is configured
for the separate main-only publication job, which was skipped in this experiment;
its performance is not measured or credited here.

**Question 6: complete as a measured timing/cache comparison.** Question 9 evidence
is preserved in full above. Question 10 (real comparable models/promotion results)
remains incomplete and no real MLflow alias has been changed.

Documentation verification for this update: local Ruff passes; pytest reports
34 passed, no skips, with four existing deprecation warnings. All 12 answers,
balanced code fences, JSON PR-state examples, Q9 run/commit links, and the 43
original duplicate-pair records were checked. `git diff --check` passes.

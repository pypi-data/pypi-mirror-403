# CI/CD — GitLab pipeline

## Objectif

Le pipeline fait :
1) `lint` (ruff + black)
2) `test` (pytest + coverage)
3) `release` (semantic-release : version + tag)
4) `build` (wheel/sdist)
5) `publish` (upload vers GitLab PyPI)

---

## Stages

### 1) lint
- Image : python:3.12
- Installe deps dev : `pip install -e ".[dev]"`
- Commandes :
  - `ruff check .`
  - `black --check .`

### 2) test
- Exécute :
  - `pytest -q --cov=sunpy_regards --cov-report=term-missing --cov-fail-under=80`

### 3) release (uniquement sur main + push)
Règle :
- `CI_COMMIT_BRANCH == "main"` et `CI_PIPELINE_SOURCE == "push"`

Préparation :
- configure git user
- configure remote avec token :
  - `git remote set-url origin https://oauth2:${RELEASE_TOKEN}@...`
- fetch tags + checkout SHA

Détection commits “release-worthy” :
- calcule un range :
  - normal : `${CI_COMMIT_BEFORE_SHA}..${CI_COMMIT_SHA}`
  - cas initial (BEFORE=0...) : fallback sur `LAST_TAG..AFTER` ou juste `AFTER`
- si le range contient :
  - `feat...` ou `fix...` ou `perf...` ou `BREAKING CHANGE`
  → exécute `semantic-release version`
- sinon, exit 0 (pas de release)

Push :
- push branch + tags

> Important : le job release ne déclenche pas `build/publish`. Ces jobs sont déclenchés par le pipeline de tag (CI_COMMIT_TAG).

---

### 4) build (uniquement si tag)
Règle :
- `if: $CI_COMMIT_TAG`

Commandes :
- `python -m build`

Artifacts :
- `dist/`

### 5) publish (uniquement si tag)
- dépend de `build` via `needs: ["build"]`
- utilise `twine` vers GitLab registry :
  - repository-url : `${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/pypi`
- Auth :
  - `TWINE_USERNAME=gitlab-ci-token`
  - `TWINE_PASSWORD=$CI_JOB_TOKEN`

---

## Variables nécessaires

- `RELEASE_TOKEN` :
  - token GitLab avec droits push (pour tags / commit release)
- Variables REGARDS (pour exécution réelle hors tests) :
  - `REGARDS_BASE_URL`, `REGARDS_TENANT`, `REGARDS_USERNAME`, `REGARDS_PASSWORD`

---

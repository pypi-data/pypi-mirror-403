# sunpy-regards — Documentation projet

## Objectif

`sunpy-regards` est un plugin SunPy/Fido qui permet d'interroger l'archive **REGARDS** (tenant MEDOC/Solar) via API REST, en exposant un provider `regards` utilisable dans `sunpy.net.Fido`.

Le projet est structuré selon une architecture inspirée Clean Architecture :
- **Adapters** : intégration SunPy / Fido (attrs + client)
- **Application** : use-cases + ports
- **Domain** : entités + erreurs métier
- **Infrastructure** : HTTP + mapping JSON

---

## Arborescence

### Racine
- `.env` / `.env.example` : configuration locale
- `.gitlab-ci.yml` : CI/CD
- `pyproject.toml` : packaging + semantic-release
- `CHANGELOG.md` : changelog généré
- `requirements.txt` / `requirements-dev.txt` : dépendances (optionnel si pyproject suffit)

### Package `sunpy_regards/`

#### `config.py`
- `RegardsConfig.from_env()` lit :
  - `REGARDS_BASE_URL`
  - `REGARDS_USERNAME`
  - `REGARDS_PASSWORD`
  - `REGARDS_TENANT`
- Lève une erreur si user/pass manquants.

---

## Adapter SunPy (plugin Fido)

Dossier : `sunpy_regards/adapters/sunpy/`

### `_attrs.py`
Définit les attributs SunPy et un `AttrWalker` qui construit la requête REGARDS (`q=`).

Attributs :
- `Dataset(value)` → `properties.dataset_name:"..."`
- `Observatory(value)` → `properties.observatory:"..."`
- `a.Instrument(value)` → `properties.instrument:"..."`
- `a.Time(start, end)` → `properties.date_obs:[START TO END]`

Note : `a.Provider("REGARDS")` est filtré dans `_can_handle_query`, sans être injecté dans le `q=`.

### `attrs.py`
Ré-export des attrs pour que SunPy les détecte proprement dans `a.regards.*`.

### `client.py`
Implémente `REGARDSClient(BaseClient)` :
- `search()` :
  - construit les branches via `walker.create()`
  - appelle le UseCase `SearchProducts`
  - convertit en `QueryResponseTable`
  - applique une **politique d’affichage** : table réduite (display) + table complète attachée (`_regards_full_table`)
- `register_values()` :
  - tente de récupérer des valeurs dynamiques depuis REGARDS (`/rs-dam/datasets`)
  - fallback statique si indisponible
- `fetch()` :
  - si `_regards_full_table` existe, l’utilise (car la vue masque URL/URN/filename)
  - si URL est sur `REGARDS_BASE_URL` → download via `FetchProducts` (auth)
  - si domaine SOAR → `requests.get()` direct
  - sinon → `downloader.enqueue_file(...)` (parfive)

---

## Application (use-cases)

Dossier : `sunpy_regards/application/`

- `dto.py` : `ProductDTO` (données transport)
- `ports.py` : interface `RegardsRepository`
- `use_cases.py` :
  - `SearchProducts.execute(q, page, size)`
  - `RegisterValues.execute()`
  - `FetchProducts.download(url)`

---

## Domain

Dossier : `sunpy_regards/domain/`

- `entities.py` : `Product`
- `value_objects.py` : `TimeRange`
- `exceptions.py` :
  - `RegardsError`
  - `RegardsAuthError`
  - `RegardsApiError`

---

## Infrastructure

Dossier : `sunpy_regards/infrastructure/`

### `http/auth.py`
- `request_token(config)` :
  - POST `/api/v1/rs-authentication/oauth/token`
  - grant_type=password
  - scope = tenant
  - renvoie `access_token`

### `http/regards_client.py` (repository)
`RegardsApi` implémente `RegardsRepository` :
- `register_values()` :
  - GET `/api/v1/rs-dam/datasets`
  - met en cache `_register_cache`
  - fallback vide si erreur
- `search(q, page, size)` :
  - GET `/api/v1/rs-access-project/dataobjects/search`
  - parse JSON via mapper
- `download_bytes(url)` :
  - GET binaire + Authorization Bearer

### `mappers/regards_mapper.py`
- `extract_register_values(js)` : extrait datasets/instruments/observatories
- `json_to_products(js, base_url, tenant)` :
  - gère plusieurs shapes (`content` ou `features`)
  - localise `props`, `urn`, `files`
  - construit download_url :
    - si `uri` présent → direct
    - sinon fallback `/rs-catalog/{tenant}/downloads/{urn}/files/{file_id}`
  - enrichit `extra`
- `extract_wavelength_numbers(...)` : cherche valeurs “wave/wav” dans un JSON (fallback wavemin)

---

## Tests

- `tests/` : unit tests (sans réseau bloqué par fixture `no_network`)
- `tests/infra/` : tests infra mockés (requests monkeypatch)
- `fixtures/regards_search_sample.json` : sample JSON

La fixture `no_network` bloque requests.get/post/request/Session.request pendant les unit tests.

---

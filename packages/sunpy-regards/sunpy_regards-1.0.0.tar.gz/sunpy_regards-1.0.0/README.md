
# sunpy-regards

**SunPy/Fido plugin** for searching and downloading solar data from the  
**REGARDS archive (MEDOC – Solar tenant)**.

Adds a new **`regards` provider** to `sunpy.net.Fido`.

---

## 🚀 Quick start

### Install
```bash
pip install sunpy-regards
````

### Configure

Create a `.env` file (or export environment variables):

```env
REGARDS_BASE_URL=https://regards.osups.universite-paris-saclay.fr
REGARDS_TENANT=Solar
REGARDS_USERNAME=your_username
REGARDS_PASSWORD=your_password
```

---

## 🛰️ Supported datasets (current public list)

Datasets are defined in REGARDS and may evolve over time.
Current public datasets include:

* **SDO / AIA** — `GAIA-DEM data` *(label: GAIA-DEM)*
* **SOHO / CELIAS** — `SOHO data` *(label: SOHO)*
* **Solar Orbiter / PHI** — `Solar Orbiter data` *(label: Solar-Orbiter)*
* **STEREO / SECCHI** — `STEREO data` *(label: STEREO)*
* **TRACE / TRACE** — `TRACE data` *(label: TRACE)*

Tip: you can use these values in `r.Dataset(...)` and `r.Observatory(...)`.

---

## Use with SunPy/Fido

```python
from sunpy.net import Fido
import sunpy.net.attrs as a
from sunpy.net.attrs import regards as r

results = Fido.search(
    a.Time("2023-03-17", "2023-03-19"),
    r.Observatory("SDO"),
    a.Instrument("AIA"),
    r.Dataset("GAIA-DEM data"),
)

Fido.fetch(results, path="./downloads/{file}")
```

---

## ℹ️ Notes

* Python **≥ 3.11**, SunPy **≥ 7**
* REGARDS credentials are required for full functionality
* Dataset discovery is dynamic when credentials are available
* Project status: **Alpha**

---

## 🔗 Links

* REGARDS archive: [https://regards.osups.universite-paris-saclay.fr](https://regards.osups.universite-paris-saclay.fr)
* SunPy: [https://sunpy.org](https://sunpy.org)




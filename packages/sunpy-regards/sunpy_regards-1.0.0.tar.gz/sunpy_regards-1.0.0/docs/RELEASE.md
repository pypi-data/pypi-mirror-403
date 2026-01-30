# Release & Versioning (semantic-release)

## Principe

Le projet utilise `python-semantic-release` avec des commits **Conventional Commits**.
La release est déclenchée sur `main` lorsque le push contient au moins un commit :
- `feat:` → bump **minor**
- `fix:` → bump **patch**
- `feat!:` ou `BREAKING CHANGE` → bump **major**

Le tag est créé au format :
- `v{version}` (ex: `v1.2.0`)

Le changelog est mis à jour dans `CHANGELOG.md`.

---

## Config (pyproject.toml)

- Parser : `commit_parser = "conventional"`
- Tag format : `tag_format = "v{version}"`
- Commit message : `chore(release): v{version}`
- Remote : GitLab (`type = "gitlab"`)

Tags autorisés :
- `allowed_tags = ["feat", "fix"]`
- `minor_tags = ["feat"]`
- `patch_tags = ["fix"]`

---

## Déclenchement en CI

### Job `release` (sur push main)
1) calcule un range de commits (BEFORE..AFTER)
2) détecte si un commit “release-worthy” est présent
3) si oui :
   - `semantic-release version`
   - push du commit release + tags

### Job `build` / `publish` (sur tag)
Le pipeline de tag construit le package et le publie sur GitLab PyPI.

---

## Exemples de commits pour tester

### Patch (vX.Y.(Z+1))
```bash
git commit -am "fix: handle empty tag range in release script"
````

### Minor (vX.(Y+1).0)

```bash
git commit -am "feat: add dataset filter support"
```

### Major (v(X+1).0.0)

```bash
git commit -am "feat!: change query API response format"
# ou ajouter "BREAKING CHANGE:" dans le body
```


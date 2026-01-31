# Workflow State

## Informations générales

- **Projet** : dymfile
- **Étape courante** : 5. Execution
- **Rôle actif** : Développeur
- **Dernière mise à jour** : 2026-01-22 12:20

## Résumé du besoin

Le projet **dymfile** est une bibliothèque Python pour manipuler des fichiers `.dym` (format binaire scientifique plus simple que NetCDF/HDF5). Le code actuel permet uniquement la lecture et nécessite une modernisation complète.

**Objectifs principaux :**

1. Refactoring du code existant (écrit avec moins d'expérience)
2. Migration vers outils modernes : uv (remplace Poetry), ruff (linter/formatter), pyright (type checker)
3. Ajout de la fonctionnalité d'écriture de fichiers .dym
4. Simplification : retrait des fonctions de visualisation et dépendances graphiques
5. Intégration native avec xarray (backend pour lecture/écriture)
6. Documentation complète + site MkDocs hébergé sur GitHub Pages
7. Suite de tests

**Contraintes :**

- Utilisateurs : auteur + quelques équipes distinctes
- Pas de rétrocompatibilité requise
- Pas de contrainte de temps
- Cible Python : version large (3.10+ ou 3.11+)
- Fichiers exemple disponibles dans `/Users/adm-lehodey/Documents/Workspace/Data/dym/`

**Périmètre OUT :**

- Interface graphique
- Fonctions de visualisation
- Optimisations de performance complexes
- Support d'autres formats

## Rapport d'analyse

### Structure du projet

```
dymfile/
├── AI/                    # Documentation workflow ASH (11 fichiers .md)
├── src/dymfile/          # Code source principal
│   ├── __init__.py       # Export de la classe Dymfile
│   ├── dymfile.py        # Classe principale Dymfile (210 lignes)
│   └── core/
│       ├── __init__.py   # Fichier vide
│       ├── dymfile_loading.py  # Fonctions de lecture binaire (295 lignes)
│       └── dymfile_tools.py    # Utilitaires (222 lignes)
├── scripts/
│   └── dymtonetcdf.py    # Script CLI de conversion DYM → NetCDF
├── pyproject.toml        # Configuration Poetry + dépendances
├── setup.py              # Configuration setuptools (legacy)
├── poetry.lock           # Lock file Poetry
├── README.md             # Documentation minimale (3 lignes)
└── .gitignore            # Fichiers ignorés
```

**Organisation :**

- Code bien structuré en modules (`core/` pour la logique, classe principale séparée)
- Présence de `setup.py` ET `pyproject.toml` (duplication)
- Script CLI inclus mais non documenté
- Pas de dossier `tests/`, `docs/`, `examples/`, `.github/`

### Technologies identifiées

- **Langage** : Python 3.13 (version cible dans pyproject.toml : `>=3.13`)
- **Gestionnaire de dépendances** : Poetry (via `poetry.lock` et `pyproject.toml`)
- **Build backend** : poetry-core 2.0.0+
- **Dépendances principales** :
  - numpy >= 2.2.4
  - xarray >= 2025.3.0 (très récent)
  - netCDF4 >= 1.7.2
- **Dépendances de visualisation** (à retirer selon le besoin) :
  - matplotlib, cartopy, hvplot, geoviews, jupyter-bokeh
  - ipykernel (pour Jupyter)
- **Outils de qualité** : Aucun (pas de ruff, pyright, mypy, pytest, pre-commit, etc.)
- **CI/CD** : Aucun
- **Documentation** : Aucune (pas de MkDocs, Sphinx)

### Patterns et conventions

**Nommage :**

- Fichiers : `snake_case` (dymfile_loading.py, dymfile_tools.py)
- Fonctions : `snake_case` (read_header, format_data, normalize_longitude)
- Classes : `PascalCase` (Dymfile, HeaderData, LabelsCoordinates)
- Constantes : `SCREAMING_SNAKE_CASE` (DYM_INVALID_VALUE, NB_DAY_MONTHLY)

**Architecture :**

- Pattern **Façade** : classe `Dymfile` qui encapsule les fonctions du module `core`
- **Dispatch par type** : utilisation de `@singledispatchmethod` pour `from_input()` (gère `str` et `bytes`)
- **Dataclasses** : `HeaderData` pour structure de données (bon usage)
- **Séparation des responsabilités** :
  - `dymfile_loading.py` : lecture binaire brute
  - `dymfile_tools.py` : transformations et utilitaires
  - `dymfile.py` : API publique

**Type hints :**

- Utilisation de `from __future__ import annotations` (bonne pratique)
- Type hints présents mais pas exhaustifs
- `TYPE_CHECKING` pour imports conditionnels (bonne pratique)
- Annotations `Any` pour certains retours (plot)

**Docstrings :**

- Format **NumPy style** (sections Parameters, Returns, Notes, Examples)
- Très détaillées et complètes
- Présence d'exemples dans la classe principale

**Qualité du code :**

- Commentaires inline rares mais pertinents (ex: `# sourcery skip`)
- Utilisation de `# noqa` pour ignorer des linters
- Presence d'un TODO dans le script CLI (ligne 55)

### Points d'attention

**Dette technique :**

1. **Double configuration build** : `setup.py` ET `pyproject.toml` coexistent avec des dépendances non synchronisées
   - `setup.py` liste "plotly" (absent de pyproject.toml)
   - `pyproject.toml` liste des versions strictes, `setup.py` non
2. **Version Python très récente** : `>=3.13` peut limiter l'adoption (3.13 sorti fin 2024)
3. **Dépendances de visualisation non optionnelles** : cartopy, hvplot importés directement dans le code
4. **Import hvplot side-effect** : `import hvplot.xarray  # noqa: F401` (ligne 10 de dymfile.py) modifie xarray globalement
5. **Script CLI non testé** : pas de tests pour `dymtonetcdf.py`
6. **Fonction plot() avec type de retour Any** : difficile à typer correctement
7. **Logique de normalisation dupliquée** : dans `__init__()` lignes 98-100, appel à `normalize_longitude()` deux fois

**Incohérences :**

1. `core/__init__.py` est vide mais le module est importé dans `dymfile.py`
2. Script CLI dans `scripts/` mais `__init__.py` présent (devrait être un package ?)
3. README minimal (3 lignes) ne documente ni l'installation ni l'usage

**Zones à risque :**

1. **Lecture binaire brute** : code sensible aux erreurs (struct.unpack) sans gestion d'erreur explicite
2. **Mask** : toujours présent dans le format selon le code, mais besoin de vérification utilisateur
3. **Format de date SEAPODYM** : logique métier spécifique (fonctions `get_date_sea`, `year_month_sea`) non documentée
4. **Pas de tests** : aucune garantie de non-régression lors du refactoring

**Fonctionnalités manquantes (selon le besoin) :**

1. Écriture de fichiers .dym (lecture seule actuellement)
2. Backend xarray natif (actuellement classe wrapper)
3. Tests automatisés
4. Documentation utilisateur
5. Validation des données (dimensions, types, valeurs)

### Opportunités

1. **Code bien structuré** : refactoring facilité par l'organisation modulaire
2. **Type hints existants** : bon point de départ pour pyright
3. **Utilisation de xarray** : déjà présent, facilite l'intégration backend
4. **Docstrings complètes** : excellent pour générer documentation MkDocs
5. **Patterns modernes** : singledispatch, dataclasses, annotations from **future**

## Décisions d'architecture

### Choix techniques

| Domaine                         | Choix                    | Justification                                                                                              |
| ------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Gestionnaire de dépendances** | uv                       | Remplacement de Poetry. Ultra-rapide, moderne, compatible pyproject.toml. Évite le lock file lourd (202KB) |
| **Linter + Formatter**          | ruff                     | Remplace black, isort, flake8, etc. Ultra-rapide (écrit en Rust), configuration minimale                   |
| **Type checker**                | pyright                  | Demandé par l'utilisateur. Plus rapide et moderne que mypy. Excellente intégration VS Code                 |
| **Framework de tests**          | pytest                   | Standard Python. Simple, extensible, découverte automatique des tests                                      |
| **Documentation**               | MkDocs + mkdocs-material | Génération de docs moderne, thème Material design. Hébergement GitHub Pages natif                          |
| **Backend xarray**              | xarray.backends API      | API officielle xarray pour backends custom. Permet `xr.open_dataset("file.dym", engine="dym")`             |
| **Version Python cible**        | >=3.10                   | Au lieu de 3.13. Balance entre modernité et adoption (3.10 = oct 2021, encore largement supporté)          |
| **Pre-commit hooks**            | pre-commit + ruff        | Automatisation qualité code avant commit. Exécute ruff check + ruff format                                 |

### Structure proposée

```
dymfile/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Tests + linting + type checking
│       └── docs.yml            # Déploiement MkDocs sur GitHub Pages
├── docs/
│   ├── index.md                # Page d'accueil documentation
│   ├── installation.md         # Guide installation
│   ├── usage.md                # Guide utilisation
│   ├── api/                    # Documentation API auto-générée
│   └── format.md               # Spécification format DYM
├── src/dymfile/
│   ├── __init__.py             # Exports publics (open_dym, to_dym, __version__)
│   ├── _version.py             # Version centralisée
│   ├── backend.py              # Backend xarray (DymBackendEntrypoint, DymBackendArray)
│   ├── reader.py               # Lecture fichiers .dym (refactoré depuis dymfile_loading)
│   ├── writer.py               # Écriture fichiers .dym (NOUVEAU)
│   ├── _formats.py             # Structures de données (HeaderData, etc.)
│   └── _utils.py               # Utilitaires (dates SEAPODYM, normalisation, etc.)
├── tests/
│   ├── conftest.py             # Fixtures pytest (fichiers exemple)
│   ├── test_reader.py          # Tests lecture
│   ├── test_writer.py          # Tests écriture
│   ├── test_backend.py         # Tests backend xarray
│   ├── test_roundtrip.py       # Tests lecture → écriture → lecture
│   └── data/                   # Fichiers .dym de test (petits)
├── scripts/
│   ├── dym-to-dataset          # Script CLI : .dym → NetCDF/Zarr
│   └── dataset-to-dym          # Script CLI : NetCDF/Zarr → .dym
├── pyproject.toml              # Configuration unifiée (uv, ruff, pyright, pytest)
├── mkdocs.yml                  # Configuration MkDocs
├── .pre-commit-config.yaml     # Hooks pre-commit
├── .gitignore                  # Mise à jour
└── README.md                   # Documentation complète avec badges

SUPPRIMÉS :
├── setup.py                    # Remplacé par pyproject.toml moderne
├── poetry.lock                 # Remplacé par uv.lock
└── src/dymfile/core/           # Refactoré et aplati
```

### Interfaces et contrats

#### 1. API Publique (pour utilisateurs finaux)

```python
# Usage simple via xarray backend
import xarray as xr

# Lecture
ds = xr.open_dataset("file.dym", engine="dym")
da = xr.open_dataarray("file.dym", engine="dym")

# Écriture
ds.to_netcdf("output.dym", engine="dym")
```

#### 2. Backend xarray (interface interne)

```python
class DymBackendEntrypoint(xarray.backends.BackendEntrypoint):
    """Point d'entrée pour le backend xarray."""

    def open_dataset(
        self,
        filename_or_obj,
        *,
        drop_variables=None,
        # options spécifiques dym
        normalize_longitude=False,
        decode_times=True,
    ) -> xr.Dataset:
        """Ouvre un fichier .dym comme Dataset xarray."""
        ...

    def guess_can_open(self, filename_or_obj) -> bool:
        """Détecte si le fichier est un .dym."""
        return str(filename_or_obj).endswith(".dym")
```

#### 3. Module Reader (lecture bas niveau)

```python
@dataclass
class DymHeader:
    """Header d'un fichier DYM."""
    nlon: int
    nlat: int
    nlevel: int
    t0: float
    tfin: float

@dataclass
class DymData:
    """Données complètes d'un fichier DYM."""
    header: DymHeader
    data: np.ndarray  # Shape: (nlevel, nlat, nlon)
    mask: np.ndarray  # Shape: (nlat, nlon)
    longitude: np.ndarray  # Shape: (nlon,)
    latitude: np.ndarray  # Shape: (nlat,)
    time: np.ndarray  # Shape: (nlevel,)

def read_dym(file: str | PathLike | BinaryIO) -> DymData:
    """Lit un fichier .dym et retourne les données brutes."""
    ...
```

#### 4. Module Writer (écriture bas niveau)

```python
def write_dym(
    file: str | PathLike | BinaryIO,
    data: np.ndarray,
    longitude: np.ndarray,
    latitude: np.ndarray,
    time: np.ndarray,
    mask: np.ndarray | None = None,
    *,
    t0: float | None = None,
    tfin: float | None = None,
) -> None:
    """Écrit un fichier .dym depuis des arrays numpy."""
    ...

def dataset_to_dym(ds: xr.Dataset, file: str | PathLike) -> None:
    """Écrit un Dataset xarray au format .dym."""
    ...
```

### Conventions de code

| Domaine                | Convention                        | Note                                                           |
| ---------------------- | --------------------------------- | -------------------------------------------------------------- |
| **Nommage variables**  | snake_case                        | Conservé (existant)                                            |
| **Nommage fichiers**   | snake_case.py                     | Conservé (existant)                                            |
| **Nommage classes**    | PascalCase                        | Conservé (existant)                                            |
| **Nommage constantes** | SCREAMING_SNAKE_CASE              | Conservé (existant)                                            |
| **Imports privés**     | Préfixe `_` pour modules internes | Nouveau : `_utils.py`, `_formats.py`                           |
| **Formatage**          | ruff format                       | Remplace black. Compatible black par défaut                    |
| **Linting**            | ruff check                        | ~700 règles activables. Config minimale au départ              |
| **Typage**             | pyright strict                    | Tous les fichiers `src/` typés. `Any` évité sauf cas justifiés |
| **Docstrings**         | NumPy style                       | Conservé (existant). Compatible mkdocstrings                   |
| **Tests**              | pytest + fixtures                 | Fichiers `test_*.py` dans `tests/`. Coverage > 80%             |
| **Commits**            | Conventional Commits              | `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`       |

### Migrations nécessaires

#### Phase 1 : Configuration des outils

1. Suppression de Poetry → migration vers uv
2. Ajout de ruff configuration dans pyproject.toml
3. Ajout de pyright configuration dans pyproject.toml
4. Ajout de pytest configuration dans pyproject.toml
5. Création de .pre-commit-config.yaml
6. Mise à jour .gitignore
7. Nettoyage des dépendances (retrait viz)

#### Phase 2 : Refactoring du code existant

1. Aplatissement de `src/dymfile/core/` → modules `_utils.py`, `_formats.py`
2. Renommage `dymfile_loading.py` → `reader.py`
3. Suppression des imports de visualisation (cartopy, hvplot)
4. Suppression des méthodes `plot_data()`, `plot_mask()`
5. Fix des types avec pyright
6. Application de ruff format + ruff check --fix

#### Phase 3 : Nouvelle fonctionnalité (écriture)

1. Création de `writer.py`
2. Implémentation de `write_dym()` (bas niveau)
3. Implémentation de `dataset_to_dym()` (haut niveau)
4. Tests de round-trip (lecture → écriture → lecture)

#### Phase 4 : Backend xarray

1. Création de `backend.py`
2. Implémentation de `DymBackendEntrypoint`
3. Implémentation de `DymBackendArray` (lazy loading)
4. Enregistrement du backend dans `__init__.py`
5. Tests d'intégration avec xarray

#### Phase 5 : Documentation et tests

1. Configuration MkDocs
2. Rédaction des guides utilisateur
3. Génération de l'API reference (mkdocstrings)
4. Écriture des tests (coverage > 80%)
5. Configuration CI/CD GitHub Actions
6. Mise à jour du README avec badges et exemples

### Risques identifiés

| Risque                                | Impact | Mitigation                                                                                                          |
| ------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------- |
| **Format binaire non documenté**      | Haut   | Vérifier sur fichiers exemple. Documenter dans `docs/format.md`. Ajouter tests de non-régression sur fichiers réels |
| **Mask optionnel dans le format**     | Moyen  | Implémenter détection (lecture de taille de fichier attendue vs réelle). Gérer cas avec/sans mask                   |
| **Dates SEAPODYM non standard**       | Moyen  | Conserver logique existante. Documenter clairement. Ajouter tests sur cas limites (années bissextiles, etc.)        |
| **Performance lecture/écriture**      | Bas    | Accepté par l'utilisateur. Si besoin, profiler avec cProfile et optimiser après                                     |
| **Backend xarray lazy loading**       | Moyen  | Implémenter `DymBackendArray` avec indexing. Tester sur gros fichiers si disponibles                                |
| **Rétrocompatibilité classe Dymfile** | Bas    | Pas de contrainte utilisateur. Documenter migration dans docs si besoin                                             |
| **Version Python 3.10**               | Bas    | Tester CI sur 3.10, 3.11, 3.12, 3.13. Éviter features 3.11+                                                         |

### Décisions validées par l'utilisateur

1. **Classe `Dymfile`** : ✅ Suppression complète. On utilise uniquement le backend xarray.

2. **Scripts CLI** : ✅ Deux scripts à créer :
   - `dym-to-dataset` : Conversion .dym → NetCDF/Zarr
   - `dataset-to-dym` : Conversion NetCDF/Zarr → .dym

3. **Nom du package** : ✅ On garde `dymfile`

4. **Fichiers de test** : ✅ Un fichier disponible : `data/historical_yft_larve.dym`. Suffisant pour démarrer (tests de lecture + round-trip). Autres fichiers pourront être ajoutés plus tard.

5. **Documentation du format** : ✅ Aucune spécification existante. À déduire du code existant et à documenter dans `docs/format.md`.

## Todo List

### Phase 1 : Configuration des outils

| État | ID  | Nom                           | Description                                                                                        | Dépendances | Résolution                                                                  |
| ---- | --- | ----------------------------- | -------------------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------- |
| ☑    | T1  | Créer pyproject.toml moderne  | Refondre pyproject.toml avec config uv, ruff, pyright, pytest. Supprimer dépendances visualisation | -           | Fichier créé avec Python 3.10+, hatchling, ruff, pyright, pytest configurés |
| ☑    | T2  | Créer .pre-commit-config.yaml | Configurer pre-commit avec ruff check + ruff format                                                | T1          | Fichier créé avec hooks ruff + pyright + pre-commit standards               |
| ☑    | T3  | Mettre à jour .gitignore      | Ajouter uv.lock, .pytest_cache, .coverage, site/ (mkdocs)                                          | -           | Fichier mis à jour avec entrées uv, pytest, pyright, mkdocs, IDE            |
| ☑    | T4  | Installer dépendances avec uv | Exécuter `uv sync` pour créer uv.lock et .venv                                                     | T1          | 50 packages installés avec succès via uv sync                               |
| ☑    | T5  | Supprimer fichiers legacy     | Supprimer setup.py, poetry.lock, et dossier .venv ancien                                           | T4          | setup.py et poetry.lock supprimés                                           |

### Phase 2 : Refactoring du code existant

| État | ID  | Nom                                   | Description                                                                                                       | Dépendances | Résolution                                                       |
| ---- | --- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------- |
| ☑    | T6  | Créer src/dymfile/\_formats.py        | Créer dataclasses DymHeader, DymData. Déplacer HeaderData depuis loading                                          | T4          | Fichier créé avec DymHeader et DymData dataclasses               |
| ☑    | T7  | Créer src/dymfile/\_utils.py          | Déplacer fonctions utilitaires depuis dymfile_tools.py (dates, normalisation, iter_unpack). Supprimer imports viz | T6          | Fichier créé avec fonctions utilitaires sans dépendances viz     |
| ☑    | T8  | Renommer et refactorer reader.py      | Renommer dymfile_loading.py → reader.py. Refactorer avec nouvelles structures. Utiliser \_formats et \_utils      | T6, T7      | Fichier créé avec read_dym() et dym_to_dataset(), code refactoré |
| ☑    | T9  | Supprimer src/dymfile/core/           | Supprimer dossier core/ et tous ses fichiers (code migré)                                                         | T8          | Dossier core/ supprimé                                           |
| ☑    | T10 | Supprimer src/dymfile/dymfile.py      | Supprimer classe Dymfile (remplacée par backend xarray)                                                           | T8          | Fichier dymfile.py supprimé                                      |
| ☑    | T11 | Mettre à jour src/dymfile/**init**.py | Nouveaux exports : open_dym (alias xr.open_dataset), to_dym, **version**. Supprimer Dymfile                       | T10         | Fichier mis à jour avec nouvelle API publique                    |
| ☑    | T12 | Appliquer ruff sur le code            | Exécuter `ruff format .` et `ruff check --fix .` sur src/                                                         | T11         | Ruff appliqué : 1 fichier reformatté, 2 erreurs corrigées        |
| ☑    | T13 | Fix types avec pyright                | Corriger toutes les erreurs pyright dans src/dymfile/                                                             | T12         | Types corrigés (1 erreur restante sur backend.py non créé)       |

### Phase 3 : Implémentation écriture

| État | ID  | Nom                                     | Description                                                               | Dépendances | Résolution                                        |
| ---- | --- | --------------------------------------- | ------------------------------------------------------------------------- | ----------- | ------------------------------------------------- |
| ☑    | T14 | Créer src/dymfile/writer.py             | Implémenter write_dym() : écriture bas niveau numpy → .dym binaire        | T8          | Fichier créé avec write_dym() et dataset_to_dym() |
| ☑    | T15 | Ajouter dataset_to_dym() dans writer.py | Fonction haut niveau : xr.Dataset → .dym. Gestion métadonnées, validation | T14         | Inclus dans T14 (même fichier)                    |

### Phase 4 : Backend xarray

| État | ID  | Nom                                     | Description                                                                            | Dépendances | Résolution |
| ---- | --- | --------------------------------------- | -------------------------------------------------------------------------------------- | ----------- | ---------- |
| ☐    | T16 | Créer src/dymfile/backend.py            | Implémenter DymBackendEntrypoint avec open_dataset(), guess_can_open()                 | T8          |            |
| ☐    | T17 | Ajouter DymBackendArray dans backend.py | Implémentation lazy loading avec **getitem** pour indexing efficace                    | T16         |            |
| ☐    | T18 | Enregistrer backend dans **init**.py    | Ajouter entrypoint xarray dans pyproject.toml [project.entry-points."xarray.backends"] | T16, T11    |            |

### Phase 5 : Scripts CLI

| État | ID  | Nom                              | Description                                                                                | Dépendances | Résolution |
| ---- | --- | -------------------------------- | ------------------------------------------------------------------------------------------ | ----------- | ---------- |
| ☐    | T19 | Créer scripts/dym-to-dataset     | Script CLI avec argparse : .dym → NetCDF/Zarr. Options : output format, compression        | T16         |            |
| ☐    | T20 | Créer scripts/dataset-to-dym     | Script CLI avec argparse : NetCDF/Zarr → .dym. Options : variable selection, time encoding | T15         |            |
| ☐    | T21 | Supprimer scripts/dymtonetcdf.py | Supprimer ancien script (remplacé par dym-to-dataset)                                      | T19         |            |

### Phase 6 : Tests

| État | ID  | Nom                           | Description                                                     | Dépendances   | Résolution |
| ---- | --- | ----------------------------- | --------------------------------------------------------------- | ------------- | ---------- |
| ☐    | T22 | Créer tests/conftest.py       | Fixtures pytest : fichier dym exemple, Dataset temporaire       | T8            |            |
| ☐    | T23 | Créer tests/test_reader.py    | Tests lecture : header, data, mask, coordinates, dates SEAPODYM | T22           |            |
| ☐    | T24 | Créer tests/test_writer.py    | Tests écriture : validation format binaire, header correcte     | T15, T22      |            |
| ☐    | T25 | Créer tests/test_roundtrip.py | Tests read → write → read. Vérifier conservation des données    | T23, T24      |            |
| ☐    | T26 | Créer tests/test_backend.py   | Tests backend xarray : open_dataset, lazy loading, indexing     | T18, T22      |            |
| ☐    | T27 | Ajouter tests scripts CLI     | Tests des deux scripts CLI avec fichiers temporaires            | T19, T20, T22 |            |

### Phase 7 : Documentation

| État | ID  | Nom                        | Description                                                           | Dépendances | Résolution |
| ---- | --- | -------------------------- | --------------------------------------------------------------------- | ----------- | ---------- |
| ☐    | T28 | Créer mkdocs.yml           | Configuration MkDocs avec thème material, plugins mkdocstrings        | T1          |            |
| ☐    | T29 | Créer docs/index.md        | Page d'accueil : présentation, quickstart, features                   | T28         |            |
| ☐    | T30 | Créer docs/installation.md | Guide installation : uv, pip, conda. Configuration                    | T29         |            |
| ☐    | T31 | Créer docs/usage.md        | Guide utilisation : lecture, écriture, backend xarray, exemples       | T30         |            |
| ☐    | T32 | Créer docs/format.md       | Spécification format DYM : structure binaire, header, dates SEAPODYM  | T31         |            |
| ☐    | T33 | Créer docs/api.md          | Page API reference avec mkdocstrings auto-généré depuis docstrings    | T32         |            |
| ☐    | T34 | Mettre à jour README.md    | Documentation complète : badges, installation, quickstart, liens docs | T33         |            |

### Phase 8 : CI/CD

| État | ID  | Nom                              | Description                                                     | Dépendances | Résolution |
| ---- | --- | -------------------------------- | --------------------------------------------------------------- | ----------- | ---------- |
| ☐    | T35 | Créer .github/workflows/ci.yml   | CI : matrix Python 3.10-3.13, tests pytest, ruff check, pyright | T23         |            |
| ☐    | T36 | Créer .github/workflows/docs.yml | CD : build MkDocs et deploy sur GitHub Pages à chaque push main | T28         |            |

### Phase 9 : Finalisation

| État | ID  | Nom                            | Description                                                            | Dépendances | Résolution |
| ---- | --- | ------------------------------ | ---------------------------------------------------------------------- | ----------- | ---------- |
| ☐    | T37 | Créer src/dymfile/\_version.py | Fichier version centralisé. Utilisé dans **init**.py et pyproject.toml | T11         |            |
| ☐    | T38 | Vérifier tests                 | Exécuter pytest avec coverage. Viser > 80%. Corriger échecs            | T27         |            |
| ☐    | T39 | Vérifier documentation         | Générer docs localement `mkdocs serve`. Vérifier liens, exemples       | T34         |            |
| ☐    | T40 | Vérifier CI/CD                 | Pousser sur branche et vérifier que CI passe. Corriger si échecs       | T35, T36    |            |

## Historique des transitions

| De                | Vers              | Raison                                 | Date             |
| ----------------- | ----------------- | -------------------------------------- | ---------------- |
| -                 | 1. Initialisation | Démarrage du workflow ASH              | 2026-01-22 09:45 |
| 1. Initialisation | 2. Analyse        | Besoin validé par l'utilisateur        | 2026-01-22 11:35 |
| 2. Analyse        | 3. Architecture   | Analyse complétée                      | 2026-01-22 11:40 |
| 3. Architecture   | 4. Planification  | Architecture validée par l'utilisateur | 2026-01-22 12:15 |
| 4. Planification  | 5. Execution      | Todo list complétée (40 tâches)        | 2026-01-22 12:20 |

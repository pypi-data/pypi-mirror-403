# Publishing golpo to PyPI

The package is published under the name **`golpo`** on PyPI (the `golpo-pip` folder is the repo; the installable name is `golpo`).

---

## CI/CD: GitHub Actions (recommended)

A workflow at **`.github/workflows/publish-pypi.yml`** builds and publishes to PyPI automatically.

### Triggers

- **Release published** – when you create a release in GitHub
- **Tag push** – e.g. `git tag v0.9.8 && git push origin v0.9.8`
- **Manual** – Actions → “Publish to PyPI” → “Run workflow”

### One-time setup: PyPI Trusted Publishing (no secrets)

1. On **PyPI**: open [Manage project → Publishing](https://pypi.org/manage/project/golpo/settings/publishing/) for the `golpo` project.
2. Click **Add a new pending publisher**.
3. Set:
   - **Owner:** your GitHub org or username
   - **Repository name:** the repo that contains this workflow (e.g. `golpo-pip` or `golpo-ai`)
   - **Workflow name:** `publish-pypi.yml`
   - **Environment:** leave empty (or create an environment like `pypi` for approval rules)
4. Save. After the next successful run from that workflow, the publisher becomes active.

No `PYPI_API_TOKEN` or other secrets are needed when using trusted publishing.

### Alternative: API token (legacy)

If you prefer an API token:

1. Create a token at [PyPI → API tokens](https://pypi.org/manage/account/token/).
2. In the repo: **Settings → Secrets and variables → Actions** → **New repository secret**  
   Name: `PYPI_API_TOKEN`, Value: `pypi-...`
3. In `.github/workflows/publish-pypi.yml`, in the “Publish to PyPI” step, uncomment and use:
   ```yaml
   username: __token__
   password: ${{ secrets.PYPI_API_TOKEN }}
   ```
   and remove or narrow `permissions.id-token` if you are not using OIDC.

### Monorepo (workflow in repo root)

If `golpo-pip` is a **subfolder** of the repo (e.g. `golpo-ai`):

1. Copy `.github/workflows/publish-pypi.yml` to the **root** of the repo (e.g. `golpo-ai/.github/workflows/publish-pypi.yml`).
2. In that file, set:
   ```yaml
   env:
     PACKAGE_DIR: golpo-pip
   ```
3. In PyPI trusted publisher config, use the **root repo** name (e.g. `golpo-ai`).

### Release flow with CI/CD

1. Bump `version` in `pyproject.toml`.
2. Commit and push.
3. Create and push a tag: `git tag v0.9.8 && git push origin v0.9.8`  
   **or** create a GitHub Release (which also runs the workflow).
4. The workflow builds and publishes to PyPI; install with `pip install golpo --upgrade`.

---

## Manual publish (local)

### Prerequisites

1. **PyPI account**  
   Create one at [pypi.org](https://pypi.org/account/register/).

2. **API token (recommended)**  
   - PyPI → Account settings → API tokens → Add API token  
   - Scope: entire account or a single project (e.g. `golpo`)  
   - Copy the token (e.g. `pypi-...`); you won’t see it again.

3. **Test PyPI (optional)**  
   For dry runs, use [test.pypi.org](https://test.pypi.org/) and create a separate account/token there.

---

## One-time setup

Install build and upload tools:

```bash
pip install build twine
```

Store your PyPI token so `twine` can use it without putting it in the command line:

- **Windows (PowerShell):**
  ```powershell
  # Create/edit .pypirc in your user folder: %USERPROFILE%\.pypirc
  # Or use keyring (pip install keyring) and twine will prompt once
  ```

- **Linux/macOS:**
  ```bash
  # ~/.pypirc
  [pypi]
  username = __token__
  password = pypi-YOUR_API_TOKEN_HERE
  ```

For Test PyPI, add:

```ini
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

---

## Publish steps

### 1. Bump version (if needed)

Edit `pyproject.toml` and set a new version, e.g.:

```toml
version = "0.9.8"
```

PyPI does not allow re-uploading the same version.

### 2. Clean and build

From the **`golpo-pip`** directory (same folder as `pyproject.toml`):

```bash
# Remove old builds
rm -rf dist build *.egg-info
# Or on Windows:
# Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Build wheel and sdist
python -m build
```

This fills the `dist/` folder with something like `golpo-0.9.8-py3-none-any.whl` and `golpo-0.9.8.tar.gz`.

### 3. Check the archives (optional)

```bash
twine check dist/*
```

Fix any reported errors before uploading.

### 4. Upload to PyPI

**Production PyPI:**

```bash
twine upload dist/*
```

**Test PyPI:**

```bash
twine upload --repository testpypi dist/*
```

When prompted, use username `__token__` and password = your API token (or rely on `~/.pypirc` / keyring if configured).

### 5. Install and verify

```bash
pip install golpo --upgrade
python -c "import golpo; print(golpo.__version__)"
```

For Test PyPI:

```bash
pip install golpo --index-url https://test.pypi.org/simple/ --upgrade
```

---

## Checklist before each release

- [ ] Version bumped in `pyproject.toml`
- [ ] `python -m build` runs without errors
- [ ] `twine check dist/*` passes
- [ ] Changelog/README updated (if you maintain them)
- [ ] Tag the release in git, e.g. `git tag v0.9.8 && git push origin v0.9.8`

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| **“File already exists”** | You’re re-uploading the same version; bump the version and rebuild. |
| **“Invalid or non-existent authentication”** | Check `~/.pypirc` or env vars; use `__token__` as username and the token as password. |
| **“Repository not found”** | For Test PyPI you must pass `--repository testpypi` and have `[testpypi]` in `.pypirc`. |
| **Missing files in the package** | Ensure all needed files are under `golpo/` or listed in `pyproject.toml` (e.g. `tool.hatch.build.targets.wheel.sources`). |

Once published, users can install with:

```bash
pip install golpo
```

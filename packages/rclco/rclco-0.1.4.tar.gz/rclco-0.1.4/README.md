# RCLCO Python Library

A Python library for RCLCO.

## Installation

Install from PyPI:

```bash
pip install rclco
```

Or using uv:

```bash
uv pip install rclco
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. uv is an extremely fast Python package manager written in Rust that replaces pip, poetry, pyenv, and virtualenv.

### Installing uv

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Alternative (via pip):**

```bash
pip install uv
```

After installation, restart your terminal or run `refreshenv` to ensure `uv` is available in your PATH.

### Getting Started (Full Workflow)

1. **Clone the repository:**

```bash
git clone https://github.com/RCLCO-RFA/python-rclco.git
cd python-rclco
```

2. **Install all dependencies (including dev dependencies):**

```bash
uv sync --all-extras
```

This command will:
- Create a virtual environment in `.venv` (if it doesn't exist)
- Install all project dependencies
- Install the package in editable mode

3. **Activate the virtual environment (optional):**

uv commands automatically use the virtual environment, but if you want to activate it manually:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

### Common uv Commands

| Task | Command |
|------|---------|
| Install all dependencies | `uv sync` |
| Install with dev dependencies | `uv sync --all-extras` |
| Add a new dependency | `uv add <package>` |
| Add a dev dependency | `uv add --dev <package>` |
| Remove a dependency | `uv remove <package>` |
| Update all dependencies | `uv lock --upgrade` then `uv sync` |
| Run a command in the venv | `uv run <command>` |
| Run Python | `uv run python` |
| Run tests | `uv run pytest` |

### Adding Dependencies

**Add a runtime dependency:**

```bash
uv add requests
```

**Add a dev-only dependency:**

```bash
uv add --dev black ruff mypy
```

**Add a dependency with version constraints:**

```bash
uv add "pandas>=2.0"
```

After adding dependencies, the `pyproject.toml` and `uv.lock` files will be updated automatically. Commit both files to version control.

### Running Tests

```bash
uv run pytest
```

To run with verbose output:

```bash
uv run pytest -v
```

### Building and Publishing

This project uses **tag-based versioning** with [hatch-vcs](https://github.com/ofek/hatch-vcs). The version is automatically derived from git tags — no need to manually edit version strings in code.

#### How Versioning Works

- The version is determined by git tags (e.g., `v0.1.2` → version `0.1.2`)
- During development, the version includes git metadata (e.g., `0.1.2.dev3+g1234567`)
- When you build from a tagged commit, you get a clean version (e.g., `0.1.2`)

#### Creating a Release

1. **Ensure all changes are committed and pushed to main**

2. **Create and push a version tag:**

```bash
git tag v0.2.0
git push origin v0.2.0
```

3. **GitHub Actions automatically:**
   - Runs all tests
   - Builds the package
   - Creates a GitHub Release with auto-generated release notes
   - Publishes to PyPI

#### Manual Build (for testing)

**Build the package locally:**

```bash
uv build
```

This creates distribution files in the `dist/` directory.

**Publish manually (if needed):**

```bash
uv publish --token YOUR_PYPI_TOKEN
```

### Setting Up PyPI Publishing (for maintainers)

To enable automatic publishing to PyPI:

1. **Create a PyPI API Token:**
   - Go to https://pypi.org/manage/account/token/
   - Create a token scoped to the `rclco` project
   - Copy the token (starts with `pypi-`)

2. **Add the token to GitHub Secrets:**
   - Go to your repo → **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `PYPI_TOKEN`
   - Value: paste your PyPI token
   - Click **Add secret**

### Version Tag Format

Use semantic versioning with a `v` prefix:

| Tag | Version | Description |
|-----|---------|-------------|
| `v0.1.0` | 0.1.0 | Initial release |
| `v0.1.1` | 0.1.1 | Patch release (bug fixes) |
| `v0.2.0` | 0.2.0 | Minor release (new features) |
| `v1.0.0` | 1.0.0 | Major release (breaking changes) |

### Development Workflow Summary

```
1. Clone repo          → git clone ... && cd python-rclco
2. Install deps        → uv sync --all-extras
3. Make changes        → edit code
4. Add dependencies    → uv add <package> or uv add --dev <package>
5. Run tests           → uv run pytest
6. Commit changes      → git add . && git commit -m "..."
7. Push to branch      → git push origin feature-branch
8. Open PR             → merge to main after review
9. Create release      → git tag v0.2.0 && git push origin v0.2.0
```

## License

See LICENSE file for details.

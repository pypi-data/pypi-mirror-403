# acuity-cli

Python CLI for managing Acuity Scheduling appointments, clients, and availability.

## Installation

**macOS users:** Modern macOS requires a virtual environment (PEP 668).

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install CLI
pip install -e ".[dev]"
```

**Linux/WSL users:**
```bash
pip install -e ".[dev]"
```

**All installation options:**
- **Option A:** Virtual environment (recommended for macOS) - shown above
- **Option B:** System Install (Linux/WSL) - see [QUICKSTART.md](./QUICKSTART.md#option-b-system-install-linuxwsl)
- **Option C:** pipx (Isolated System Install) - see [QUICKSTART.md](./QUICKSTART.md#option-c-pipx-isolated-system-install)
- **Full guide:** See [INSTALL.md](./INSTALL.md)

## Update

```bash
acuity update
```

For Homebrew-managed Python (PEP 668), use:

```bash
acuity update --pipx
# or
acuity update --venv ~/venvs/acuity
```

## Released Versions (PyPI vs Git Tags)

PyPI may lag behind git tags. If `acuity --version` does not match the latest tag, install from the tag directly:

```bash
pip install -U "dc-acuity-cli @ git+https://github.com/DallasCrilleyMarTech/acuity-scheduling.git@v1.3.0#subdirectory=acuity-cli"
hash -r
acuity --version
```

If your shell still shows an older version, check the active binary and reinstall:

```bash
which acuity
pip uninstall -y dc-acuity-cli
pip install -U "dc-acuity-cli @ git+https://github.com/DallasCrilleyMarTech/acuity-scheduling.git@v1.3.0#subdirectory=acuity-cli"
hash -r
acuity --version
```

## Usage

```bash
# Step 1: Get appointment types (ALWAYS FIRST)
acuity types list

# Step 2: Check availability
acuity availability dates --type 12345 --month 2026-02
acuity availability times --type 12345 --date 2026-02-15

# Step 3: Validate slot
acuity availability check --type 12345 --datetime "2026-02-15T14:00:00"

# Step 4: Book appointment
acuity appointments book --type 12345 --datetime "2026-02-15T14:00:00" \
  --first-name Jane --last-name Doe --email jane@example.com
```

## Configuration

Set credentials via environment variables or config file:

```bash
export ACUITY_USER_ID="your-user-id"
export ACUITY_API_KEY="your-api-key"
```

Or create `~/.config/acuity/config.json`:

```json
{
  "user_id": "your-user-id",
  "api_key": "your-api-key",
  "default_timezone": "America/Chicago",
  "output": "json"
}
```

## Development

```bash
# Type checking
mypy acuity_cli

# Linting & formatting
ruff check acuity_cli
ruff format acuity_cli

# Run tests
pytest
```

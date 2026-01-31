# Acuity CLI - Quick Start

Get up and running in 5 minutes.

## 1. Install

Requires Python 3.10 or higher.

### Prerequisites

Check your Python version:
```bash
python3 --version
```

### Option A: Virtual Environment (Recommended for macOS)

Modern macOS blocks system-level pip installs (PEP 668). Use a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or on Windows: venv\Scripts\activate

# Install CLI
pip install -e ".[dev]"
```

### Option B: System Install (Linux/WSL)

If you're not on macOS or have configured your Python differently:

```bash
pip install -e ".[dev]"
```

### Option C: pipx (Isolated System Install)

For system-wide access without virtual environments:

```bash
# Install pipx if needed
brew install pipx  # macOS
# or: python3 -m pip install --user pipx

# Install acuity-cli
pipx install -e .
```

### Verify Installation

```bash
acuity --version
```

Expected output: `acuity-cli <version>`

### Update

```bash
acuity update
```

If you're on Homebrew Python (PEP 668), use:

```bash
acuity update --pipx
# or
acuity update --venv ~/venvs/acuity
```

## 2. Configure Credentials

Get your credentials from [Acuity Scheduling API settings](https://secure.acuityscheduling.com/app.php?key=api).

### Option A: Environment Variables (Recommended)

```bash
export ACUITY_USER_ID="your-user-id"
export ACUITY_API_KEY="your-api-key"
```

### Option B: Config File

Create `~/.config/acuity/config.json`:

```json
{
  "user_id": "your-user-id",
  "api_key": "your-api-key"
}
```

## 3. First Commands

### List appointment types (REQUIRED FIRST STEP)

You'll need the appointment type ID for booking:

```bash
acuity types list
```

This shows all available appointment types with their IDs.

### Check availability for next month

Replace `12345` with an actual type ID from the previous command:

```bash
acuity availability dates --type 12345 --month 2026-02
```

### See available time slots for a specific date

```bash
acuity availability times --type 12345 --date 2026-02-15
```

### Book an appointment

```bash
acuity appointments book \
  --type 12345 \
  --datetime "2026-02-15T10:00:00" \
  --first-name "John" \
  --last-name "Doe" \
  --email "john@example.com"
```

## Common Workflows

### Check upcoming appointments

```bash
acuity appointments list --min-date 2026-02-01
```

### Cancel an appointment

```bash
acuity appointments cancel 98765
```

### Search for a client

```bash
acuity clients list --search "john"
```

## Output Formats

⚠️ **Important:** Global options like `-o` must come BEFORE the command name.

Change output format with the `-o` flag:

```bash
# JSON (default, best for automation)
acuity -o json types list

# Human-readable table
acuity -o text types list

# Markdown table
acuity -o markdown types list
```

**Common mistake:**
```bash
# ❌ This will fail:
acuity types list -o text

# ✅ Correct:
acuity -o text types list
```

## Recommended Booking Flow

1. **Get appointment type ID**: `acuity types list`
2. **Find available dates**: `acuity availability dates --type ID --month YYYY-MM`
3. **Check time slots**: `acuity availability times --type ID --date YYYY-MM-DD`
4. **Validate slot** (optional): `acuity availability check --type ID --datetime "..."`
5. **Book**: `acuity appointments book --type ID --datetime "..." --first-name ... --last-name ... --email ...`

## Environment Variables Reference

```bash
export ACUITY_USER_ID="..."          # Required: Your Acuity user ID
export ACUITY_API_KEY="..."          # Required: Your Acuity API key
export ACUITY_TIMEZONE="..."         # Optional: Default timezone (default: America/Chicago)
export ACUITY_OUTPUT="json"          # Optional: Default output format (json|text|markdown)
```

## Next Steps

- See [README.md](./README.md) for complete command reference
- Check exit codes in README for automation integration
- Explore calendar filtering with `--calendar` option
- Use `--help` on any command for detailed options:
  ```bash
  acuity appointments book --help
  ```

## Troubleshooting

**Authentication failed (exit code 3)**

- Verify your `ACUITY_USER_ID` and `ACUITY_API_KEY` are correct
- Check credentials at https://secure.acuityscheduling.com/app.php?key=api

**Slot unavailable (exit code 5)**

- The time slot may have been booked by someone else
- Run `acuity availability check` before booking to validate

**Configuration error (exit code 2)**

- Ensure environment variables are exported or config file exists
- Verify JSON syntax if using config file

## License

MIT

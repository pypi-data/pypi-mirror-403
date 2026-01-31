# Installation Guide

This guide covers installing and updating `acuity` on macOS, Linux, and Windows/WSL.

## Option A: Virtual Environment (Recommended on macOS)

Modern macOS uses PEP 668, so a virtual environment is the safest default.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Verify:

```bash
acuity --version
```

## Option B: System Install (Linux/WSL)

```bash
pip install -e ".[dev]"
```

Verify:

```bash
acuity --version
```

## Option C: pipx (Isolated System Install)

```bash
pipx install dc-acuity-cli
pipx upgrade dc-acuity-cli
```

Verify:

```bash
acuity --version
```

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


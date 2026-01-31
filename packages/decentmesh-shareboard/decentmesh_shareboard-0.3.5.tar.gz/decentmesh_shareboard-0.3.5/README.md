# ShareBoard

A decentralized copy-paste sharing application built on DecentMesh.

## Features

- 🔐 End-to-end encrypted text sharing
- 👥 Persistent contact management
- 🌐 Decentralized mesh network communication
- 🎨 Modern dark glassmorphism UI

## Installation

```bash
cd shareboard
pip install -e .
```

## Usage

```bash
# Run the application
python -m shareboard

# Or use the entry point
shareboard
```

## First Run

1. Enter your display name when prompted
2. Your identity key will be generated automatically
3. Click "Copy My Key" to share with contacts
4. Add contacts by copying their key and clicking "Add from Clipboard"

## Storage

All data is stored in `~/.shareboard/`:

- `my_identity.json` - Your identity (name + keys)
- `identities.json` - Your contacts
- `history.json` - Shared text history

## Requirements

- Python 3.9+
- PySide6
- DecentMesh network access

# comike-cli

A Python CLI tool for browsing Comiket WebCatalog with a Claude Code-like interactive interface.

## Overview

Search and browse Comiket circle information from your terminal using the Circle.ms [WebCatalog API](https://docs.circle.ms/webcatalog/ctn/developer/001.html).

## Features

### Circle Search & Browse
- Search by circle name
- Filter by genre and hall
- View circle details
- Display circle cut images (Braille Unicode art)

### Work Search
- Keyword search by work name/description
- Filter by new/existing releases
- View work details

### Favorites Management
- Add/remove/update favorite circles
- Organize with color labels (9 colors)
- Add memos
- View favorites list

### Event Information
- Get event list
- Access past event data

## Requirements

- Python 3.10+
- Circle.ms developer account (required for API access)

### Mobile

Rust is required to build the `jiter` dependency (used by `openai` package).

**Termux (Android)**
```bash
pkg install python rust ndk-sysroot clang make libjpeg-turbo
```

**iSH (iOS)**
```bash
apk add python3 py3-pip rust cargo gcc musl-dev jpeg-dev zlib-dev
```
Note: iSH uses x86 emulation, so compilation may be slow or unstable.

## Installation

```bash
pip install comike-cli
```

Or install from source:

```bash
git clone https://github.com/m96-chan/comike-cli.git
cd comike-cli
pip install -e .
```

## Setup

1. Register as a developer at [Circle.ms](https://docs.circle.ms/webcatalog/ctn/developer/001.html) to obtain Client ID and Client Secret
2. Create `~/.comike_cli/.env` with your credentials

```bash
mkdir -p ~/.comike_cli
cat > ~/.comike_cli/.env << 'EOF'
CIRCLE_MS_CLIENT_ID=your_client_id
CIRCLE_MS_CLIENT_SECRET=your_client_secret
OPENAI_API_KEY=your_openai_api_key
EOF
```

## Usage

```bash
# Start interactive mode
comike

# Example queries (in natural language)
# "Search for circles with 東方"
# "Show my favorites"
# "Add this circle to favorites"

# Commands
# /help  - Show help
# /clear - Clear conversation history
# /quit  - Exit
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT

## Important Notes

- Data obtained via the API must not be redistributed or used for purposes other than app development
- Bulk export functionality for circle information is prohibited
- Web application development is not permitted
- API specification redistribution/publication is prohibited

See the [Developer Guidelines](https://docs.circle.ms/webcatalog/ctn/developer/003.html) for details.

# JS2 - Just Screen Share

Share your screen with friends using a simple command and public URL.

## Quick Start

```bash
# Install
pip install -e .

# Share your screen (one command!)
js2 publish
```

That's it! You'll get a public URL to share with friends.

## Features

- One command to share: `js2 publish`
- Public URL via ngrok tunnel
- View-only (no remote control)
- Works on macOS, Windows, Linux
- Browser-based viewer (friends don't need to install anything)

## Requirements

- Python 3.8+

## Installation

```bash
# Clone this repo
cd js2

# Install js2 and all dependencies
pip install -e .
```

## Usage

### Share with Public URL (Recommended)

```bash
js2 publish
```

This will:
1. Start the screen capture server
2. Create an ngrok tunnel
3. Give you a public URL to share

### Local Only

```bash
js2 start
```

Starts server on `http://localhost:8080` without tunneling.

## Commands

| Command | Description |
|---------|-------------|
| `js2 publish` | Start and get public URL (uses ngrok) |
| `js2 start` | Start locally only |
| `js2 --help` | Show help |

## ngrok Authentication (First Time Only)

If ngrok asks for authentication:

1. Create a free account at https://ngrok.com
2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
3. Run: `ngrok authtoken YOUR_TOKEN`

After this one-time setup, `js2 publish` will work automatically.

## How It Works

```
Your Screen --> [JS2 Server] --> [ngrok tunnel] --> [Public URL] --> Friend's Browser
```

1. JS2 captures your screen
2. Streams it via WebSocket
3. ngrok creates a public tunnel
4. Friends open the URL in any browser

## Troubleshooting

### macOS: "Permission denied" for screen recording

Go to: System Preferences > Security & Privacy > Privacy > Screen Recording
Add your terminal app to the allowed list.

### ngrok authentication error

Run: `ngrok authtoken YOUR_TOKEN`
Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken

## License

MIT

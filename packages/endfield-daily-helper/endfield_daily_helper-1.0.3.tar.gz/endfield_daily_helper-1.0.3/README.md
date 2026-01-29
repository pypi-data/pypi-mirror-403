# Endfield Daily Login Helper

[![Build and Publish](https://github.com/chiraitori/endfield-daily-helper/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/chiraitori/endfield-daily-helper/actions/workflows/build-and-publish.yml)
[![Docker Build](https://github.com/chiraitori/endfield-daily-helper/actions/workflows/docker-build.yml/badge.svg)](https://github.com/chiraitori/endfield-daily-helper/actions/workflows/docker-build.yml)

Automatically claim daily login rewards for **Arknights: Endfield**.

Inspired by [hoyo-daily-logins-helper](https://gitlab.com/atomicptr/hoyo-daily-logins-helper).

## Features

- 🎁 Automatic daily sign-in
- 📋 Multiple account support
- ⏰ Scheduler mode for continuous operation
- 🔔 Discord webhook notifications
- 🐳 Docker support

## Installation

### pipx (Recommended)

[pipx](https://pipx.pypa.io/) installs the tool in an isolated environment:

```bash
pipx install endfield-daily-helper
```

Or install directly from GitHub:

```bash
pipx install git+https://github.com/chiraitori/endfield-daily-helper.git
```

### pip

```bash
pip install endfield-daily-helper
```

### From Source

```bash
git clone https://github.com/chiraitori/endfield-daily-helper.git
cd endfield-daily-helper
pip install -e .
```

### Docker

```bash
docker build -t endfield-daily .
docker run --rm -e ENDFIELD_TOKEN="your_token" endfield-daily
```

## Quick Start

### 1. Get Your ACCOUNT_TOKEN

The website uses **httpOnly cookies** that cannot be copied via `document.cookie`. You need to extract the `ACCOUNT_TOKEN` manually:

1. Open the [Endfield Sign-in Page](https://game.skport.com/endfield/sign-in)
2. Log in with your Hypergryph/SKPORT account
3. Open browser DevTools (F12) → **Application** tab
4. In the left sidebar, expand **Cookies** → click `.skport.com`
5. Find the cookie named `ACCOUNT_TOKEN` and copy its **Value**

### 2. Run Sign-in

```bash
endfield-daily --token "YOUR_ACCOUNT_TOKEN_HERE"
```

That's it! 🎉

## CLI Usage

```
endfield-daily [OPTIONS]

Options:
  --version             Show version and exit
  --token TOKEN         ACCOUNT_TOKEN from browser cookies (required)
  --cookie COOKIE       Cookie string (backup method)
  --config-file FILE    Path to TOML configuration file
  --identifier NAME     Account identifier for logging
  --debug               Enable debug logging
  -h, --help            Show help message
```

### Examples

**Basic usage:**
```bash
endfield-daily --token "YOUR_TOKEN"
```

**With custom identifier:**
```bash
endfield-daily --token "YOUR_TOKEN" --identifier "Main Account"
```

**Debug mode:**
```bash
endfield-daily --token "YOUR_TOKEN" --debug
```

**Using environment variable:**
```bash
export ENDFIELD_TOKEN="YOUR_TOKEN"
endfield-daily
```

## Configuration File

For multiple accounts or advanced features, create a config file `endfield-daily-helper.toml`:

```toml
[config]
enable_scheduler = false

[[accounts]]
identifier = "Main Account"
token = "YOUR_ACCOUNT_TOKEN_HERE"

# Add more accounts:
# [[accounts]]
# identifier = "Alt Account"
# token = "ANOTHER_ACCOUNT_TOKEN"
```

Run with config file:

```bash
endfield-daily --config-file endfield-daily-helper.toml
```

The CLI automatically looks for config files in these locations:
- `./endfield-daily-helper.toml`
- `~/.config/endfield-daily-helper.toml`

## Scheduler Mode

Enable continuous operation with automatic daily sign-ins:

```toml
[config]
enable_scheduler = true

[[accounts]]
identifier = "My Account"
token = "YOUR_ACCOUNT_TOKEN"
# Optional: customize check-in time (default: 00:05 Asia/Shanghai)
checkin_time = {hour = 0, minute = 5, timezone = "Asia/Shanghai"}
```

Run the scheduler:

```bash
endfield-daily --config-file endfield-daily-helper.toml
```

The scheduler will:
- Sign in immediately on start
- Run daily at the configured time
- Keep running until stopped (Ctrl+C)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ENDFIELD_TOKEN` | ACCOUNT_TOKEN value (recommended) |
| `ENDFIELD_COOKIE` | Cookie string (backup method) |
| `ENDFIELD_CONFIG` | Path to config file |
| `ENDFIELD_DEBUG` | Enable debug mode (`1` or `true`) |

## Docker

### Docker Run

```bash
docker run --rm \
  -e ENDFIELD_TOKEN="your_token" \
  ghcr.io/Chiraitori/endfield-daily-helper
```

### Docker Compose

```yaml
version: "3"
services:
  endfield-daily:
    image: ghcr.io/chiraitori/endfield-daily-helper
    environment:
      - ENDFIELD_TOKEN=your_token_here
    restart: unless-stopped
```

### Build Locally

```bash
docker build -t endfield-daily .
docker run --rm -e ENDFIELD_TOKEN="your_token" endfield-daily
```

## Troubleshooting

### "Already signed in today"

This is normal! It means you (or this tool) already claimed today's reward.

### 401 Unauthorized Error

Your token has expired. Get a fresh `ACCOUNT_TOKEN` from browser DevTools:
1. Log out and log back in on the sign-in page
2. Copy the new `ACCOUNT_TOKEN` value
3. Update your config or CLI argument

### Token Expiration

The `ACCOUNT_TOKEN` may expire after extended periods. If sign-in fails after working previously, refresh your token from the browser.

### Debug Mode

If you encounter issues, run with `--debug` to see detailed request/response logs:

```bash
endfield-daily --token "YOUR_TOKEN" --debug
```

## How It Works

The authentication flow:
1. Exchange `ACCOUNT_TOKEN` for OAuth code via Gryphline OAuth
2. Generate credentials from OAuth code
3. Refresh signing token
4. Fetch player binding info (game role)
5. POST to attendance API with signed headers

## Publishing to PyPI

To publish this package:

```bash
# Build the package
pip install build
python -m build

# Upload to PyPI
pip install twine
twine upload dist/*
```

## License

MIT

## Credits

- Inspired by [hoyo-daily-logins-helper](https://gitlab.com/atomicptr/hoyo-daily-logins-helper)
- API reverse-engineered from [SKPORT](https://game.skport.com)

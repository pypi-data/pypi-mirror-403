# OBS Controller MCP Server

[![PyPI version](https://badge.fury.io/py/obs-controller.svg)](https://badge.fury.io/py/obs-controller)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

MCP server for controlling OBS Studio via WebSocket API. Provides **100+ tools** for complete OBS automation through Claude Code or any MCP-compatible client.

## Features

- **Full OBS Control** - Manage scenes, sources, inputs, filters, and transitions
- **Streaming & Recording** - Start/stop streams and recordings, manage replay buffer
- **Audio Management** - Control volume, mute, audio tracks, and monitoring
- **Media Playback** - Play, pause, stop, and seek media sources
- **Studio Mode** - Full support for preview/program workflow
- **Performance Monitoring** - Access OBS stats and video settings

## Tool Categories

| Category | Description | Tools |
|----------|-------------|-------|
| Scenes | Create, switch, and manage scenes | 12 |
| Inputs | Control sources, settings, and audio | 25 |
| Streaming | Stream control and service settings | 8 |
| Recording | Record, pause, chapters, and directory | 10 |
| Transitions | Manage scene transitions | 10 |
| Filters | Add/remove/configure source filters | 10 |
| Scene Items | Position, transform, visibility | 15 |
| Media | Playback control for media sources | 8 |
| Outputs | Virtual camera, replay buffer | 12 |
| General | Stats, hotkeys, profiles | 10+ |

## Installation

### From PyPI (Recommended)

```bash
pip install obs-controller
```

### From Source

```bash
git clone https://github.com/ldraney/obs-controller
cd obs-controller
poetry install
```

## Quick Start

1. **Enable OBS WebSocket** - In OBS: Tools > WebSocket Server Settings > Enable
2. **Configure connection** - Set environment variables (see Configuration below)
3. **Run the MCP server**:
   ```bash
   # If installed from PyPI
   obs-controller

   # If installed from source
   poetry run python -m obs_controller.server
   ```

## Configuration

Set environment variables or create a `.env` file:

```bash
OBS_HOST=172.25.128.1  # Windows host IP from WSL
OBS_PORT=4455
OBS_PASSWORD=          # If authentication enabled
OBS_TIMEOUT=10
```

## Claude Code Integration

### Using PyPI Installation
```bash
claude mcp add obs-controller -- obs-controller
```

### Using Source Installation
```bash
claude mcp add obs-controller -- poetry --directory /path/to/obs-controller run python -m obs_controller.server
```

## Example Usage

Once integrated with Claude Code, you can control OBS with natural language:

```
> Switch to the "Gaming" scene
> Start recording
> Mute the microphone
> Take a screenshot of the current scene
> What's the current stream status?
```

## Troubleshooting (WSL Users)

### Finding Windows Host IP
From WSL, get your Windows host IP:
```bash
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
```

### OBS WebSocket Connection Refused
1. Ensure OBS WebSocket Server is enabled (Tools > WebSocket Server Settings)
2. Check Windows Firewall allows connections on port 4455
3. Verify the host IP is correct in your `.env` file

### Authentication Errors
If you've set a password in OBS WebSocket settings, add it to your `.env`:
```bash
OBS_PASSWORD=your_password_here
```

## License

MIT License - see [LICENSE](LICENSE) for details.

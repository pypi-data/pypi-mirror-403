# Rigctl MCP Server

[![PyPI version](https://badge.fury.io/py/rigctl-mcp.svg)](https://badge.fury.io/py/rigctl-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A Model Context Protocol (MCP) server for controlling Software Defined Radio (SDR) applications via the Hamlib rigctl protocol.

## Overview

This MCP server provides AI assistants with the ability to control radio receivers and SDR software like SDR++, GQRX, and other Hamlib-compatible applications. It implements the rigctl network protocol, allowing frequency tuning, mode selection, and recording control.

## Features

- **Frequency Control**: Set and query radio frequency in Hz
- **Mode Control**: Select demodulation mode (FM, WFM, AM, USB, LSB, CW, DSB, RAW)
- **Recording Control**: Start/stop audio recording
- **Quick FM Tuning**: Convenience tool for tuning FM broadcast stations (88-108 MHz)
- **Timed Recording**: Record audio for a specified duration with automatic start/stop

## Supported Applications

Any application that supports the Hamlib rigctl network protocol:

- **SDR++** - Popular cross-platform SDR application
- **GQRX** - Linux SDR receiver
- **CubicSDR** - Cross-platform SDR application
- **rigctld** - Hamlib network daemon for hardware radios

## Installation

### Using uvx (recommended)

```bash
uvx rigctl-mcp
```

### Using pip

```bash
pip install rigctl-mcp
```

### From source (development)

```bash
git clone https://github.com/Zappatta/rigctlmcp.git
cd rigctlmcp
pip install -e .
```

## Setup

### SDR++ Configuration

1. Open SDR++
2. Enable the **Rigctl Server** module in Module Manager
3. Configure rigctl settings:
   - **Port**: 4532 (default Hamlib port)
   - **Bind Address**:
     - `0.0.0.0` if using from Docker
     - `127.0.0.1` if running locally
4. Connect to your SDR device

### Docker Note

If running the MCP server in Docker, the rigctl server must bind to `0.0.0.0` to be accessible from the container. Use `host.docker.internal:4532` to connect from inside Docker.

## Usage

### Running the MCP Server

```bash
# Using uvx
uvx rigctl-mcp

# With options
uvx rigctl-mcp --host 192.168.1.50 --port 4532 --auto-connect

# If installed via pip
rigctl-mcp
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `localhost` | Rigctl server host |
| `--port` | `4532` | Rigctl server port |
| `--auto-connect` | `false` | Automatically connect on startup |

The server communicates over stdio and can be integrated with MCP-compatible clients.

### Desktop Client Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "rigctl": {
      "command": "uvx",
      "args": ["rigctl-mcp", "--auto-connect"]
    }
  }
}
```

## Available Tools

### Connection Management

#### connect
Connect to a rigctl server.

**Parameters:**
- `host` (optional): Server address (default: "localhost")
- `port` (optional): Server port (default: 4532)

**Example:**
```json
{
  "host": "localhost",
  "port": 4532
}
```

#### disconnect
Disconnect from the rigctl server.

#### get_status
Get current connection status.

### Frequency Control

#### set_frequency
Set the radio frequency in Hz.

**Parameters:**
- `frequency_hz` (required): Frequency in Hz

**Example:**
```json
{
  "frequency_hz": 100000000
}
```
Sets frequency to 100 MHz.

#### get_frequency
Get the current radio frequency.

**Returns:** Frequency in Hz and MHz.

#### tune_fm_station
Quick tune to an FM broadcast station (88-108 MHz).

**Parameters:**
- `frequency_mhz` (required): FM frequency in MHz (e.g., 88.5, 101.1)
- `set_wfm_mode` (optional): Auto-set WFM mode (default: true)

**Example:**
```json
{
  "frequency_mhz": 88.0,
  "set_wfm_mode": true
}
```

### Mode Control

#### set_mode
Set the demodulation mode and bandwidth.

**Parameters:**
- `mode` (required): FM, WFM, AM, USB, LSB, CW, DSB, or RAW
- `bandwidth` (optional): Bandwidth in Hz (0 for automatic)

**Example:**
```json
{
  "mode": "WFM",
  "bandwidth": 200000
}
```

#### get_mode
Get the current demodulation mode and bandwidth.

### Recording Control

#### start_recording
Start recording audio. The file is saved to the application's recording directory.

#### stop_recording
Stop recording audio.

#### record_audio
Convenience tool that tunes, sets mode, and records for a specified duration.

**Parameters:**
- `frequency_hz` (required): Frequency in Hz
- `mode` (optional): Demodulation mode
- `duration_seconds` (required): Recording duration (1-3600 seconds)

**Example:**
```json
{
  "frequency_hz": 88000000,
  "mode": "WFM",
  "duration_seconds": 30
}
```

Records 30 seconds of 88 MHz in WFM mode.

## Usage Examples

### Tune to FM Station

```python
# Connect to rigctl
connect("host.docker.internal", 4532)

# Tune to 88.5 FM
tune_fm_station(88.5)

# Or manually:
set_frequency(88500000)
set_mode("WFM", 200000)
```

### Record Audio

```python
# Quick recording (automatic tuning and timing)
record_audio(
    frequency_hz=101100000,
    mode="WFM",
    duration_seconds=60
)

# Manual recording control
set_frequency(88000000)
set_mode("WFM", 200000)
start_recording()
# ... wait ...
stop_recording()
```

### Query Current Settings

```python
# Get current frequency
get_frequency()
# Returns: "Current frequency: 88000000 Hz (88.000 MHz)"

# Get current mode
get_mode()
# Returns: "Current mode: WFM, bandwidth: 200000 Hz"
```

## Rigctl Protocol

This server implements the Hamlib rigctl network protocol. Key commands:

- `F <freq>` - Set frequency in Hz
- `f` - Get frequency
- `M <mode> <bw>` - Set mode and bandwidth
- `m` - Get mode
- `AOS` / `\recorder_start` - Start recording
- `LOS` / `\recorder_stop` - Stop recording

## Testing (Development)

Test scripts are included for development:

```bash
# Clone and install for development
git clone https://github.com/Zappatta/rigctlmcp.git
cd rigctlmcp
pip install -e .

# Test connection and basic commands
python scripts/tests/test_rigctl.py

# Test FM tuning
python scripts/tests/test_fm.py

# Test recording
python scripts/tests/test_recording.py
```

## Troubleshooting

### Connection Refused

**Problem**: Cannot connect to rigctl server

**Solutions**:
- Verify SDR++ (or other application) is running
- Check rigctl server module is enabled
- Verify correct port (default: 4532)
- For Docker: ensure bind address is `0.0.0.0`
- Try: `ss -tln | grep 4532` to check if port is listening

### Commands Not Working

**Problem**: Commands return errors or don't work

**Solutions**:
- Check application logs for errors
- Verify SDR is connected and working in the application
- Some commands may not be supported by all applications
- Try the command manually using `telnet localhost 4532`

### Recording Directory

Audio recordings are saved to the application's configured recording directory:

- **SDR++**: Check Settings → Recording
- **GQRX**: Check File → Save options
- Default locations vary by platform

## Technical Details

### Protocol

Uses Hamlib rigctl protocol over TCP socket. Commands are ASCII text, responses are newline-terminated.

### Threading

Socket operations are synchronous but the MCP server runs in an async context. Long-running operations (like timed recordings) use `asyncio.sleep()`.

### Error Handling

- Connection errors return user-friendly messages
- Invalid frequencies/modes are validated by the radio application
- Recording errors are reported but don't disconnect the client

## References

- [Hamlib Rigctl Documentation](https://hamlib.sourceforge.net/html/rigctl.1.html)
- [Hamlib Network Protocol](https://github.com/Hamlib/Hamlib/wiki/Network-Device-Control)
- [SDR++ Rigctl Implementation](https://github.com/LunaeMons/SDRPlusPlus_CommunityEdition/tree/master/misc_modules/rigctl_server)
- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk)


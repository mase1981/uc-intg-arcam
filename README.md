# Arcam FMJ Integration for Unfolded Circle Remote 2/3

Control your Arcam FMJ A/V receivers and processors directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive media player control, **multi-zone support**, and **full state synchronization**.

![Arcam FMJ](https://img.shields.io/badge/Arcam-FMJ-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-arcam?style=flat-square)](https://github.com/mase1981/uc-intg-arcam/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-arcam?style=flat-square)](https://github.com/mase1981/uc-intg-arcam/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://community.unfoldedcircle.com/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-arcam/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of Arcam FMJ A/V receivers and processors through the Arcam network protocol, delivering seamless integration with your Unfolded Circle Remote for complete audio system control.

---
## 💰 Support Development

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎵 **Media Player Control**

#### **Power Management**
- **Power On/Off** - Complete power control
- **State Feedback** - Real-time power state monitoring
- **Network Control** - Full network-based control

#### **Volume Control**
- **Volume Up/Down** - Precise volume adjustment
- **Set Volume** - Direct volume control (0-100)
- **Volume Slider** - Visual volume control with dB conversion
- **Mute Toggle** - Quick mute/unmute
- **Unmute** - Explicit unmute control
- **Mute** - Explicit mute control

#### **Source Selection**
- **Input Selection** - Switch between all available inputs
- **Source List** - Automatic detection of configured sources
- **HDMI Inputs** - Full support for HDMI 1-4
- **Digital Inputs** - Optical, coaxial, and digital sources
- **Network Sources** - Streaming and network audio

### 🔊 **Multi-Zone Support**

#### **Independent Zone Control**
- **Zone 1** - Full media player control
- **Zone 2** - Independent media player control
- **Separate Configuration** - Configure zones independently
- **Individual State** - Each zone maintains its own state
- **Zone-Specific Commands** - Commands routed to correct zone

### 🌐 **Network Communication**

#### **Arcam Network Protocol**
- **Binary Protocol** - Native Arcam FMJ network protocol
- **TCP Connection** - Persistent TCP connection on port 50000
- **Real-time Updates** - Immediate state synchronization
- **Automatic Reconnection** - Resilient connection management
- **State Callbacks** - Event-driven state updates

### 🔌 **Multi-Device Support**

- **Multiple Receivers** - Control unlimited Arcam FMJ devices
- **Individual Configuration** - Each device with independent settings
- **Manual Configuration** - Direct IP address entry
- **Model Detection** - Automatic receiver model identification
- **Zone Management** - Control multiple zones per device

### **Supported Models**

#### **Arcam FMJ A/V Receivers**
- **AVR Series** - AVR390, AVR450, AVR550, AVR750, AVR850, AVR860
- **AV Series** - AV40, AV41
- **SA Series** - SA10, SA20, SA30
- **All FMJ Models** - Any Arcam FMJ device with network control

#### **Zone Support**
- **Zone 1** - Primary zone with full control
- **Zone 2** - Secondary zone with full control
- **Multi-Zone** - Configure multiple zones per device

### **Protocol Requirements**

- **Protocol**: Arcam FMJ binary protocol over TCP
- **Control Port**: 50000 (default)
- **Network Access**: Receiver must be on same local network
- **Connection Type**: Persistent TCP connection with state callbacks
- **Volume Range**: -90.0 dB to +10.0 dB (mapped to 0-100%)

### **Network Requirements**

- **Local Network Access** - Integration requires same network as receiver
- **TCP Protocol** - Firewall must allow TCP traffic on port 50000
- **Static IP Recommended** - Receiver should have static IP or DHCP reservation
- **Network Control Enabled** - Receiver must allow network control (usually enabled by default)

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-arcam/releases) page
2. Download the latest `uc-intg-arcam-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-arcam:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-arcam:
    image: ghcr.io/mase1981/uc-intg-arcam:latest
    container_name: uc-intg-arcam
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-arcam --restart unless-stopped --network host -v arcam-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-arcam:latest
```

## Configuration

### Step 1: Prepare Your Arcam FMJ Receiver

**IMPORTANT**: Receiver must be powered on and connected to your network before adding the integration.

#### Verify Network Connection:
1. Check that receiver is connected to network (WiFi or Ethernet)
2. Note the IP address from receiver's network settings menu
3. Ensure network control is enabled (usually enabled by default)
4. Verify receiver firmware is up to date

#### Network Setup:
- **Wired Connection**: Recommended for stability
- **Static IP**: Recommended via DHCP reservation
- **Firewall**: Allow TCP traffic on port 50000
- **Network Isolation**: Must be on same subnet as Remote

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The Arcam FMJ integration should appear in **Available Integrations**
3. Click **"Configure"** and enter receiver details:

#### **Configuration Fields:**

   - **Device Name**: Friendly name (e.g., "Living Room AVR")
   - **IP Address**: Enter receiver IP (e.g., 192.168.1.100)
   - **Port**: Default 50000 (change only if customized)
   - **Zone**: Select 1 or 2 depending on which zone to control
   - Click **Complete Setup**

   **Connection Test:**
   - Integration verifies receiver connectivity
   - Tests protocol communication
   - Retrieves initial state

4. Integration will create a **media player entity**:
   - **Media Player**: `media_player.arcam_[device_name]`

### Step 3: Multiple Zones (Optional)

To control both Zone 1 and Zone 2:
1. Add the integration again
2. Use the same IP address and port
3. Select different zone number (1 or 2)
4. Each zone gets its own media player entity

## Using the Integration

### Media Player Entity

Each Arcam FMJ zone's media player entity provides complete control:

- **Power Control**: On/Off with state feedback
- **Volume Control**: Volume slider (0-100, mapped to -90dB to +10dB)
- **Volume Buttons**: Up/Down with real-time feedback
- **Mute Control**: Toggle, Mute, Unmute
- **Source Selection**: Switch between all configured inputs
- **Source List**: Display of all available sources
- **State Display**: Current power, volume, mute, and source status

### Volume Conversion

The integration automatically converts between Arcam's dB range and percentage:
- **Arcam Range**: -90.0 dB (min) to +10.0 dB (max)
- **Remote Range**: 0% to 100%
- **Conversion**: Bidirectional and automatic
- **Display**: Volume shown as percentage on Remote

## ⚠️ Power Control Limitations & Solutions

### The Network Port Standby Issue

**IMPORTANT**: Arcam FMJ receivers close their network port when powered off (standby mode). This means:

- ✅ **Power OFF works**: Command is sent successfully before the port closes
- ❌ **Power ON via network does NOT work**: The network port is closed, making the receiver unreachable
- 🔄 **Auto-reconnection**: The integration continuously attempts to reconnect every 5 seconds when the entity is active on your Remote

**What happens when you power off:**
1. Integration sends power off command
2. Receiver enters standby and closes network port
3. Integration detects connection loss and begins reconnection attempts
4. Entity shows as "UNAVAILABLE" on Remote
5. Integration keeps trying to reconnect every 5 seconds indefinitely

**What happens when receiver powers on physically:**
1. Network port opens
2. Integration reconnects automatically (within 5-10 seconds)
3. Entity becomes available again
4. Full control restored

### Solution 1: Network Standby Mode (Recommended for Newer Models)

Some newer Arcam FMJ models offer the ability to keep the network port active in standby mode:

**Configuration Steps:**
1. On your Arcam receiver, go to: **HDMI Settings** → **HDMI Bypass & IP**
2. Enable: **HDMI & IP On**
3. This keeps the network port active in standby
4. Allows full power control from Unfolded Circle Remote

**Supported Models:**
- Most AVR models from 2018+
- Check your receiver's manual for "Network Standby" or "HDMI & IP" settings

### Solution 2: IR Blaster (Universal Solution)

Use your Unfolded Circle Remote's IR blaster capability with discrete power codes:

**Discrete IR Codes:**
- **Zone 1**: Protocol: RC5, Device: 16, Function: 123
- **Zone 2**: Protocol: RC5, Device: 23, Function: 123

**Note**: Power on sometimes requires two IR codes to be sent.

**Generate IR Codes:**
Using the `irgen` tool, you can generate the format for your Remote:

```bash
# Zone 1 - Send twice for reliability
irgen -i rc5 -d 16 0 123 -o broadlink_base64 -r 2

# Zone 2 - Send twice for reliability
irgen -i rc5 -d 23 0 123 -o broadlink_base64 -r 2
```

**Setup on Unfolded Circle Remote:**
1. Configure IR blaster output on your Remote
2. Add IR command as a button action
3. Use the generated code from `irgen` tool
4. Combine with the integration entity for complete control:
   - IR button for power ON
   - Integration entity for all other controls and power OFF

### Solution 3: Serial to Network Gateway (Most Reliable)

Use a serial-to-network gateway to connect to the receiver's RS232 serial port:

**Why Serial is Better:**
- Serial port is **always active**, even in standby
- Can power on the device reliably
- Most reliable communication method
- No network port closure issues

**Hardware Options:**
- Global Caché iTach IP2SL (IP to Serial)
- USR-TCP232 (TCP to Serial converter)
- Raspberry Pi with USB-to-RS232 adapter

**Configuration:**
1. Connect gateway to Arcam's RS232 port
2. Configure the integration to use the gateway's IP address
3. Full power control including power ON will work reliably

**Serial Port Settings:**
- **Baud Rate**: 38400
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None
- **Flow Control**: None

### Solution Comparison

| Solution | Power ON | Power OFF | Complexity | Cost | Reliability |
|----------|----------|-----------|------------|------|-------------|
| **Network Standby Mode** | ✅ | ✅ | Low | Free | High (if supported) |
| **IR Blaster** | ✅ | ✅ | Medium | Low | Medium (line of sight) |
| **Serial Gateway** | ✅ | ✅ | High | Medium | Very High |
| **Network Only** | ❌ | ✅ | None | Free | Medium |

### Recommended Approach

**For Newer Receivers (2018+):**
1. Try enabling Network Standby mode first (easiest)
2. If not supported, use IR blaster

**For Older Receivers:**
1. IR blaster for occasional use
2. Serial gateway for mission-critical installations

**For Home Theater Installers:**
- Serial gateway is the professional solution
- Provides most reliable control
- Eliminates all network port issues

## Troubleshooting

### Integration Not Discovered

**Symptoms**: Integration doesn't appear in Remote's integration list

**Solutions**:
1. **Check Integration Running**: Look for "Driver is up" in logs
2. **Verify driver.json**: Must exist at project root
3. **Check mDNS**: Integration publishes via mDNS for discovery
4. **Network Issues**: Ensure Remote and integration on same network
5. **Restart Integration**: Stop and restart the integration

### Cannot Connect to Receiver

**Symptoms**: "Connection refused" or timeout errors during setup

**Solutions**:
1. Verify receiver's IP address is correct
2. Ping receiver from PC/Remote: `ping 192.168.1.100`
3. Check receiver is powered on
4. Verify port 50000 is not blocked by firewall
5. Ensure receiver and Remote on same network/subnet
6. Check receiver's network control settings are enabled
7. Try power cycling receiver

### Receiver Shows as Unavailable

**Symptoms**: Entity exists but shows unavailable status

**Solutions**:
1. Check receiver is powered on
2. Verify receiver responds to network commands
3. Review integration logs for connection errors
4. Restart integration
5. Check network connectivity is stable
6. Verify firewall allows TCP on port 50000
7. Try power cycling receiver

### Commands Not Working

**Symptoms**: Commands sent but receiver doesn't respond

**Solutions**:
1. Check receiver is powered on
2. Verify receiver receives network commands
3. Check for firmware updates for receiver
4. Review integration logs for error messages
5. Ensure no other application is controlling receiver
6. Power cycle receiver and test again
7. Verify zone number is correct

### State Not Updating

**Symptoms**: Receiver changes state but Remote doesn't reflect it

**Solutions**:
1. Check connection status in logs
2. Verify network connection is stable
3. Review logs for communication errors
4. Restart integration to reset connection
5. Verify no network packet loss
6. Check receiver responds to status queries

### Volume Not Syncing

**Symptoms**: Volume changes on receiver but not reflected in Remote

**Solutions**:
1. Check connection is active
2. Verify network connection is stable
3. Review logs for communication errors
4. Manual volume changes should sync via callbacks
5. Use Remote for volume control for immediate feedback
6. Restart integration if sync is consistently failing

### Zone Not Responding

**Symptoms**: Commands sent but wrong zone or no zone responds

**Solutions**:
1. Verify zone number in configuration (1 or 2)
2. Check receiver supports the configured zone
3. Ensure zone is powered on
4. Review logs for zone-specific errors
5. Try configuring zone again with correct number
6. Some receivers require zone to be enabled in settings

## For Developers

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-arcam.git
   cd uc-intg-arcam
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Configuration:**
   ```bash
   # Windows PowerShell
   $env:UC_CONFIG_HOME = "./config"

   # Linux/Mac
   export UC_CONFIG_HOME=./config
   ```

3. **Run simulator (for testing without hardware):**
   ```bash
   python tools/arcam_simulator.py 50000
   ```

4. **Run integration:**
   ```bash
   python -m intg_arcam
   ```

5. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Two debug configurations available:
     - **Arcam Integration**: Main integration
     - **Arcam Simulator**: Test simulator

### Project Structure

```
uc-intg-arcam/
├── intg_arcam/                # Main package
│   ├── __init__.py            # Package initialization & main entry
│   ├── __main__.py            # Module execution support
│   ├── config.py              # Configuration management
│   ├── device.py              # Arcam FMJ device implementation
│   ├── driver.py              # Integration driver
│   ├── media_player.py        # Media player entity
│   └── setup_flow.py          # Setup flow with connection validation
├── tools/                     # Development tools
│   └── arcam_simulator.py     # Arcam protocol simulator
├── .github/workflows/         # GitHub Actions CI/CD
│   └── build.yml              # Automated build pipeline
├── .vscode/                   # VS Code configuration
│   └── launch.json            # Debug configuration
├── driver.json                # Integration metadata
├── requirements.txt           # Dependencies
├── pyproject.toml             # Python project config
└── README.md                  # This file
```

### Key Implementation Details

#### **Arcam FMJ Protocol**
- Uses `arcam-fmj` Python library (v1.8.2)
- Binary protocol over TCP
- Port 50000 (default)
- Persistent connection with callbacks
- Event-driven state updates

#### **Connection Management**
```python
from arcam.fmj import Client
from arcam.fmj.state import State

# Create connection
client = Client(host="192.168.1.100", port=50000)
state = State(client, zone=1)

# Start client
await client.start()

# Register callback
def state_callback():
    # Handle state updates
    pass

state.register_callback(state_callback)
await state.update()
```

#### **Device State Management**
- ExternalClientDevice base class for external library integration
- arcam-fmj library manages connection lifecycle
- Event-driven state propagation via callbacks
- Automatic reconnection on connection loss
- Graceful handling of network issues

#### **Volume Control**
```python
# Get volume (-90.0 to +10.0 dB)
volume_db = await state.get_volume()

# Set volume
await state.set_volume(-20.0)

# Convert dB to percentage
def db_to_percent(db):
    return int(((db - (-90.0)) / (10.0 - (-90.0))) * 100)

# Convert percentage to dB
def percent_to_db(percent):
    return (percent / 100.0) * (10.0 - (-90.0)) + (-90.0)
```

### Arcam FMJ Command Reference

Essential arcam-fmj library methods:
```python
# Power Control
await state.set_power(True)       # Power on
await state.set_power(False)      # Power off
power = await state.get_power()   # Query power state

# Volume Control
volume = await state.get_volume()      # Query volume (dB)
await state.set_volume(-30.0)          # Set volume (dB)
muted = await state.get_mute()         # Query mute state
await state.set_mute(True)             # Set mute state

# Source Selection
source = await state.get_source()      # Query current source
await state.set_source("HDMI 1")       # Set source
sources = await state.get_source_list() # Get available sources
```

### Arcam Simulator

The integration includes a full protocol simulator for testing without hardware:

**Features:**
- Full binary protocol emulation
- Zone 1 and Zone 2 support
- All commands (power, volume, mute, source)
- Status update packets
- Debug logging

**Usage:**
```bash
# Start simulator on default port 50000
python tools/arcam_simulator.py

# Start on custom port
python tools/arcam_simulator.py 50001
```

**Protocol Details:**
- Command format: `[0x21, zone, command, param]`
- Status updates sent automatically
- Zone codes: 1 = Zone 1, 2 = Zone 2
- Volume range: 0-99 (mapped internally)

### Testing Protocol

#### **Connection Testing**
```python
from arcam.fmj import Client
from arcam.fmj.state import State

# Test connection
client = Client("192.168.1.100", 50000)
state = State(client, zone=1)

await client.start()
power = await state.get_power()
assert power is not None

await client.stop()
```

#### **Command Testing**
```python
# Test power control
await state.set_power(True)
await asyncio.sleep(2)
power = await state.get_power()
assert power == True

# Test volume control
await state.set_volume(-30.0)
await asyncio.sleep(0.5)
volume = await state.get_volume()
assert abs(volume - (-30.0)) < 1.0

# Test mute control
await state.set_mute(True)
await asyncio.sleep(0.5)
muted = await state.get_mute()
assert muted == True
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with Arcam simulator or real device
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Style

- Follow PEP 8 Python conventions
- Use type hints for all functions
- Async/await for all I/O operations
- Comprehensive docstrings
- Descriptive variable names
- Header comments only (no inline comments)

## Credits

- **Developer**: Meir Miyara
- **Arcam**: FMJ receiver platform
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **arcam-fmj**: Python library for Arcam FMJ control
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-arcam/issues)
- **UC Community Forum**: [General discussion and support](https://community.unfoldedcircle.com/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Arcam Support**: [Official Arcam Support](https://www.arcam.co.uk/support.htm)

---

**Made with ❤️ for the Unfolded Circle and Arcam FMJ Communities**

**Thank You**: Meir Miyara

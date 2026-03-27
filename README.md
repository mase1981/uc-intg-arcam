# Arcam FMJ Integration for Unfolded Circle Remote 2/3

Control your Arcam FMJ A/V receivers and processors directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive media player control, **multi-zone support**, and **full state synchronization**.

![Arcam FMJ](https://img.shields.io/badge/Arcam-FMJ-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-arcam?style=flat-square)](https://github.com/mase1981/uc-intg-arcam/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-arcam?style=flat-square)](https://github.com/mase1981/uc-intg-arcam/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-arcam/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of Arcam FMJ A/V receivers and processors through the Arcam network protocol, delivering seamless integration with your Unfolded Circle Remote for complete audio system control.

---
## ❤️ Support Development ❤️

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
- **HDA Series** - AVR5, AVR10, AVR20, AVR30, AVR11, AVR21, AVR31
- **AV Series** - AV40, AV41
- **SA Series** - SA10, SA20, SA30
- **All FMJ Models** - Any Arcam FMJ device with network control

#### **JBL Synthesis**
- **SDP Series** - SDP-55, SDP-58
- These models use the same Arcam network protocol and are fully compatible

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
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Arcam Support**: [Official Arcam Support](https://www.arcam.co.uk/support.htm)

---

**Made with ❤️ for the Unfolded Circle and Arcam FMJ Communities**

**Thank You**: Meir Miyara

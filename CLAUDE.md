# CLAUDE.md

## How We Work Together

1. **Challenge assumptions** — do not agree with me to be agreeable. The goal is to produce high quality, accurate code. Push back when something doesn't seem right.
2. **Always review** — review code and plans to ensure they solve the actual problem. Code should be idiomatic, clean, and well documented.
3. **Do not guess** — if you don't understand something, research it. Read the spec, read the source, search the docs. Know for sure before proposing a solution.
4. **Be direct** — say what you know, what you don't know, and what you're uncertain about. Don't present speculation as fact.

## Project Overview

Arcam FMJ integration for Unfolded Circle Remote Two/3. Controls Arcam/JBL Synthesis AV receivers and processors via the Arcam IP protocol (TCP, port 50000).

Integrations can run **on the Remote itself** (sandboxed, max 100MB RAM) or **externally** on a separate host (Raspberry Pi, NAS, Docker container). When running on-device, integrations suspend during Remote standby and must re-sync all state on wake. Running externally maintains a persistent TCP connection to the receiver and serves current state on demand.

The Remote always initiates the WebSocket connection to the integration driver, regardless of where it runs.

## References

- Integration drivers overview: https://unfoldedcircle.github.io/core-api/integration-driver/index.html
- Writing an integration driver: https://unfoldedcircle.github.io/core-api/integration-driver/write-integration-driver.html
- Media player entity: https://unfoldedcircle.github.io/core-api/entities/entity_media_player.html
- Remote entity: https://unfoldedcircle.github.io/core-api/entities/entity_remote.html
- Sensor entity: https://unfoldedcircle.github.io/core-api/entities/entity_sensor.html
- Core API GitHub: https://github.com/unfoldedcircle/core-api
- Protocol spec — 860 series (AV860, AVR850, AVR550, AVR390, SR250): https://www.arcam.co.uk/ugc/tor/avr850/RS232/RS232_860_850_550_390_250_SH274E_D_181018.pdf
- Protocol spec — HDA series (AVR5/10/11/20/21/30/31/40/41, AV40): https://www.arcam.co.uk/ugc/tor/AVR11/Custom%20Installation%20Notes/RS232_5_10_20_30_40_11_21_31_41__SH289E_F_07Oct21.pdf
- Protocol spec — HDA/JBL Synthesis (SDP-55/58, SDR-35/38): https://www.jblsynthesis.com/on/demandware.static/-/Sites-masterCatalog_Harman/default/dwee3561f4/pdfs/RS232_SDR35_38_SDP55_58_SH289E_E_2Jun21.pdf
- Protocol spec — SA series (SA10, SA20): https://www.arcam.co.uk/ugc/tor/SA20/Custom%20Installation%20Notes/SH277E_RS232_SA10_SA20_B.pdf
- Protocol spec — PA series (PA720, PA240, PA410): https://www.arcam.co.uk/ugc/tor/PA240/Custom%20Installation%20Notes/RS232_PA720_PA240_PA410_SH305E_3.pdf
- Protocol spec — ST series (ST60): https://www.arcam.co.uk/ugc/tor/ST60/Custom%20Installation%20Notes/SH309_RS232_ST60_C.pdf

## Arcam Receiver Limitations

### Single-Threaded IP Control

The Arcam IP protocol is **RS232 over TCP**. The receiver's IP control module handles one command at a time:

- **No concurrent queries**: simultaneous commands overwhelm the receiver and cause timeout cascades.
- **No bulk queries**: every state requires its own request/response round-trip.
- **Heartbeat sensitivity**: the arcam-fmj library sends a POWER query every 5s as heartbeat. Blocking the connection too long triggers a disconnect.
- **Sequential queries with delays** are required. The trickle system uses 0.3s (Group 1) to 0.4s (Group 2/3) delays between commands, above the library's 0.2s throttle.

### Push Events

The receiver pushes unsolicited STATUS_UPDATE packets on state changes (volume, source, etc.). TCP guarantees delivery while connected, so push events are reliable — polling is only a safety net for edge cases.

## Testing

No automated tests. Deploy to UC Remote and verify: entity states populate on connect, commands work (power, volume, source), push events update state in real-time, and sleep/wake cycle recovers cleanly. Check logs for disconnect loops ("Connection lost" / "Reconnection attempt" cycling).

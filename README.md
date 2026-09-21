# ThingsBoard PLC Data Collection

This repository provides an operational guide and working template for collecting industrial data from programmable logic controllers (PLCs) via OPC-UA into the ThingsBoard platform using a local ThingsBoard and ThingsBoard IoT Gateway stack. It includes a simulated OPC-UA PLC server enabling end-to-end pipeline validation and telemetry mapping verification before connecting to physical production hardware.

## Architecture

```
[PLC / Simulated PLC] --(OPC-UA)--> [ThingsBoard Gateway] --(MQTT)--> [ThingsBoard]
```

## Prerequisites

- **Docker & Docker Compose**: Docker Engine 20.10+ and Docker Compose v2.0+ installed.
- **Python 3.10+**: Required only if running the simulated PLC locally for pre-hardware testing.
- **Network Connectivity**: Network access to your target PLC (port 4840 or custom OPC-UA port) for production deployment.

## Guides

Follow these operational guides in sequential order:

1. [Setup ThingsBoard Platform and Gateway](guides/01-setup-thingsboard-platform-and-gateway.md) — Configure environment variables, deploy the ThingsBoard and Gateway stack, and verify services.
2. [Test Your Setup with a Simulated PLC](guides/02-test-your-setup-with-a-simulated-plc.md) — Launch the simulated OPC-UA server, configure the connector, and validate telemetry flow.
3. [Connect a Real PLC](guides/03-connect-a-real-plc.md) — Discover PLC endpoints, configure security profiles, and transition from simulated to production hardware.
4. [Mapping PLC Registers to Telemetry Keys](guides/04-mapping-plc-registers-to-telemetry-keys.md) — Reference guide for node paths, identifiers, tag patterns, and telemetry mappings.
5. [Multiple PLCs](guides/05-multiple-plcs.md) — Architecture and configurations for handling multiple devices or multi-PLC environments.
6. [Troubleshooting](guides/06-troubleshooting.md) — Diagnostic strategies for network issues, node discovery errors, security policies, and subscription fallbacks.

## License & Contributions

Open documentation and templates for ThingsBoard IoT implementations. For contributions, bug fixes, or enhancements, please submit an issue or pull request.

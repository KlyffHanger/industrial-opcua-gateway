# 05 — Multiple PLCs

Industrial installations frequently involve multiple machines or controllers. Depending on your automation architecture, this is configured in one of two ways:

1. **Scenario A**: Multiple logical devices exposed under a **single OPC-UA server** (e.g., a central PLC, edge PC, or line gateway aggregating multiple sub-stations).
2. **Scenario B**: Multiple physical PLCs on **different IP addresses**, each hosting its own independent OPC-UA server.

---

## Scenario A: Multiple Devices Under One OPC-UA Server

When a single OPC-UA server hosts multiple machines or lines, configure **one connector** with **multiple entries in the `mapping` array**.

### Architecture
```
+------------------------------------------+
|       Single OPC-UA Server (IP: 4840)    |
|   Root/Objects/                          |
|      ├── Station1 (Object)               |
|      └── Station2 (Object)               |
+------------------------------------------+
                    │
                    ▼
   [Single ThingsBoard Connector]
    ├── mapping[0] -> Station1
    └── mapping[1] -> Station2
                    │
                    ▼
   [ThingsBoard: 2 distinct devices]
```

### Connector Configuration Snippet

```json
{
  "server": {
    "url": "opc.tcp://192.168.1.50:4840",
    "timeoutInMillis": 5000,
    "scanPeriodInMillis": 3600000,
    "pollPeriodInMillis": 2000,
    "enableSubscriptions": true,
    "security": "Basic256Sha256",
    "identity": { "type": "username", "username": "tb_operator", "password": "SecretPassword" }
  },
  "mapping": [
    {
      "deviceNodeSource": "path",
      "deviceNodePattern": "Root\\.Objects\\.2:Station1",
      "deviceInfo": {
        "deviceNameExpression": "Assembly-Station-01",
        "deviceNameExpressionSource": "constant",
        "deviceProfileExpressionSource": "constant",
        "deviceProfileExpression": "Station"
      },
      "attributes": [],
      "timeseries": [
        { "key": "cycleTime", "type": "path", "value": "${CycleTime}" },
        { "key": "status", "type": "path", "value": "${Status}" }
      ]
    },
    {
      "deviceNodeSource": "path",
      "deviceNodePattern": "Root\\.Objects\\.2:Station2",
      "deviceInfo": {
        "deviceNameExpression": "Packaging-Station-02",
        "deviceNameExpressionSource": "constant",
        "deviceProfileExpressionSource": "constant",
        "deviceProfileExpression": "Station"
      },
      "attributes": [],
      "timeseries": [
        { "key": "weight", "type": "path", "value": "${PackageWeight}" },
        { "key": "rejectedCount", "type": "path", "value": "${RejectCounter}" }
      ]
    }
  ],
  "name": "central-line-connector",
  "logLevel": "INFO",
  "configVersion": "3.8.4"
}
```

Each mapping entry discovers its corresponding device node pattern and provisions an independent device entity in ThingsBoard with its own metrics.

---

## Scenario B: Multiple Separate PLCs (Separate IP Addresses)

When PLCs run on distinct IP addresses (e.g., `192.168.1.10`, `192.168.1.20`), create **multiple distinct connectors** within ThingsBoard Gateway. Each connector targets a dedicated `server.url` and manages its own connection lifecycle, credentials, and mapping rules.

### Architecture
```
[PLC 1: 192.168.1.10] ───(OPC-UA)───> [Connector: plc-line-1] ──┐
                                                                   ├──> [ThingsBoard Gateway] ──> [ThingsBoard]
[PLC 2: 192.168.1.20] ───(OPC-UA)───> [Connector: plc-line-2] ──┘
```

### Gateway Connectors Setup

In the ThingsBoard Web UI (**Entities** → **Gateways** → select your gateway → **Connectors Configuration** tab), add both connectors:

1. **Connector 1 (`plc-line-1`)**: Type `OPC-UA`, paste the configuration from `plc-line-1.json`.
2. **Connector 2 (`plc-line-2`)**: Type `OPC-UA`, paste the configuration from `plc-line-2.json`.

If managing configurations locally via file volumes, register both in the gateway's connector definitions:
```json
[
  {
    "name": "plc-line-1",
    "type": "opcua",
    "configuration": "plc-line-1.json"
  },
  {
    "name": "plc-line-2",
    "type": "opcua",
    "configuration": "plc-line-2.json"
  }
]
```

### Connector 1: `plc-line-1.json`
```json
{
  "server": {
    "url": "opc.tcp://192.168.1.10:4840",
    "timeoutInMillis": 5000,
    "scanPeriodInMillis": 3600000,
    "pollPeriodInMillis": 1000,
    "enableSubscriptions": true,
    "security": "None",
    "identity": { "type": "anonymous" }
  },
  "mapping": [
    {
      "deviceNodeSource": "path",
      "deviceNodePattern": "Root\\.Objects\\.3:Extruder",
      "deviceInfo": {
        "deviceNameExpression": "Extruder-01",
        "deviceNameExpressionSource": "constant",
        "deviceProfileExpressionSource": "constant",
        "deviceProfileExpression": "Extruder"
      },
      "attributes": [],
      "timeseries": [
        { "key": "meltTemperature", "type": "path", "value": "${MeltTemp}" },
        { "key": "screwSpeed", "type": "path", "value": "${Rpm}" }
      ]
    }
  ],
  "name": "plc-line-1",
  "logLevel": "INFO",
  "configVersion": "3.8.4"
}
```

### Connector 2: `plc-line-2.json`
```json
{
  "server": {
    "url": "opc.tcp://192.168.1.20:4840",
    "timeoutInMillis": 5000,
    "scanPeriodInMillis": 3600000,
    "pollPeriodInMillis": 1000,
    "enableSubscriptions": true,
    "security": "Basic256Sha256",
    "identity": {
      "type": "username",
      "username": "tb_admin",
      "password": "Line2Password"
    }
  },
  "mapping": [
    {
      "deviceNodeSource": "path",
      "deviceNodePattern": "Root\\.Objects\\.2:Chiller",
      "deviceInfo": {
        "deviceNameExpression": "Chiller-Unit-02",
        "deviceNameExpressionSource": "constant",
        "deviceProfileExpressionSource": "constant",
        "deviceProfileExpression": "Chiller"
      },
      "attributes": [],
      "timeseries": [
        { "key": "coolantFlow", "type": "path", "value": "${FlowRate}" },
        { "key": "returnTemp", "type": "path", "value": "${ReturnTemperature}" }
      ]
    }
  ],
  "name": "plc-line-2",
  "logLevel": "INFO",
  "configVersion": "3.8.4"
}
```

### Advantages of Separate Connectors:
- **Isolation**: A temporary network drop or reboot on PLC 1 does not disrupt telemetry collection from PLC 2.
- **Independent Security**: Each PLC can use distinct authentication schemes (e.g., anonymous vs. encrypted username/password).
- **Independent Polling Cycles**: High-speed machines can be polled at 500ms intervals, while environmental chillers can be polled at 10-second intervals.

---

## Next Steps

To troubleshoot any network connectivity, address mapping, or certificate issues across your setup, proceed to [06 — Troubleshooting](06-troubleshooting.md).

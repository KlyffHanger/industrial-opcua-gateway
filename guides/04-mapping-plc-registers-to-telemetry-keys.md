# 04 — Mapping PLC Registers to Telemetry Keys

This guide explains how OPC-UA data nodes in a PLC are transformed into device telemetry and attributes inside the ThingsBoard platform.

---

## Where Mapping Lives

A common point of confusion for new users is where tag translation is configured:

- **Mapping is defined entirely inside the ThingsBoard IoT Gateway's OPC-UA Connector configuration** (e.g., `gateway-config/opcua-connector.json` or through the ThingsBoard Web UI).
- **Mapping does NOT exist inside ThingsBoard**. ThingsBoard is completely agnostic to OPC-UA node IDs, tag addresses, or PLC data structures. It merely receives standard JSON key-value pairs (telemetry and attributes) published over MQTT by the gateway.

```
+--------------------------+          +------------------------+          +-----------------------+
|        PLC Node          |  OPC-UA  |   ThingsBoard Gateway  |   MQTT   |      ThingsBoard      |
| "Temperature" (ns=2;i=2) | -------->| maps to key            | -------->| Device: Test-PLC      |
| Current Value: 24.5      |          | "temperature": 24.5    |          | Telemetry:            |
|                          |          |                        |          |   temperature = 24.5  |
+--------------------------+          +------------------------+          +-----------------------+
```

---

## Structure of a Mapping Entry

Inside the connector JSON, the `"mapping"` array holds one or more device mapping objects. Each object defines:
1. **Device discovery (`deviceNodePattern`)**: Where to locate the device in the OPC-UA address space.
2. **Device identification (`deviceInfo`)**: How the device is named and classified in ThingsBoard.
3. **Data extraction (`timeseries` and `attributes`)**: Which tags under the device node are ingested and what telemetry keys they map to.

### Example Mapping Chunk

```json
{
  "deviceNodeSource": "path",
  "deviceNodePattern": "Root\\.Objects\\.2:Device1",
  "deviceInfo": {
    "deviceNameExpression": "Test-PLC",
    "deviceNameExpressionSource": "constant",
    "deviceProfileExpressionSource": "constant",
    "deviceProfileExpression": "Device"
  },
  "attributes": [
    {
      "key": "serialNumber",
      "type": "path",
      "value": "${SerialNo}"
    }
  ],
  "timeseries": [
    {
      "key": "temperature",
      "type": "path",
      "value": "${Temperature}"
    },
    {
      "key": "humidity",
      "type": "path",
      "value": "${Humidity}"
    }
  ]
}
```

---

## How Field Resolution Works

### 1. `deviceNodePattern`
- Identifies the root node representing the physical or logical device within the OPC-UA tree.
- When `deviceNodeSource` is `"path"`, the pattern uses dot-separated browsable path segments escaped with double backslashes:
  ```
  Root\\.Objects\\.2:Device1
  ```
  - `Root`: Top-level root node.
  - `Objects`: The standard OPC-UA folder holding application data.
  - `2:Device1`: The node name prefixed by its namespace index (`2`).
- You can also use regular expressions in `deviceNodePattern` (e.g. `Root\\.Objects\\.2:Station[0-9]+`) to automatically discover multiple devices matching a pattern.

### 2. Relative Tag Paths (`${TagName}`)
- Once the gateway resolves the device node via `deviceNodePattern`, any entries in `timeseries` or `attributes` are evaluated **relative to that device node**.
- In the example:
  ```json
  { "key": "temperature", "type": "path", "value": "${Temperature}" }
  ```
  - `key`: The metric name displayed in ThingsBoard (e.g., `temperature`).
  - `type`: `"path"` indicates the tag is resolved by child node browse name.
  - `value`: `"${Temperature}"` instructs the gateway to find a child node named `Temperature` directly under the device node and read its value.

### 3. Absolute NodeId Addressing (`type: "nodeId"`)
If your PLC organizes tags in non-hierarchical structures or complex nested arrays, you can target nodes directly by their OPC-UA NodeId instead of browsing paths:

```json
{
  "key": "oilPressure",
  "type": "nodeId",
  "value": "ns=3;s=DB10.DBW20"
}
```
Supported NodeId formats:
- String identifier: `ns=3;s=Machine.Sensors.Pressure`
- Numeric identifier: `ns=2;i=1042`
- GUID identifier: `ns=1;g=12345678-1234-1234-1234-123456789abc`

---

## Attributes vs. Timeseries

| Category | Typical Data Types | Purpose in ThingsBoard | Update Frequency |
| :--- | :--- | :--- | :--- |
| **`attributes`** | String, Int, Boolean | Static or semi-static metadata: serial numbers, firmware version, rated voltage, IP address, installation date. | Emitted once on connection or only when the tag value changes. Stored in ThingsBoard device attributes table. |
| **`timeseries`** | Double, Float, Int, Boolean | Dynamic metrics: temperature, pressure, flow rate, cycle counter, alarm flags. | Emitted periodically according to `pollPeriodInMillis` or OPC-UA subscription notifications. Stored in ThingsBoard timeseries database for trending, dashboards, and alerting. |

---

## Worked Mapping Reference Table

Use this reference table to map typical PLC memory structures into OPC-UA tags and ThingsBoard telemetry:

| Industrial Domain | PLC Register / Tag | OPC-UA Tag Path or NodeId | Target Category | ThingsBoard Key | Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Process Sensor** | `DB10.DBD0 (REAL)` | `${Temperature}` or `ns=2;s="DB10"."Temp"` | `timeseries` | `temperature` | Double |
| **Environmental** | `DB10.DBD4 (REAL)` | `${Humidity}` or `ns=2;s="DB10"."Hum"` | `timeseries` | `humidity` | Double |
| **Motor Drive** | `MW100 (INT)` | `${MotorCurrent}` or `ns=2;s="Drive1"."Amps"` | `timeseries` | `motorCurrent` | Double |
| **Line Status** | `M0.1 (BOOL)` | `${RunningState}` or `ns=2;s="Line"."IsRunning"` | `timeseries` | `isRunning` | Boolean |
| **Production Counter** | `MD20 (DINT)` | `${PartsProduced}` or `ns=2;s="Counter"."Total"` | `timeseries` | `partCount` | Integer |
| **Identification** | `DB1.DBB10..30 (STRING)` | `${SerialNumber}` or `ns=2;s="Info"."Serial"` | `attributes` | `serialNumber` | String |
| **Maintenance** | `DB1.DBD40 (REAL)` | `${OperatingHours}` or `ns=2;s="Info"."Hours"` | `attributes` | `operatingHours` | Double |

---

## Next Steps

If your facility operates multiple machines or multi-station controllers, proceed to [05 — Multiple PLCs](05-multiple-plcs.md) to learn how to scale your gateway configuration.

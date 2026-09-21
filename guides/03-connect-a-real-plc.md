# 03 — Connect a Real PLC

This guide walks through transitioning from the local simulated PLC to a physical, production Programmable Logic Controller (PLC) communicating over OPC-UA.

---

## Step 1: Browse the PLC Address Space Using an OPC-UA Client

Before writing or modifying your connector configuration, inspect the physical PLC's address space using an OPC-UA diagnostic client such as **Unified Automation UaExpert** or **Prosys OPC UA Client**.

1. Connect your workstation to the operational technology (OT) network or industrial VLAN hosting the PLC.
2. Launch your OPC-UA client and add a new server connection:
   - Provide the PLC's IP address and port (default OPC-UA port is `4840`):
     ```
     opc.tcp://192.168.1.50:4840
     ```
3. Discover endpoints:
   - Browse the security policies presented by the PLC (e.g., `None`, `Basic256Sha256 - Sign & Encrypt`).
   - Select the required security policy and user token type (Anonymous, Username/Password, or Certificate).
4. Connect and explore the address space tree under `Root` → `Objects`:
   - Identify the parent Object node for your machine, station, or controller.
   - Note the **NodeId** (e.g., `ns=3;s="Line1"."Station1"`) or browsable path.
   - Locate the child Variable nodes (e.g., `MotorSpeed`, `Pressure`, `CycleCounter`, `AlarmActive`).
   - Confirm data types (e.g., `Double`, `Int32`, `Boolean`, `String`).

---

## Step 2: Configuration Differences (Simulation vs. Production)

Industrial PLCs (such as Siemens S7-1200/1500, Beckhoff TwinCAT, Rockwell Allen-Bradley, or Schneider Modicon) differ from the local test simulator in three primary areas:

| Configuration Property | Simulated Setup | Real PLC (Production) | Description / Notes |
| :--- | :--- | :--- | :--- |
| **`server.url`** | `opc.tcp://host.docker.internal:4840/freeopcua/server/` | `opc.tcp://192.168.1.50:4840` | Real IP or DNS hostname reachable from the gateway container on your factory network. |
| **`server.security`** | `"None"` | `"Basic256Sha256"` (or `"Aes128_Sha256_RsaOaep"`) | Production PLCs enforce cryptographic signing and encryption to protect industrial traffic. |
| **`server.identity`** | `{"type": "anonymous"}` | `{"type": "username", "username": "...", "password": "..."}` or `{"type": "cert"}` | Authentication credentials created in the PLC's engineering software (e.g., TIA Portal, TwinCAT). |
| **`deviceNodePattern`** | `Root\\.Objects\\.<IDX>:Device1` | `Root\\.Objects\\.3:"MachineBlock"` or specific NodeId pattern | Must match the actual path in the PLC's server address space. |
| **`timeseries.value`** | `${Temperature}` | `${MotorSpeed}` / `${"DB_Telemetry"."Pressure"}` | Variable names as exposed by the PLC symbol table. |
| **`enableSubscriptions`**| `false` (polling mode) | `true` or `false` | `true` allows real-time event-driven updates from PLCs with robust subscription engines; fallback to `false` for high-frequency polling. |
| **`pollPeriodInMillis`** | `5000` (5s) | `1000` to `60000` | Adjust based on telemetry dynamics and network bandwidth requirements. |

---

## Step 3: Configure Gateway with Real PLC Settings

Update your connector configuration (either in ThingsBoard UI under **Connectors Configuration** or within your JSON configuration file):

```json
{
  "server": {
    "url": "opc.tcp://192.168.1.50:4840",
    "timeoutInMillis": 10000,
    "scanPeriodInMillis": 3600000,
    "pollPeriodInMillis": 2000,
    "enableSubscriptions": true,
    "subCheckPeriodInMillis": 100,
    "showMap": false,
    "security": "Basic256Sha256",
    "identity": {
      "type": "username",
      "username": "tb_operator",
      "password": "SecurePassword123"
    }
  },
  "mapping": [
    {
      "deviceNodeSource": "path",
      "deviceNodePattern": "Root\\.Objects\\.3:PackagingLine",
      "deviceInfo": {
        "deviceNameExpression": "Packaging-Line-01",
        "deviceNameExpressionSource": "constant",
        "deviceProfileExpressionSource": "constant",
        "deviceProfileExpression": "PackagingMachine"
      },
      "attributes": [
        { "key": "serialNumber", "type": "path", "value": "${SerialNo}" },
        { "key": "firmwareVersion", "type": "path", "value": "${FirmwareVersion}" }
      ],
      "timeseries": [
        { "key": "lineSpeed", "type": "path", "value": "${ActualSpeed}" },
        { "key": "inletPressure", "type": "path", "value": "${SensorPressure}" },
        { "key": "motorCurrent", "type": "path", "value": "${CurrentAmps}" }
      ],
      "rpc_methods": [],
      "attributes_updates": []
    }
  ],
  "logLevel": "INFO",
  "name": "production-plc-connector",
  "enableRemoteLogging": false,
  "configVersion": "3.8.4"
}
```

---

## Step 4: Stop the Test Simulator

To prevent overlapping telemetry, naming collisions, or unnecessary host resource usage, stop and deactivate the simulated PLC server:

1. In the terminal running `fake_opcua_server.py`, press `Ctrl + C`.
2. Deactivate the virtual environment:
   ```bash
   deactivate
   ```
3. In ThingsBoard UI, if you no longer need the mock `Test-PLC` device entity:
   - Navigate to **Entities** → **Devices**.
   - Select `Test-PLC` and choose **Delete**.

---

## Step 5: Production Security Best Practices

When deploying ThingsBoard in production environments:

1. **Network Segmentation**:
   - Isolate the PLC and ThingsBoard Gateway on an industrial OT VLAN.
   - Restrict traffic so only the ThingsBoard Gateway can reach port `4840` on the PLC.
2. **Mutual TLS & Certificate Trust**:
   - If using `SignAndEncrypt` with client certificates, ensure the ThingsBoard Gateway client certificate is uploaded to the PLC's trusted certificates store (e.g., in Siemens TIA Portal under Security Settings → Certificates).
   - Verify the PLC's server certificate is trusted by the gateway.
3. **Gateway Access Token Rotation**:
   - Store `.env` securely on the host. Do not commit credentials or tokens to version control.
   - Rotate Gateway device access tokens periodically through the ThingsBoard interface.

---

## Next Steps

To deep-dive into how tag addresses and node patterns are resolved, proceed to [04 — Mapping PLC Registers to Telemetry Keys](04-mapping-plc-registers-to-telemetry-keys.md).

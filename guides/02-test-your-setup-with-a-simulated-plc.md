# 02 — Test Your Setup with a Simulated PLC

The simulated PLC script allows you to validate your end-to-end telemetry pipeline locally before touching physical factory hardware or networking equipment.

Once telemetry flows from the test server through ThingsBoard Gateway into ThingsBoard, you have verified:
1. The ThingsBoard Gateway ↔ ThingsBoard MQTT connection and credential authentication.
2. The OPC-UA connector scanning, node resolution, and polling mechanics.
3. The telemetry mapping structure and key transformations.

Any issues encountered when connecting a physical PLC later will be isolated to PLC-specific factors (IP reachability, firewall settings, authentication credentials, or tag addressing), rather than architectural defects in your gateway or platform.

---

## Step 1: Install Dependencies and Launch the Simulator

The simulated server runs locally on your host machine outside Docker. It opens an OPC-UA endpoint on port `4840` and registers a mock device (`Device1`) with two dynamic metrics: `Temperature` and `Humidity`.

1. Open a new terminal on your host machine.
2. Navigate to the `test-opcua-server/` directory:
   ```bash
   cd test-opcua-server
   ```
3. Set up a Python virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Start the simulated server:
   ```bash
   python3 fake_opcua_server.py
   ```

5. Keep this terminal open. You will see output similar to:
   ```text
   INFO:fake_opcua_server:Starting simulated PLC server...
   INFO:fake_opcua_server:Namespace index: 2
   INFO:fake_opcua_server:Temperature NodeId: ns=2;i=2
   INFO:fake_opcua_server:Humidity NodeId: ns=2;i=3
   INFO:fake_opcua_server:Server started. Endpoint: opc.tcp://0.0.0.0:4840/freeopcua/server/
   INFO:fake_opcua_server:Temperature=24.32  Humidity=52.18
   INFO:fake_opcua_server:Temperature=27.85  Humidity=46.90
   ```

> [!IMPORTANT]
> **Take note of the Namespace index printed in the log output** (usually `2`). You will insert this value into the connector configuration in the next step.

---

## Step 2: Configure the OPC-UA Connector in ThingsBoard

Now configure ThingsBoard Gateway to connect to the running simulation server and extract telemetry.

### Option A: Using the ThingsBoard Web UI (Recommended)

1. Open your browser and log into ThingsBoard at [http://localhost:8080](http://localhost:8080).
2. Go to **Entities** → **Gateways**.
3. Click on your gateway (`OPCUA-Gateway`).
4. Click the **Connectors Configuration** tab.
5. Click **Add connector** (or the **+** button):
   - **Type**: Select `OPC-UA`
   - **Name**: Enter `tb-plc-connector`
6. Navigate to the JSON configuration editor:
   - Click on the selected connector to open its settings.
   - Choose **Advanced settings** (or the Settings/Edit mode).
   - Click on the **Configuration** tab (which opens the raw JSON editor).
   - Open [`gateway-config/opcua-connector.json`](../gateway-config/opcua-connector.json) from this repository and copy its contents.
   - Replace `<NAMESPACE_INDEX>` with the actual namespace index printed by your Python script (e.g., `2`):
     ```json
     "deviceNodePattern": "Root\\.Objects\\.2:Device1"
     ```
   - Paste this JSON into the **Configuration** tab editor.
7. Click **Save**. ThingsBoard will remotely push the configuration to ThingsBoard Gateway automatically.

### Option B: Local File Configuration

If managing configuration files directly on the gateway volume:
1. Copy `gateway-config/opcua-connector.json` to your gateway configuration directory.
2. Replace `<NAMESPACE_INDEX>` with the actual integer value (e.g., `2`).
3. Add the connector entry into `tb_gateway.json` under `connectors`:
   ```json
   {
     "name": "tb-plc-connector",
     "type": "opcua",
     "configuration": "opcua-connector.json"
   }
   ```
4. Restart the gateway container:
   ```bash
   docker compose restart tb-gateway
   ```

---

## Step 3: Verify Connector Discovery and Telemetry Stream

1. Check the gateway logs to verify the connection to the simulated server:
   ```bash
   docker compose logs -f tb-gateway
   ```
   You should see entries confirming the connector initialized and subscribed to/polled the nodes:
   ```text
   [INFO] - [opcua_connector.py] - Starting OPC-UA connector...
   [INFO] - [opcua_connector.py] - Connected to OPC-UA server: opc.tcp://host.docker.internal:4840/freeopcua/server/
   [INFO] - [opcua_connector.py] - Scanning devices on server...
   [INFO] - [opcua_connector.py] - Device Test-PLC was found
   ```

2. Return to the ThingsBoard Web UI:
   - Go to **Entities** → **Devices**.
   - You will see a newly discovered device named **`Test-PLC`**.
   - Click on **`Test-PLC`** and select the **Latest Telemetry** tab.
3. Observe live updating values:
   - `temperature`: updating every 5 seconds with values between `20.0` and `30.0`.
   - `humidity`: updating every 5 seconds with values between `40.0` and `60.0`.

> [!TIP]
> **Adding Your Own Device & Custom Key Mappings**:
> You are not limited to `Test-PLC`. You can add your own devices and map custom keys directly within the connector configuration:
> - **Custom Device Name**: Modify `"deviceNameExpression": "Your-Device-Name"` under `deviceInfo`.
> - **Custom Telemetry Keys**: In the `"timeseries"` array, define your own metric names and matching OPC-UA tag paths:
>   ```json
>   { "key": "motorSpeed", "type": "path", "value": "${MotorSpeed}" },
>   { "key": "linePressure", "type": "path", "value": "${LinePressure}" }
>   ```
> - **Custom Attributes**: In the `"attributes"` array, map static metadata such as serial numbers or model info:
>   ```json
>   { "key": "serialNumber", "type": "path", "value": "${SerialNumber}" }
>   ```
> For complete details on syntax, relative paths, and direct NodeId addressing, refer to [04 — Mapping PLC Registers to Telemetry Keys](04-mapping-plc-registers-to-telemetry-keys.md).

---

## Milestone Complete

You have successfully validated the complete data pipeline:
```
[Simulated PLC (Port 4840)] 
           ↓ (OPC-UA binary protocol)
[ThingsBoard Gateway (tb-gateway container)]
           ↓ (MQTT payload)
[ThingsBoard (localhost:8080)]
```

Now that you know the pipeline is working as expected, proceed to [03 — Connect a Real PLC](03-connect-a-real-plc.md) to integrate physical production equipment.

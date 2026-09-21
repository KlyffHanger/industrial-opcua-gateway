# 06 — Troubleshooting and Reference

This guide provides practical diagnostics and remedies for the most common issues encountered when connecting PLCs via OPC-UA to the ThingsBoard platform.

---

## 1. Gateway Cannot Reach ThingsBoard

### Symptoms
- Gateway logs show: `Connection refused`, `Failed to connect to ThingsBoard on thingsboard:1883`, or `MQTT connection error`.
- Gateway entity remains "Inactive" or "Offline" in ThingsBoard.

### Diagnostic Steps & Solutions
1. **Verify Docker Network**:
   Ensure both containers are running on the same Docker Compose network:
   ```bash
   docker network inspect $(basename "$PWD")_default
   ```
   Both `thingsboard` and `tb-gateway` should be listed with active IP assignments.
2. **Verify Environment Variables in `.env`**:
   Ensure `TB_GW_HOST` matches the service name (`thingsboard`) and `TB_GW_PORT` is `1883`:
   ```env
   TB_GW_HOST=thingsboard
   TB_GW_PORT=1883
   ```
3. **Verify Access Token**:
   If the gateway logs show `Connection error: 4` or `Connection error: Bad user name or password`, the access token in `.env` does not match the token configured in ThingsBoard.
   - Go to ThingsBoard UI → **Entities** → **Gateways** → Click your Gateway → Copy token under **Details**.
   - Paste the exact token into `.env` under `TB_GW_ACCESS_TOKEN`.
   - Restart the gateway container:
     ```bash
     docker compose restart tb-gateway
     ```

---

## 2. Gateway Cannot Reach the PLC

### Symptoms
- Connector logs show: `Cannot connect to server`, `Connection timed out`, or `Endpoint not found`.

### Diagnostic Steps & Solutions
1. **Network Reachability Test**:
   From the host machine, test whether the PLC's OPC-UA port is open and listening:
   ```bash
   nc -zv <plc-ip> 4840
   ```
   Or from inside the gateway container:
   ```bash
   docker compose exec tb-gateway python3 -c "import socket; s = socket.socket(); s.settimeout(3); s.connect(('<plc-ip>', 4840)); print('Connected!')"
   ```
2. **Firewall & Routing Rules**:
   - Verify that firewalls on switches, edge routers, or the host machine are not blocking TCP port `4840`.
   - If connecting to the simulated PLC running on the host machine, verify that the connector URL uses `host.docker.internal` and that `docker-compose.yml` includes `extra_hosts: ["host.docker.internal:host-gateway"]`.
3. **PLC Endpoint URL Path**:
   Some PLCs require a specific endpoint path suffix (e.g., `/freeopcua/server/` or `/UA/Server`). Verify the exact path required by the PLC using an OPC-UA client tool.

---

## 3. "Node Not Found" Errors

### Symptoms
- Gateway logs show: `BadNodeIdUnknown`, `Node not found in address space`, or warning messages that tags could not be read.
- Device entity appears in ThingsBoard, but Latest Telemetry shows empty values.

### Diagnostic Steps & Solutions
1. **Namespace Index Drift**:
   In OPC-UA servers, namespace indexes are dynamic integer indexes assigned at server startup. If the PLC restarts or project code is recompiled, namespace indexes can shift (e.g., from `2` to `3`).
   - Use an OPC-UA client (e.g., UaExpert) to verify the current namespace index for your device.
   - If the PLC uses stable string NodeIds, use explicit NodeIds in your configuration:
     ```json
     { "key": "speed", "type": "nodeId", "value": "ns=2;s=Motor.ActualSpeed" }
     ```
2. **Escaping in `deviceNodePattern`**:
   Dot separators in path strings must be escaped with double backslashes in JSON:
   - Correct: `"Root\\.Objects\\.2:Device1"`
   - Incorrect: `"Root.Objects.2:Device1"`
3. **Case Sensitivity**:
   OPC-UA node names and browse names are case-sensitive. Ensure `${Temperature}` matches the casing defined in the PLC symbol table exactly.

---

## 4. Subscription Failures & High CPU

### Symptoms
- Connector logs show: `BadSubscriptionIdInvalid`, `BadTooManySubscriptions`, or updates stall after initial connection.
- High memory or CPU utilization on older PLCs.

### Diagnostic Steps & Solutions
Some embedded PLCs have limited resources or incomplete implementations of the OPC-UA subscription specification.
- **Switch to Polling**: In your connector JSON, set:
  ```json
  "enableSubscriptions": false,
  "pollPeriodInMillis": 5000
  ```
  Polling mode queries tag values at fixed intervals, which is significantly more compatible across diverse PLC hardware.

---

## 5. Security & TLS Certificate Handshake Errors

### Symptoms
- Connector logs show: `BadSecurityChecksFailed`, `BadCertificateUntrusted`, or `BadCertificateHostNameInvalid`.

### Diagnostic Steps & Solutions
1. **Trusting Client Certificate in the PLC**:
   When using security policies like `Basic256Sha256`, the PLC will reject connections until you explicitly trust the gateway's certificate.
   - Connect once to trigger the initial rejection.
   - In your PLC's engineering tool (e.g., Siemens TIA Portal or Beckhoff TwinCAT), open the certificate management console.
   - Move the rejected certificate from the "Quarantine" / "Untrusted" list to "Trusted Certificates".
2. **Clock Synchronization**:
   OPC-UA security certificates enforce validity periods. If the system clock of the PLC or the host server drifts by more than a few minutes, certificate validation will fail. Ensure both host and PLC are synchronized to an NTP time source.

---

## Glossary of Terms

| Term | Definition |
| :--- | :--- |
| **OPC-UA** | *Open Platform Communications Unified Architecture*. An open, platform-independent industrial communication standard for secure data exchange between machines and software systems. |
| **Node** | The fundamental unit of information in an OPC-UA address space. Nodes can represent objects (e.g., a machine), variables (e.g., a sensor value), or methods. |
| **NodeId** | The unique identifier for a node within an OPC-UA server, consisting of a namespace index and an identifier (numeric, string, GUID, or opaque). |
| **Namespace** | A URI defining the scope of node names, preventing collisions between vendor-specific nodes and standard OPC-UA nodes. Mapped to an integer **Namespace Index** at runtime. |
| **Endpoint** | The network address and port where an OPC-UA server listens for connections (e.g., `opc.tcp://192.168.1.50:4840`). |
| **Device** | In ThingsBoard, an entity representing a physical or logical asset (e.g., a PLC, pump, or robot) that produces telemetry and holds attributes. |
| **Telemetry Key** | A named data point (e.g., `temperature`, `motorSpeed`) representing time-stamped metric values stored in ThingsBoard timeseries storage. |
| **Attribute** | Semi-static metadata associated with a device (e.g., `serialNumber`, `firmwareVersion`, `ipAddress`) stored as key-value pairs. |
| **Connector** | A gateway module responsible for bridging an industrial protocol (e.g., OPC-UA, Modbus, MQTT) into ThingsBoard telemetry events. |

---

## Support and Escalation

If you encounter an issue not addressed in this guide:
1. Enable debug logging by setting `"logLevel": "DEBUG"` in your connector JSON.
2. Collect container logs:
   ```bash
   docker compose logs --tail=200 tb-gateway > gateway-debug.log
   docker compose logs --tail=200 thingsboard > thingsboard-debug.log
   ```
3. Contact your platform operations or automation engineering team with the collected logs and PLC model details.

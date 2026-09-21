# 01 — Setup ThingsBoard Platform and Gateway

This guide covers deploying the ThingsBoard platform stack using Docker Compose, creating a Gateway entity in ThingsBoard, configuring credentials, and verifying that services are connected and healthy.

---

## Prerequisites

Before starting, ensure your host environment meets the following requirements:

- **Docker & Docker Compose**: Docker Engine 20.10+ and Docker Compose v2.0+ installed and running.
- **Port Availability**: Verify the following host ports are not currently occupied by other applications:
  - `8080` (ThingsBoard Web UI, mapped from container port `9090`)
  - `1883` (ThingsBoard MQTT Broker for gateway communication)
  - `7071` (ThingsBoard internal HTTP transport, mapped from container port `7070`)
- **Host Resource Allocation**: At least 4 GB of available RAM and 10 GB of free disk space.

You can verify port availability with:
```bash
sudo lsof -i :8080 -i :1883 -i :7071
```

---

## Step 1: Initialize Environment Configuration

Copy the example environment file to create your active `.env` file:

```bash
cp .env.example .env
```

The default `.env` contains:
```env
TB_GW_HOST=thingsboard
TB_GW_PORT=1883
TB_GW_ACCESS_TOKEN=replace-with-your-gateway-access-token
```

Leave this file open; you will populate `TB_GW_ACCESS_TOKEN` in Step 3.

---

## Step 2: Start the ThingsBoard Platform

Start the `thingsboard` platform service first so the web platform and database initialize:

```bash
docker compose up -d thingsboard
```

Follow the startup logs to ensure database migrations complete and the service is ready:

```bash
docker compose logs -f thingsboard
```

Once you see the application started message, the web interface is accessible at [http://localhost:8080](http://localhost:8080).

Default administrative credentials for ThingsBoard Community Edition:
- **System Administrator**: `sysadmin@thingsboard.org` / `sysadmin` (for platform-level settings and tenant management)
- **Tenant Administrator**: `tenant@thingsboard.org` / `tenant` (for managing devices, gateways, rules, and dashboards)

Log in using the Tenant Administrator credentials (`tenant@thingsboard.org` / `tenant`).

---

## Step 3: Create Gateway Entity & Retrieve Access Token

ThingsBoard IoT Gateway communicates with ThingsBoard over MQTT and authenticates using a Gateway device access token.

1. Navigate to **Entities** → **Gateways** in the left sidebar navigation.
2. Click the **+** icon (Add Gateway) in the top-right corner.
3. In the creation dialog:
   - **Name**: Enter a descriptive name, such as `OPCUA-Gateway`.
   - **Gateway**: Ensure the **Is Gateway** checkbox is enabled.
   - **Device Profile**: Select default `Gateway` profile.
4. Click **Add**.
5. Click on the newly created gateway from the list to open its details panel.
6. Under the **Details** tab, locate **Credentials**.
7. Copy the **Access Token** string (for example, `D4dzY7BsTyua7zkM6qeC`).
8. Open your `.env` file and replace the placeholder:
   ```env
   TB_GW_HOST=thingsboard
   TB_GW_PORT=1883
   TB_GW_ACCESS_TOKEN=<paste-copied-token-here>
   ```
9. Save the `.env` file.

---

## Step 4: Start ThingsBoard Gateway

With the access token saved, launch the gateway service:

```bash
docker compose up -d --build tb-gateway
```

Docker Compose launches the `tb-gateway` container attached to the shared internal network, resolving `thingsboard:1883`.

---

## Step 5: Verify Connectivity and Service Health

Verify container status:
```bash
docker compose ps
```
Both `thingsboard` and `tb-gateway` should display status `Up`.

Inspect gateway startup logs:
```bash
docker compose logs -f tb-gateway
```

Expected log highlights:
- Gateway process starts and connects to `thingsboard:1883`.
- Successful authentication line:
  ```text
  Connected to ThingsBoard with status: 0
  Gateway successfully connected and authenticated
  ```

Check Web UI status:
1. Return to the ThingsBoard UI at [http://localhost:8080](http://localhost:8080).
2. Navigate to **Entities** → **Gateways**.
3. Confirm that `OPCUA-Gateway` shows an **Active** / **Online** indicator.

---

## Persistence and Volume Management

The stack uses dedicated Docker named volumes:

| Volume Name | Target Path inside Container | Contents | Impact if Deleted |
| :--- | :--- | :--- | :--- |
| `tb-data` | `/var/lib/postgresql/data` | PostgreSQL database (tenants, devices, telemetry history, dashboards) | All telemetry, users, and device entities will be permanently lost. |
| `tb-gw-config` | `/thingsboard_gateway/config` | Gateway connectors configuration and settings | Gateway connector definitions and remote configuration state are reset. |
| `tb-gw-logs` | `/thingsboard_gateway/logs` | Diagnostic logs from gateway runtime and connectors | Historical logs deleted; no functional impact. |
| `tb-gw-extensions`| `/thingsboard_gateway/extensions` | Custom connectors and extension scripts | Any custom Python extensions added to the gateway are removed. |

---

## Official Images and Pinning

The stack utilizes official Docker Hub images:
- `thingsboard/tb-postgres:latest` — Official single-instance ThingsBoard distribution backed by PostgreSQL.
- `thingsboard/tb-gateway:latest` — Official ThingsBoard IoT Gateway distribution.

To pin specific releases for reproducible production deployments, specify release tags (e.g., `thingsboard/tb-postgres:3.8.1` and `thingsboard/tb-gateway:3.5.2`) in `docker-compose.yml`.

---

## Stopping and Teardown

To stop the services while preserving all data and configurations:
```bash
docker compose down
```

To restart the stack later:
```bash
docker compose up -d
```

To perform a complete wipe of the environment (including all historical telemetry and databases):
```bash
docker compose down -v
```
> [!CAUTION]
> The `-v` flag removes named volumes (`tb-data`, `tb-gw-*`). Use this only when resetting a development environment from scratch.

---

## Next Steps

Once ThingsBoard and ThingsBoard Gateway are running and active, proceed to [02 — Test Your Setup with a Simulated PLC](02-test-your-setup-with-a-simulated-plc.md) to validate the pipeline before connecting physical hardware.

"""
Simulates a PLC's OPC-UA server so you can validate your full ThingsBoard Gateway → ThingsBoard pipeline before connecting real hardware.

Creates a browsable address space:
    Root
     └── Objects
          └── Device1        (Object)
               ├── Temperature (Double, updates every 5s)
               └── Humidity    (Double, updates every 5s)

Requirements:
    pip install -r requirements.txt
    python3 fake_opcua_server.py

Server listens on: opc.tcp://0.0.0.0:4840/freeopcua/server/
"""

import asyncio
import logging
import random

from asyncua import Server, ua

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("fake_opcua_server")


async def main():
    server = Server()
    await server.init()

    # Endpoint the ThingsBoard Gateway (or any client) will connect to
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("Fake PLC Test Server")

    # No security, anonymous access - suitable for local validation
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    # Register our own namespace so our nodes don't clash with standard OPC-UA nodes
    uri = "http://example.org/fake-plc"
    idx = await server.register_namespace(uri)

    # Get the standard Objects folder
    objects = server.nodes.objects

    # Create an Object node representing our device
    device = await objects.add_object(idx, "Device1")

    # Create variables under that device object
    temperature_var = await device.add_variable(idx, "Temperature", 25.0, ua.VariantType.Double)
    humidity_var = await device.add_variable(idx, "Humidity", 50.0, ua.VariantType.Double)

    # Enable write access
    await temperature_var.set_writable()
    await humidity_var.set_writable()

    _logger.info("Starting simulated PLC server...")
    _logger.info("Namespace index: %s", idx)
    _logger.info("Temperature NodeId: %s", temperature_var.nodeid)
    _logger.info("Humidity NodeId: %s", humidity_var.nodeid)

    async with server:
        _logger.info("Server started. Endpoint: opc.tcp://0.0.0.0:4840/freeopcua/server/")
        while True:
            # Generate simulated sensor values
            new_temp = round(random.uniform(20.0, 30.0), 2)
            new_humidity = round(random.uniform(40.0, 60.0), 2)

            await temperature_var.write_value(new_temp)
            await humidity_var.write_value(new_humidity)

            _logger.info("Temperature=%s  Humidity=%s", new_temp, new_humidity)

            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())

# Poseidon WEP SDK

Python SDK for building Worker Execution Process (WEP) workflows on the Poseidon Subnet.

## Installation

```bash
pip install poseidon-wep-sdk
```

## Quick Start

```python
from poseidon_wep_sdk_pkg import WepServer, ServiceRegistry

# Register your service
registry = ServiceRegistry()
registry.register("my_service", my_service_handler)

# Start the WEP server
server = WepServer(registry=registry)
server.run()
```

## Documentation

For detailed documentation, see the [examples](https://github.com/PSDN-AI/wep-python-sdk/tree/main/examples) directory.

## License

MIT

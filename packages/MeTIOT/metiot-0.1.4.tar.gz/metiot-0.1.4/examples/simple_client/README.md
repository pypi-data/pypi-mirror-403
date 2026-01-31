# Quickstart: Simple Client

The `main.py` script in the `examples/simple_client/` folder is the simplest way to see the library in action. It performs the following handshake and monitoring flow:

## What this example demonstrates:

1. **Connection Management:** Establishing a link to a specific IP and Port.
2. **Device Identification:** Using `get_device_type()` to determine if the node is a `FISH_TANK` or a `FILTER_GUARDIAN`.
3. **Asynchronous Handlers:** Assigning callback functions (`on_data`, `on_warning`, `on_fatal`) so your main loop stays clean while the library handles the background communication.
4. **Protocol Interpretation:** Using the `device_protocol` handler to transform the data stream into readable Python dictionaries (e.g., Temperature or Flow rate).

## How to run it:

1. **Configure the IP:** Open `main.py` and update the `deviceIP` variable to match your hardware's address:
```py
deviceIP = "10.0.0.98" # Change this to your device IP
```
2. **Run the script:**
```bash
python3 main.py
```

## Expected Output:

When successful, you will see the connection status followed by a live stream of telemetry:
```plaintext
Connecting to device...
Connected! Device type: DeviceType.FISH_TANK
Received message from 506097522914230528 with header: NodeHeader.General.Data
Flow rate: 15.32 L/m
Flow rate: 10.90 L/m
Flow rate: 6.41 L/m
```
import MeTIOT
import time

def fishtank_update_handler(device, header, data):
    print(f"Received message from {device.get_unique_id()} with header: {header}")

    match header:
        case MeTIOT.NodeHeader.General.Data:
            deviceProtocol = device.get_protocol_handler()
            telemetry = deviceProtocol.interpret_data(data)
            print(f"Temperature: {telemetry['Temperature_C']} C")

        case MeTIOT.NodeHeader.MalformedPacketNotification:
            print("Device reported a communication error.")

        case _:
            print(f"Unhandled header occured: {header}")

def filterguardian_update_handler(device, header, data):
    print(f"Received message from {device.get_unique_id()} with header: {header}")

    match header:
        case MeTIOT.NodeHeader.General.Data:
            deviceProtocol = device.get_protocol_handler()
            telemetry = deviceProtocol.interpret_data(data)
            print(f"Flow rate: {telemetry['Flowrate_LM']} L/m")

        case MeTIOT.NodeHeader.MalformedPacketNotification:
            print("Device reported a communication error.")

        case _:
            print(f"Unhandled header occured: {header}")

def warning_handler(device, msg):
    print(f"Device {device.get_unique_id()} has non-fatal warning: {msg}")

def error_handler(device, msg):
    print(f"Device {device.get_unique_id()} has fatal error: {msg}")


deviceIP = "10.0.0.98" # Change this to your device IP
devicePort = 12345


device = MeTIOT.DeviceClient(deviceIP, devicePort)

print("Connecting to device...")
device.connect()

devType = device.get_device_type()
print(f"Connected! Device type: {devType}. ID: {device.get_unique_id()}")

if (devType == MeTIOT.DeviceType.FISH_TANK):
    device.assign_handlers(on_data=fishtank_update_handler, on_warning=warning_handler, on_fatal=error_handler)
elif (devType == MeTIOT.DeviceType.FILTER_GUARDIAN):
    device.assign_handlers(on_data=filterguardian_update_handler, on_warning=warning_handler, on_fatal=error_handler)

while (True):
    time.sleep(5)
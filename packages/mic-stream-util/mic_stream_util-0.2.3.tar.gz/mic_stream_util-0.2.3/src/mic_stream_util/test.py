import sounddevice as sd

print(sd.query_hostapis())  # Look for names like 'PulseAudio' or 'PipeWire'
# dev = sd.query_devices(sd.default.device if sd.default.device is not None else None)
# print(dev)


print("=== Available Host APIs ===")
hostapis = sd.query_hostapis()
for i, api in enumerate(hostapis):
    print(f"{i}: {api['name']}")

print("\n=== All Audio Devices ===")
devices = sd.query_devices()
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']} (hostapi: {dev['hostapi']})")

print("\n=== Pipewire Device Details ===")
# Find the pipewire device
pipewire_devices = [dev for dev in devices if "pipewire" in dev["name"].lower()]
for dev in pipewire_devices:
    print(f"Device {dev['index']}: {dev}")

print("\n=== Using Pipewire Device Directly ===")
if pipewire_devices:
    pipewire_device = pipewire_devices[0]
    print(f"Using Pipewire device: {pipewire_device['name']}")
    print(f"Device index: {pipewire_device['index']}")
    print(f"Max input channels: {pipewire_device['max_input_channels']}")
    print(f"Max output channels: {pipewire_device['max_output_channels']}")
    print(f"Default sample rate: {pipewire_device['default_samplerate']}")
else:
    print("No Pipewire device found")

# Example of how to use the pipewire device
print("\n=== Example Usage ===")
if pipewire_devices:
    pipewire_idx = pipewire_devices[0]["index"]
    print(f"To use Pipewire device, specify device={pipewire_idx} in your sounddevice calls")
    print("Example: sd.play(data, samplerate=44100, device=pipewire_idx)")
else:
    print("Cannot demonstrate usage - no Pipewire device available")

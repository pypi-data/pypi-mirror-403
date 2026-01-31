"""
Comprehensive CCTV system test script.
Tests SSM functionality, system components, LED control, GPIO operations, and button handling.
"""
import pprint
import threading
import logging
from pathlib import Path
from time import sleep
from ekfsm.system import System

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Initialize system
config = Path(__file__).parent / "cctv.yaml"
system = System(config, abort=True)

print("=" * 60)
print("=== CCTV Comprehensive Test Script ===")
print("=" * 60)

# ============================================================================
# SECTION 1: System and Component Tests
# ============================================================================
print("\n### SECTION 1: System and Component Tests ###\n")

print("System slots:")
pprint.pprint(system.slots)

system.print()

# Test different ways to access CPU
cpu = system["CPU"]
cpuB = system.cpu
cpuC = system[0]

assert cpu == cpuB == cpuC
print("\nCPU access methods verified (all point to same object)")

cpu.print()
print(f"\nProbing CPU: {cpu.probe()}")
print(f"Inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}")

# Get SMC and i4edge interface
smc = system.smc
smc.print()

i4e = smc.i4e
print(f"\ni4edge interface: {i4e}")

# ============================================================================
# SECTION 2: SSM (System State Manager) Tests
# ============================================================================
print("\n### SECTION 2: SSM (System State Manager) Tests ###\n")

ssm = i4e.ssm
print(f"SSM Device: {ssm}")
print(f"Service Address: {ssm.service_addr}\n")

# Test 1: Get SSM description
print("Test 1: Getting SSM description...")
try:
    description = ssm.describe()
    print(f"  Description: {description}")
except Exception as e:
    print(f"  Error: {e}")

# Test 2: Get current system state
print("\nTest 2: Getting current system state...")
try:
    state = ssm.state()
    print(f"  Current state: {state}")
except Exception as e:
    print(f"  Error: {e}")

# Test 3: Turn system ON
print("\nTest 3: Turning system ON...")
try:
    ssm.on()
    print("  System turned ON successfully")
    sleep(1)
    state = ssm.state()
    print(f"  New state: {state}")
except Exception as e:
    print(f"  Error: {e}")

# Test 4: SSM watchdog kicks
print("\nTest 4: Kicking SSM watchdog 5 times...")
for i in range(5):
    try:
        ssm.kick()
        print(f"  SSM Kick {i+1}/5 successful")
        sleep(0.5)
    except Exception as e:
        print(f"  SSM Kick {i+1}/5 failed: {e}")
        break

# Test 5: Set and resolve error state
print("\nTest 5: Testing error state...")
try:
    ssm.error("Test error message")
    print("  Error state set successfully")
    sleep(1)
    state = ssm.state()
    print(f"  State after error: {state}")
    ssm.resolve("Test error resolved")
    print("  Error resolved successfully")
    sleep(1)
    state = ssm.state()
    print(f"  State after resolve: {state}")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================================
# SECTION 3: LED Control Tests
# ============================================================================
print("\n### SECTION 3: LED Control Tests ###\n")

print("Setting and verifying LED states...")
try:
    # LED 2 test
    i4e.leds.led2.set(0, True)
    led2 = i4e.leds.led2.get()
    assert led2 == (0, True)
    print(f"  LED2: brightness=0, on=True -> {led2} ✓")

    # LED 5 test
    i4e.leds.led5.set(3, True)
    led5 = i4e.leds.led5.get()
    assert led5 == (3, True)
    print(f"  LED5: brightness=3, on=True -> {led5} ✓")

    # LED 3 test
    i4e.leds.led3.set(5, False)
    led3 = i4e.leds.led3.get()
    assert led3 == (5, False)
    print(f"  LED3: brightness=5, on=False -> {led3} ✓")
    print("\nAll LED tests passed!")
except Exception as e:
    print(f"  LED test error: {e}")

# ============================================================================
# SECTION 4: GPIO and Button Tests
# ============================================================================
print("\n### SECTION 4: GPIO and Button Tests ###\n")

button_array = i4e.gpios.buttons
pw_toggle = i4e.gpios.power
redriver_toggle = i4e.gpios.redriver

eject = button_array.eject

# Set up button handler
eject.handler = lambda: print("  [BUTTON EVENT] Eject button pressed!")

# Start button monitoring thread
print("Starting button monitoring thread...")
stop_event = threading.Event()
button_thread = threading.Thread(target=button_array.read, args=(stop_event,))
button_thread.start()
print("  Button thread started (press eject button to test)\n")

# ============================================================================
# SECTION 5: Comprehensive Loop Test
# ============================================================================
print("### SECTION 5: Comprehensive Loop Test ###\n")
print("Running 30 iterations of LED and GPIO tests...")
for i in range(30):
    try:
        # LED cycling tests
        i4e.leds.led1.set(1, True)
        led1 = i4e.leds.led1.get()
        assert led1 == (1, True)
        i4e.leds.led4.set(2, True)
        led4 = i4e.leds.led4.get()
        assert led4 == (2, True)
        i4e.leds.led6.set(4, False)
        led6 = i4e.leds.led6.get()
        assert led6 == (4, False)

        # GPIO toggle tests
        pw_toggle.off()
        pw_toggle.on()
        redriver_toggle.off()
        redriver_toggle.on()

        if (i + 1) % 10 == 0:
            print(f"  Iteration {i+1}/30 complete")

    except Exception as e:
        print(f"  Error in iteration {i+1}: {e}")
        break

print("\nLoop test complete!")

# Stop button monitoring thread
print("\nStopping button monitoring thread...")
stop_event.set()
button_thread.join()
print("  Button thread stopped")

# ============================================================================
# Test Summary
# ============================================================================
print("\n" + "=" * 60)
print("=== All Tests Complete ===")
print("=" * 60)
print("\nNote: Shutdown and fatal tests are commented out to avoid system disruption.")
print("Uncomment them if you need to test those functions.\n")

# Uncomment to test shutdown:
# print("\nTest: Testing shutdown...")
# ssm.shutdown()

# Uncomment to test fatal error:
# print("\nTest: Testing fatal error...")
# ssm.fatal("Test fatal error")

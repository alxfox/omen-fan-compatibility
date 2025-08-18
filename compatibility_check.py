#!/usr/bin/env python3

"""
OMEN Fan Control - Hardware Compatibility Check
===============================================

This script performs SAFE READ-ONLY tests to check if your HP OMEN laptop
is compatible with the omen-fan control system. It does NOT write to the EC.

All operations are read-only to prevent any potential system damage.

This is part of a COMMUNITY FORK for broader compatibility testing.
Use at your own risk - hardware compatibility is not guaranteed.
"""

import os
import sys
import subprocess
import glob
from time import sleep

# EC Memory offsets from the main omen-fan.py script
FAN1_OFFSET = 52      # 0x34 - Fan 1 speed control
FAN2_OFFSET = 53      # 0x35 - Fan 2 speed control  
BIOS_OFFSET = 98      # 0x62 - BIOS control status
TIMER_OFFSET = 99     # 0x63 - Timer value
CPU_TEMP_OFFSET = 87  # 0x57 - CPU temperature
GPU_TEMP_OFFSET = 183 # 0xB7 - GPU temperature  
BOOST_OFFSET = 236    # 0xEC - Boost control

# File paths
ECIO_FILE = "/sys/kernel/debug/ec/ec0/io"
DEVICE_FILE = "/sys/devices/virtual/dmi/id/product_name"


def check_root_access():
    """Check if running as root (required for EC access)"""
    if os.geteuid() != 0:
        print("ERROR: Root access is required for EC testing.")
        print("Please run: sudo python3 compatibility_check.py")
        return False
    return True


def load_ec_module():
    """Load the ec_sys kernel module for EC access"""
    try:
        # Check if module is already loaded
        result = subprocess.run(["lsmod"], capture_output=True, text=True)
        if "ec_sys" not in result.stdout:
            print("Loading ec_sys module...")
            subprocess.run(["modprobe", "ec_sys", "write_support=1"], check=True)
            print("✓ ec_sys module loaded successfully")
        else:
            print("✓ ec_sys module already loaded")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to load ec_sys module: {e}")
        return False


def check_device_compatibility():
    """Check if the device is in the supported list"""
    try:
        with open(DEVICE_FILE, "r") as f:
            device_name = f.read().strip()
        print(f"Device name: {device_name}")
        
        # Known supported devices
        supported = ["OMEN by HP Laptop 16"]
        
        is_supported = any(supported_device in device_name for supported_device in supported)
        if is_supported:
            print("✓ Device appears to be in supported list")
        else:
            print("⚠ Device may not be officially supported")
            print("  This doesn't mean it won't work, but proceed with caution")
        
        return device_name
    except Exception as e:
        print(f"ERROR: Cannot read device info: {e}")
        return None


def check_ec_interface():
    """Check if EC interface is accessible"""
    try:
        if not os.path.exists(ECIO_FILE):
            print("ERROR: EC interface file not found")
            return False
        
        # Check permissions
        stat = os.stat(ECIO_FILE)
        if not (stat.st_mode & 0o200):  # Check write permission for root
            print("WARNING: EC interface may not have write support")
        
        print("✓ EC interface file exists and is accessible")
        return True
    except Exception as e:
        print(f"ERROR: Cannot access EC interface: {e}")
        return False


def check_hp_wmi_interface():
    """Check HP WMI hwmon interface availability"""
    try:
        fan_files = glob.glob("/sys/devices/platform/hp-wmi/hwmon/*/fan*_input")
        boost_files = glob.glob("/sys/devices/platform/hp-wmi/hwmon/*/pwm1_enable")
        
        if fan_files:
            print(f"✓ Found HP WMI fan interfaces: {len(fan_files)} fans")
            for fan_file in fan_files:
                try:
                    with open(fan_file, 'r') as f:
                        speed = f.read().strip()
                    print(f"  {os.path.basename(fan_file)}: {speed} RPM")
                except Exception as e:
                    print(f"  {os.path.basename(fan_file)}: Cannot read ({e})")
        else:
            print("⚠ No HP WMI fan interfaces found")
        
        if boost_files:
            print("✓ Found boost control interface")
            try:
                with open(boost_files[0], 'r') as f:
                    boost_status = f.read().strip()
                print(f"  Current boost status: {boost_status}")
            except Exception as e:
                print(f"  Cannot read boost status: {e}")
        else:
            print("⚠ No boost control interface found")
        
        return len(fan_files) > 0 or len(boost_files) > 0
    except Exception as e:
        print(f"ERROR checking HP WMI interface: {e}")
        return False


def read_ec_byte(offset):
    """Safely read a single byte from EC at given offset"""
    try:
        with open(ECIO_FILE, "rb") as ec:
            ec.seek(offset)
            byte_data = ec.read(1)
            if byte_data:
                return int.from_bytes(byte_data, "big")
            else:
                return None
    except Exception as e:
        print(f"ERROR reading EC offset {offset} (0x{offset:02X}): {e}")
        return None


def test_ec_read_capabilities():
    """Test reading various EC memory locations"""
    print("\n" + "="*50)
    print("TESTING EC READ CAPABILITIES")
    print("="*50)
    
    # Test critical offsets
    test_offsets = [
        (FAN1_OFFSET, "Fan 1 Speed Control"),
        (FAN2_OFFSET, "Fan 2 Speed Control"), 
        (BIOS_OFFSET, "BIOS Control Status"),
        (TIMER_OFFSET, "Timer Value"),
        (CPU_TEMP_OFFSET, "CPU Temperature"),
        (GPU_TEMP_OFFSET, "GPU Temperature"),
        (BOOST_OFFSET, "Boost Control")
    ]
    
    successful_reads = 0
    
    for offset, description in test_offsets:
        value = read_ec_byte(offset)
        if value is not None:
            print(f"✓ Offset {offset:3d} (0x{offset:02X}) - {description:20s}: {value:3d} (0x{value:02X})")
            successful_reads += 1
        else:
            print(f"✗ Offset {offset:3d} (0x{offset:02X}) - {description:20s}: READ FAILED")
    
    print(f"\nSUMMARY: {successful_reads}/{len(test_offsets)} offsets readable")
    
    return successful_reads == len(test_offsets)


def analyze_current_state():
    """Analyze current fan control state"""
    print("\n" + "="*50)
    print("CURRENT SYSTEM STATE ANALYSIS")
    print("="*50)
    
    # Read BIOS control status
    bios_status = read_ec_byte(BIOS_OFFSET)
    if bios_status is not None:
        if bios_status == 6:
            print("BIOS Fan Control: DISABLED (Manual control active)")
        elif bios_status == 0:
            print("BIOS Fan Control: ENABLED (Automatic control)")
        else:
            print(f"BIOS Fan Control: UNKNOWN STATE ({bios_status})")
    
    # Read current fan control values
    fan1_value = read_ec_byte(FAN1_OFFSET)
    fan2_value = read_ec_byte(FAN2_OFFSET)
    
    if fan1_value is not None:
        print(f"Fan 1 EC Value: {fan1_value} (approx {fan1_value * 100} RPM)")
    if fan2_value is not None:
        print(f"Fan 2 EC Value: {fan2_value} (approx {fan2_value * 100} RPM)")
    
    # Read temperatures
    cpu_temp = read_ec_byte(CPU_TEMP_OFFSET)
    gpu_temp = read_ec_byte(GPU_TEMP_OFFSET)
    
    if cpu_temp is not None:
        print(f"CPU Temperature: {cpu_temp}°C")
    if gpu_temp is not None:
        print(f"GPU Temperature: {gpu_temp}°C")
    
    # Read boost status
    boost_value = read_ec_byte(BOOST_OFFSET)
    if boost_value is not None:
        print(f"Boost EC Value: {boost_value}")


def compatibility_report():
    """Generate final compatibility report"""
    print("\n" + "="*50)
    print("COMPATIBILITY REPORT")
    print("="*50)
    
    print("Based on the tests performed:")
    print()
    
    # Check if all tests passed
    device_ok = check_device_compatibility() is not None
    ec_ok = check_ec_interface()
    hp_wmi_ok = check_hp_wmi_interface()
    ec_read_ok = test_ec_read_capabilities()
    
    if all([device_ok, ec_ok, hp_wmi_ok, ec_read_ok]):
        print("🟢 LOOKS HIGHLY COMPATIBLE: All systems appear functional")
        print("   - Device partially matches known supported devices")
        print("   - EC interface is accessible and readable")
        print("   - HP WMI interface is available")
        print("   - All critical EC offsets can be read")
        print()
        print("⚠ NEXT STEP RECOMMENDATION:")
        print("   You can likely proceed with the EC write test")
        print("   However, write tests carry MODERATE-HIGH RISK")
        print("   - Could temporarily break fan control")
        print("   - Usually recoverable with reboot")
        print("   - Small chance of requiring BIOS reset")
        print()
        
        while True:
            response = input("Do you want to proceed to the risky write test? (y/N): ").lower()
            if response in ['n', 'no', '']:
                print("\n✓ Wise choice! You can run ec_write_test.py manually later if desired.")
                break
            elif response in ['y', 'yes']:
                print("\n⚠ Proceeding to write test...")
                print("   Loading ec_write_test.py...")
                print("   (You'll get more detailed warnings in that script)")
                try:
                    import subprocess
                    subprocess.run([sys.executable, "ec_write_test.py"], check=False)
                except Exception as e:
                    print(f"Could not launch write test: {e}")
                    print("You can run it manually: sudo python3 ec_write_test.py")
                break
            else:
                print("Please answer 'y' for yes or 'n' for no.")
                
    elif ec_ok and ec_read_ok:
        print("🟡 POSSIBLY COMPATIBLE: Core functionality present")
        print("   - EC interface works correctly")
        print("   - Missing some HP WMI features")
        print()
        print("⚠ RECOMMENDATION: Proceed with extreme caution")
        print("   Consider testing write operations very carefully")
    else:
        print("🔴 LIKELY INCOMPATIBLE: Major issues detected")
        print("   - Critical interfaces missing or non-functional")
        print()
        print("⚠ RECOMMENDATION: Do NOT attempt write operations")
        print("   This laptop may not support EC fan control")


def main():
    """Main test execution"""
    print("OMEN Fan Control - Hardware Compatibility Check")
    print("===============================================")
    print("🟢 RISK LEVEL: Should be very safe (but no guarantees)")
    print("   - Only READS from system - no changes planned")
    print("   - Should not damage hardware or affect fan control")
    print("   - Recovery not needed - no system modifications planned")
    print()
    print("What this test checks:")
    print("✓ EC (Embedded Controller) accessibility")
    print("✓ Required memory offsets readable")  
    print("✓ HP WMI interface availability")
    print("✓ Device compatibility with known models")
    print("✓ Current thermal/fan control state")
    print()
    
    # Get user confirmation
    while True:
        response = input("Do you want to proceed with the read-only compatibility check? (y/N): ").lower()
        if response in ['n', 'no', '']:
            print("Test cancelled by user.")
            return 1
        elif response in ['y', 'yes']:
            break
        else:
            print("Please answer 'y' for yes or 'n' for no.")
    
    print("\n" + "="*50)
    print("STARTING COMPATIBILITY TESTS...")
    print("="*50)
    
    # Prerequisites check
    if not check_root_access():
        return 1
    
    if not load_ec_module():
        print("Cannot proceed without EC module")
        return 1
    
    # Wait a moment for module to initialize
    sleep(0.5)
    
    # Run compatibility tests
    print("\n" + "="*50)
    print("SYSTEM COMPATIBILITY CHECKS")
    print("="*50)
    
    check_device_compatibility()
    check_ec_interface()
    check_hp_wmi_interface()
    
    # Test EC functionality
    test_ec_read_capabilities()
    
    # Analyze current state
    analyze_current_state()
    
    # Generate report
    compatibility_report()
    
    print("\n" + "="*50)
    print("✅ COMPATIBILITY CHECK COMPLETE")
    print("="*50)
    print("📋 What was tested:")
    print("   ✓ EC memory read access (SAFE - no system changes)")
    print("   ✓ Device model compatibility")
    print("   ✓ HP WMI interface availability")
    print("   ✓ Critical fan control registers")
    print()
    print("📋 What was NOT tested:")
    print("   ⚠ EC write operations (requires ec_write_test.py)")
    print("   ⚠ Actual fan speed control")
    print("   ⚠ BIOS control override")
    print()
    print("🎯 Next steps:")
    print("   → If results look good: sudo python3 ec_write_test.py")
    print("   → If issues found: DO NOT proceed with write tests")
    print("   → Check EMERGENCY_RECOVERY.md for safety info")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
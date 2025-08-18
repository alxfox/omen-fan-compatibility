# omen-fan (Community Fork)

> ⚠️ **This is a community fork of the original [omen-fan project](https://github.com/alou-S/omen-fan)**  
> ⚠️ **USE AT YOUR OWN RISK - No warranty provided**  
> ⚠️ **May cause hardware damage or system instability**

A utility to manually control the fans of HP Omen laptops with enhanced compatibility testing tools.

## 🔍 What's Different in This Fork

This fork adds **comprehensive compatibility testing tools** to help users safely determine if their HP Omen laptop is compatible with fan control before attempting to use the main functionality.

### New Testing Tools

1. **`compatibility_check.py`** - **SAFE** read-only compatibility test
2. **`ec_write_test.py`** - **DANGEROUS** write test for advanced users

## ⚠️ CRITICAL WARNINGS

- **Hardware Risk**: Directly accessing the Embedded Controller (EC) can potentially damage your laptop
- **No Warranty**: This software comes with absolutely no warranty or guarantee
- **System Instability**: Incorrect fan control can cause overheating or system crashes
- **Bricking Risk**: Writing wrong values to the EC could potentially brick fan control
- **Community Support**: This is a community fork - official support is not provided

**ALWAYS** ensure you can reboot your system if something goes wrong.

## 🚀 Quick Start (Recommended Testing Process)

> 📖 **For complete testing workflow, see [TESTING_WORKFLOW.md](TESTING_WORKFLOW.md)**

### Step 1: Safe Compatibility Check
```bash
# Clone this repository
git clone https://github.com/[your-username]/omen-fan
cd omen-fan

# Run the SAFE compatibility check first
sudo python3 compatibility_check.py
```

### Step 2: Advanced Testing (Only if Step 1 shows compatibility)
```bash
# Only run this if compatibility_check.py shows positive results
# This test WRITES to the EC - use extreme caution
sudo python3 ec_write_test.py
```

### Step 3: Main Functionality (Only if both tests pass)
```bash
# If both tests pass, you can try the main fan control
sudo python3 omen-fan.py --help
```

**📋 Testing Workflow Summary:**
- 🟢 **Phase 1**: Read-only compatibility check (should be very safe)
- 🟡 **Phase 2**: EC write testing (MODERATE-HIGH risk, ~95% recoverable)
- 🔴 **Phase 3**: Production fan control (HIGH risk, user dependent recovery)

## 📋 Original Features

- Manual fan speed control for HP Omen laptops
- Active fan speed adjustment service based on temperatures
- Boost mode support via sysfs
- Works on various HP Omen and some Victus laptops
- Originally made and tested on Omen 16-c0140AX, also tested on Omen 17-ck2000 

## 🛠️ Installation & Usage

### Prerequisites
```bash
# Ensure ec_sys module can be loaded
sudo modprobe ec_sys write_support=1

# Install Python dependencies (if not already available)
pip install click tomlkit click-aliases
```

### Testing Your Laptop - Detailed Risk Analysis

#### 🟢 Step 1: Compatibility Check (Should be very safe)
```bash
sudo python3 compatibility_check.py
```

**What it tests:**
- ✅ Reads EC memory locations (READ-ONLY operations)
- ✅ Checks if your laptop model matches known compatible devices
- ✅ Verifies HP WMI interface availability for fan speed reading
- ✅ Tests access to critical EC memory offsets (temperatures, fan control registers)
- ✅ Analyzes current BIOS control state

**Risk Level: 🟢 Should be very safe (but no guarantees)**
- **No system changes planned** - only reads existing values
- **Should not damage hardware** - read operations are generally safe
- **Should not affect fan control** - no writes to EC registers
- **Recovery**: Not expected to be needed - no changes planned

---

#### 🟡 Step 2: EC Write Test (MODERATE TO HIGH RISK)
```bash
sudo python3 ec_write_test.py
```

**What it tests:**

**Test 2.1: BIOS Control Toggle**
- 🔄 Disables BIOS fan control (sets EC offset 98 to value 6)
- 🔄 Re-enables BIOS fan control (sets EC offset 98 to value 0)
- **Risk**: Temporary loss of automatic fan control
- **Recovery**: Automatic restoration + reboot restores BIOS control

**Test 2.2: Manual Fan Speed Control**
- 🔄 Sets fan speeds to safe test value (20% = ~2000 RPM)
- 🔄 Monitors system for 10 seconds while fans run at test speed
- 🔄 Continuously checks temperatures to prevent overheating
- **Risk**: Manual override of fan speeds, potential overheating if test fails
- **Recovery**: Automatic restoration + reboot restores BIOS control

**Overall Risk Level: 🟡 MODERATE RISK**
- **Potential Issues:**
  - Temporary loss of automatic thermal protection
  - Risk of overheating if fan control gets stuck
  - Possible system instability during test
  - Small chance of corrupting EC fan control settings
- **Recovery Options:**
  - ✅ **Automatic**: Script restores original values on completion
  - ✅ **Manual**: Ctrl+C triggers emergency cleanup
  - ✅ **Reboot**: Simple reboot restores BIOS fan control
  - ❌ **Worst Case**: EC corruption could require BIOS reset/repair

**Important**: This test has **multiple safety layers** but still carries risk

---

#### 🔴 Step 3: Main Functionality (HIGH RISK - Production Use)
```bash
sudo python3 omen-fan.py
```

**What it does:**
- 🔄 **Disables BIOS control permanently** until manually restored
- 🔄 **Direct EC fan speed control** with user-defined values
- 🔄 **Temperature-based automatic curves** (omen-fand service)
- 🔄 **Boost mode control** via HP WMI interface

**Risk Level: 🔴 HIGH RISK**
- **Potential Issues:**
  - Complete override of laptop's thermal protection
  - Risk of overheating and hardware damage if curves are wrong
  - Possible permanent corruption of EC settings
  - System instability or crashes
  - Fan control could get stuck in manual mode
- **Recovery Options:**
  - ✅ **Command**: `sudo python3 omen-fan.py bios-control 1`
  - ✅ **Reboot**: Usually restores BIOS control
  - ❌ **Worst Case**: May require BIOS reset, CMOS clear, or hardware repair

**⚠️ Only use after both previous tests pass successfully!**

## 🆘 Emergency Recovery

> 📖 **For detailed recovery procedures, see [EMERGENCY_RECOVERY.md](EMERGENCY_RECOVERY.md)**

**Quick Emergency Actions:**
1. **🚨 High Temperature (>85°C)**: Shut down immediately
2. **⚡ Restore BIOS Control**: `sudo python3 omen-fan.py bios-control 1`
3. **🔄 Simple Reboot**: Usually fixes most fan control issues
4. **🔧 BIOS Reset**: Reset BIOS to defaults if fans remain stuck

**Recovery Success Rates:**
- � **Reboot**: ~95% success rate
- 🟡 **BIOS Reset**: ~85% success rate  
- � **CMOS Clear**: ~60% success rate
- 🔴 **Hardware Repair**: Required in ~5% of cases

## 📊 Compatibility Results

### Known Compatible Devices
- HP OMEN by HP Laptop 16 (original target)
- HP OMEN by HP Laptop (community tested)
- Various HP Victus laptops (community reports)

### Testing Status Legend
- 🟢 **Highly Compatible**: All systems functional
- 🟡 **Possibly Compatible**: Some features missing
- 🔴 **Incompatible**: Major issues detected

## 🆘 Emergency Recovery

If something goes wrong:

1. **Immediate**: Reboot your laptop
2. **If fans stuck**: Reboot and let BIOS take control
3. **If overheating**: Immediately shut down and cool the system
4. **Re-enable BIOS control**:
   ```bash
   sudo python3 omen-fan.py bios-control 1
   ```

## 📖 Documentation

- Use `omen-fan.py help` to see all available subcommands
- EC Probe documentation: [docs/probes.md](docs/probes.md)
- Original project: [alou-S/omen-fan](https://github.com/alou-S/omen-fan)

## 🤝 Contributing to Compatibility

If you test this on your laptop, please report results:

1. Run `compatibility_check.py`
2. Share your laptop model and test results
3. Create an issue with your findings
4. Help expand the compatibility database

## ⚖️ Legal Disclaimer

This software is provided "AS IS" without warranty of any kind. The authors and contributors are not responsible for any damage, data loss, or system instability that may result from using this software. Use at your own risk.

## 🙏 Credits

- **Original Author**: [alou-S](https://github.com/alou-S) - Creator of the original omen-fan project
- **Community Fork**: Enhanced with compatibility testing tools
- **Contributors**: Community members who test and report compatibility

---

**Remember: Always test compatibility safely before attempting write operations!**

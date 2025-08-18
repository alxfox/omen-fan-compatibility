#!/bin/bash

# OMEN Fan Control - Automated Compatibility Testing
# ===================================================
# This script runs the compatibility tests in the correct order
# with proper safety checks and user guidance.

set -e  # Exit on any error

echo "================================================="
echo "OMEN Fan Control - Compatibility Testing Suite"
echo "================================================="
echo ""
echo "⚠️  This is a community fork - use at your own risk"
echo ""
echo "📋 TESTING PROCESS:"
echo ""
echo "🟢 Stage 1: Read-only compatibility check"
echo "   → Should be very safe (but no guarantees)"
echo "   → Tests EC access and device compatibility"
echo ""
echo "🟡 Stage 2: EC write test (optional)"
echo "   → Higher risk but usually recoverable"
echo "   → Tests actual fan control functionality" 
echo "   → Reboot fixes most issues"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Error: This script must be run as root"
   echo "   Please run: sudo ./test_compatibility.sh"
   exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if required files exist
if [[ ! -f "compatibility_check.py" ]]; then
    echo "❌ Error: compatibility_check.py not found"
    exit 1
fi

if [[ ! -f "ec_write_test.py" ]]; then
    echo "❌ Error: ec_write_test.py not found"
    exit 1
fi

echo "🔍 Running compatibility check..."
echo "   → Testing EC read access"
echo "   → Should be safe (no system changes)"
echo ""

# Run the safe compatibility check
if python3 compatibility_check.py; then
    echo ""
    echo "✅ Compatibility check completed!"
    echo ""
    
    # Ask if user wants to proceed to write test
    while true; do
        read -p "🤔 Do you want to proceed to the RISKY write test? (y/N): " yn
        case $yn in
            [Yy]* ) 
                echo ""
                echo "⚠️  FINAL WARNING - EC WRITE TEST:"
                echo ""
                echo "   What will happen:"
                echo "   1. Temporarily disable BIOS fan control"
                echo "   2. Test manual fan speed setting (20% speed)"
                echo "   3. Monitor temperatures for 10 seconds"
                echo "   4. Restore original settings automatically"
                echo ""
                echo "   Risks:"
                echo "   🟡 Temporary loss of automatic thermal protection"
                echo "   🟡 Possible system instability during test"
                echo "   🟠 Small chance of EC corruption requiring BIOS reset"
                echo "   🔴 Very small chance of permanent fan control damage"
                echo ""
                echo "   Recovery options:"
                echo "   ✅ Automatic restoration (built-in)"
                echo "   ✅ Reboot (usually fixes any issues)"
                echo "   ✅ BIOS reset (if fans get stuck)"
                echo "   ❌ Hardware repair (worst case scenario)"
                echo ""
                
                while true; do
                    read -p "Still want to proceed? Type 'I UNDERSTAND THE RISKS' to continue: " confirm
                    case $confirm in
                        "I UNDERSTAND THE RISKS" )
                            echo ""
                            echo "🧪 Step 2: Running DANGEROUS write test..."
                            echo "   → Testing BIOS control toggle"
                            echo "   → Testing manual fan speed control"
                            echo "   → Monitoring temperatures continuously"
                            echo "   → Risk Level: 🟡 MODERATE-HIGH"
                            echo ""
                            
                            if python3 ec_write_test.py; then
                                echo ""
                                echo "🎉 SUCCESS: Your laptop appears to be compatible!"
                                echo "   You can now try using the main omen-fan.py script"
                                echo ""
                                echo "📚 Next steps:"
                                echo "   sudo python3 omen-fan.py --help"
                                echo "   sudo python3 omen-fan.py info"
                            else
                                echo ""
                                echo "❌ Write test failed - your laptop may not be compatible"
                                echo "   Do NOT use the main omen-fan.py script"
                            fi
                            break;;
                        * ) 
                            echo "❌ Test cancelled - write test skipped"
                            echo "   Your laptop may still be compatible, but not verified"
                            break;;
                    esac
                done
                break;;
            [Nn]* | "" ) 
                echo "⚠️  Write test skipped"
                echo "   Your laptop may be compatible based on the read test,"
                echo "   but write functionality is not verified."
                break;;
            * ) echo "Please answer y or n";;
        esac
    done
else
    echo ""
    echo "❌ Compatibility check failed"
    echo "   Your laptop is likely NOT compatible with omen-fan"
    echo "   Do NOT proceed with write tests or main functionality"
    exit 1
fi

echo ""
echo "================================================="
echo "Testing complete!"
echo "================================================="

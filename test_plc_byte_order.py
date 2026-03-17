#!/usr/bin/env python3
"""
Test Script for Modbus Byte Order Investigation

Run this with your actual PLC values to determine correct byte order settings.

Usage:
1. Edit TEST_INT16_* and TEST_STRING_* values below
2. Run: python test_plc_byte_order.py
3. Share output in issue report
"""

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from array import array

# =============================================================================
# EDIT THESE WITH YOUR ACTUAL PLC DATA
# =============================================================================

# Read a known INT16 from your PLC and enter:
TEST_INT16_REGISTER = 0x0064  # Raw register value (hex)
TEST_INT16_EXPECTED = 100     # Expected decimal value

# Read string registers from your PLC and enter:
TEST_STRING_REGISTERS = [0x4554, 0x5354]  # Raw register values for known string
TEST_STRING_EXPECTED = "TEST"              # Expected string content

# =============================================================================
# END CONFIG - DO NOT EDIT BELOW
# =============================================================================

def swap_bytes_in_words(raw_bytes):
    handle = array("H", raw_bytes)
    handle.byteswap()
    return handle.tobytes()

print("=" * 70)
print("PLC BYTE ORDER TEST")
print("=" * 70)

# INT16 test
print(f"\nINT16 Register: 0x{TEST_INT16_REGISTER:04X} (expecting {TEST_INT16_EXPECTED})")

dec_big = BinaryPayloadDecoder.fromRegisters([TEST_INT16_REGISTER], byteorder=Endian.BIG)
dec_little = BinaryPayloadDecoder.fromRegisters([TEST_INT16_REGISTER], byteorder=Endian.LITTLE)

val_big = dec_big.decode_16bit_int()
val_little = dec_little.decode_16bit_int()

print(f"  byteOrder=BIG:    {val_big}")
print(f"  byteOrder=LITTLE: {val_little}")

int16_needs_big = (val_big == TEST_INT16_EXPECTED)
int16_needs_little = (val_little == TEST_INT16_EXPECTED)

# String test
print(f"\nString Registers: {[hex(r) for r in TEST_STRING_REGISTERS]} (expecting '{TEST_STRING_EXPECTED}')")

dec_s_big = BinaryPayloadDecoder.fromRegisters(TEST_STRING_REGISTERS, byteorder=Endian.BIG)
dec_s_little = BinaryPayloadDecoder.fromRegisters(TEST_STRING_REGISTERS, byteorder=Endian.LITTLE)

raw_big = dec_s_big.decode_string(len(TEST_STRING_REGISTERS) * 2)
raw_little = dec_s_little.decode_string(len(TEST_STRING_REGISTERS) * 2)

fixed_big = swap_bytes_in_words(raw_big)
fixed_little = swap_bytes_in_words(raw_little)

print(f"  BIG (raw):           {raw_big}")
print(f"  BIG (byte-swapped):  {fixed_big}")
print(f"  LITTLE (raw):        {raw_little}")
print(f"  LITTLE (byte-swapped): {fixed_little}")

# Check which combination works
results = {
    "BIG, no fix": raw_big.decode('utf-8', errors='replace') == TEST_STRING_EXPECTED,
    "BIG, with fix": fixed_big.decode('utf-8', errors='replace') == TEST_STRING_EXPECTED,
    "LITTLE, no fix": raw_little.decode('utf-8', errors='replace') == TEST_STRING_EXPECTED,
    "LITTLE, with fix": fixed_little.decode('utf-8', errors='replace') == TEST_STRING_EXPECTED,
}

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)
print(f"INT16 needs: {'BIG' if int16_needs_big else 'LITTLE' if int16_needs_little else 'UNKNOWN'}")
print(f"String works with: {[k for k,v in results.items() if v]}")

if int16_needs_big and results["BIG, with fix"]:
    print("\n>>> PROBLEM: Need byteOrder=BIG for INT16, but fix applies at wrong time!")
    print("    Solution: Strings should be swapped when byteOrder=BIG, not LITTLE")
elif int16_needs_little and results["LITTLE, with fix"]:
    print("\n>>> Current fix works - use byteOrder=LITTLE")
else:
    print("\n>>> Custom configuration needed - report these results")
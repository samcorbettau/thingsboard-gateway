# Modbus String Null Terminator Fix

## Problem

PLCs like CODESYS use C-style null-terminated strings. When a string value changes from a longer value to a shorter one, the remaining bytes contain null characters (0x00).

Example:
- PLC string variable allocated as 10 characters
- Initially set to "DC12345" (7 chars + 3 nulls)
- Updated to "DC01" (4 chars + 6 nulls)
- ThingsBoard reads: "DC01\x00\x00\x00\x00\x00\x00"
- Decoded as: "DC01000000" or displays incorrectly

## Solution

### New Config Option: `stringNullTerminate`

When set to `true`, trailing null bytes (0x00) are stripped from strings.

**Default: `false`** (for backwards compatibility)

### Configuration

```json
{
  "byteOrder": "BIG",
  "wordOrder": "BIG",
  "stringNullTerminate": true
}
```

### Example

| Register Values | `stringNullTerminate: false` | `stringNullTerminate: true` |
|-----------------|------------------------------|----------------------------|
| `0x44 0x43 0x01 0x00 0x00 0x00` | "DC01\x00\x00" | "DC01" |
| "DC123" → "DC01" | "DC010000" (wrong) | "DC01" (correct) |

## How It Works

The fix adds null byte stripping after decoding:

```python
if string_null_terminate:
    decoded = decoded.rstrip(b'\x00')
```

This only affects the `string` and `bytes` data types.

## Backwards Compatibility

| Config | Behavior |
|--------|----------|
| Not set | No null stripping (original behavior) |
| `stringNullTerminate: false` | No null stripping |
| `stringNullTerminate: true` | Strips trailing nulls |

**No breaking changes** - existing configs work exactly as before.

## Files Modified

| File | Change |
|------|--------|
| `bytes_uplink_converter_config.py` | Added `string_null_terminate` config (default: False) |
| `bytes_modbus_uplink_converter.py` | Added null stripping for string/bytes types |

## Testing

Test with your CODESYS PLC:

```json
{
  "byteOrder": "BIG",
  "wordOrder": "BIG",
  "stringNullTerminate": true
}
```

Read a string that was shortened from "DC123" to "DC01":
- Without fix: Displays as "DC01" with garbage or wrong characters
- With fix: Displays correctly as "DC01"
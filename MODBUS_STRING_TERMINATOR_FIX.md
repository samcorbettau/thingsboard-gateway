# Modbus String Terminator Fix

## What Changed from Original Code

### Original Behavior
```python
# Config: No terminator option
# Code: Strings decoded as-is, no truncation
result_data = decoded.decode('UTF-8')
```

### New Behavior  
```python
# Config: stringTerminator option (default: None = original behavior)
# Code: Truncate at terminator byte if specified
if string_terminator is not None:
    terminator_pos = decoded.find(string_terminator)
    if terminator_pos != -1:
        decoded = decoded[:terminator_pos]
result_data = decoded.decode('UTF-8')
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `stringTerminator` | `null` | Byte at which to truncate strings (hex notation) |
| `null` | - | No truncation (original behavior) |
| `"0x00"` | - | Truncate at null byte (C-style strings) |
| `"0xFF"` | - | Truncate at 0xFF byte |

### Example for CODESYS

```json
{
  "byteOrder": "BIG",
  "wordOrder": "BIG",
  "stringTerminator": "0x00"
}
```

**Raw bytes:** `44 43 30 31 00 36 37 38 00 39 00 00` (D C 0 1 ␀ garbage...)

**Without terminator:** Displays garbage `"DC01\x00678\x009..."`

**With `"stringTerminator": "0x00"`:** Displays correctly `"DC01"`

## Test Results

```
Raw: 44 43 30 31 00 36 37 38 00 39 00 00 00 00 00

Without fix (stringTerminator=null):
  Result: "DC01\x00678\x009\x00\x00\x00\x00" WRONG

With fix (stringTerminator="0x00"):
  Result: "DC01" CORRECT
```

## Backwards Compatibility

| Config | Behavior |
|--------|----------|
| Not specified | Original behavior (no truncation) |
| `null` | Original behavior (no truncation) |
| `"0x00"` | Truncate at null byte |

**100% backwards compatible** - existing configs behave exactly as before.

## Files Modified

| File | Change |
|------|--------|
| `bytes_uplink_converter_config.py` | Added `stringTerminator` option with `_parse_terminator()` helper |
| `bytes_modbus_uplink_converter.py` | Added terminator byte handling in `decode_from_registers()` |
# Modbus String Null Terminator Fix

## Problem

PLCs like CODESYS use C-style null-terminated strings with fixed buffer sizes. When a string value changes from longer to shorter, the PLC doesn't clear the remaining buffer bytes.

**Example:**
- CODESYS String(15) initially contains "DC12345" (7 chars + 8 nulls)
- Updated to "DC01" (4 chars + 11 nulls)
- BUT the old data remains after the null: "DC01\x00garbage..."

**Actual bytes from your TM241:**
```
Raw: 43 44 31 30 36 00 38 37 00 39 00 00 00 00 00
      D  C  0  1  6  ␀  8  7  ␀  9  ␀  ␀  ␀  ␀  ␀
                 ^first null
```

After byte swap (LITTLE): "DC01\x00garbage689\x00..." 

My original fix using `rstrip(b'\x00')` would give:
- **WRONG**: "DC01\x00garbage689" (still contains garbage!)

## Fixed Implementation

**Stop at FIRST null byte (C-style string termination):**
```python
null_pos = decoded.find(b'\x00')
if null_pos != -1:
    decoded = decoded[:null_pos]
```

Result:
- **CORRECT**: "DC01" (stops at first null)

## Configuration

```json
{
  "byteOrder": "BIG",
  "wordOrder": "BIG",
  "stringNullTerminate": true
}
```

## Test Results

```
Raw bytes: 44 43 30 31 00 36 37 38 00 39 00 00 00 00 00

WITHOUT FIX (stringNullTerminate=false):
  Result: "DC01\x00garbage..." WRONG

WITH FIX (stringNullTerminate=true):
  Result: "DC01" CORRECT
```

## Backwards Compatibility

| Setting | Behavior |
|---------|----------|
| Not set / false | Original behavior - reads entire buffer |
| true | Truncates at first null byte |

**No breaking changes** - default is false for existing configs.
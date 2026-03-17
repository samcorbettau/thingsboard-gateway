# Modbus String Byte Order Fix

## Issue Summary

In the ThingsBoard Gateway Modbus connector, string values are not affected by the `byteOrder` configuration setting. When changing from BIG to LITTLE byte order:

- **INT16/INT32 values**: Correctly byte-swapped ✓
- **String values**: NOT byte-swapped ✗ (BUG)
- **Bytes values**: NOT byte-swapped ✗ (BUG)

## Root Cause

The bug is in the **pymodbus** library's `BinaryPayloadDecoder.decode_string()` method. While numeric types correctly apply byte order transformation via the internal `_unpack_words()` method, `decode_string()` **ignores both `byteorder` and `wordorder` parameters entirely**.

### pymodbus Code Comparison

**Numeric types (works correctly):**
```python
def decode_32bit_int(self):
    self._pointer += 4
    handle = self._payload[self._pointer - 4 : self._pointer]
    handle = self._unpack_words(handle)  # <-- Applies byte/word order
    return unpack("!i", handle)[0]
```

**String type (BUG - ignores byte order):**
```python
def decode_string(self, size=1):
    self._pointer += size
    return self._payload[self._pointer - size : self._pointer]  # <-- RAW bytes, no transformation!
```

## File Modified

**File:** `thingsboard_gateway/connectors/modbus/bytes_modbus_uplink_converter.py`

## Changes Required

### Change 1: Add Helper Method

Add this static method before `_get_device_report_strategy` (around line 340):

```python
@staticmethod
def _apply_byte_order_for_string(raw_bytes: bytes, byte_order, word_order) -> bytes:
    """Apply byte order transformation for strings/bytes.
    
    This mirrors what pymodbus's BinaryPayloadDecoder._unpack_words does for numeric types.
    The pymodbus decode_string() method ignores byte_order/word_order parameters,
    so strings and bytes were not being properly byte-swapped when byteOrder=LITTLE.
    
    Args:
        raw_bytes: Raw bytes from the Modbus device
        byte_order: Endian.BIG or Endian.LITTLE for byte order within each 16-bit word
        word_order: Endian.BIG or Endian.LITTLE for word order (multi-word values)
        
    Returns:
        Bytes with byte order transformation applied
    """
    from array import array
    
    if byte_order == Endian.LITTLE or word_order == Endian.LITTLE:
        # Convert bytes to array of 16-bit unsigned integers (words)
        handle = array("H", raw_bytes)
        
        if byte_order == Endian.LITTLE:
            # Swap bytes within each word
            handle.byteswap()
        
        if word_order == Endian.LITTLE:
            # Reverse word order
            handle.reverse()
        
        return handle.tobytes()
    
    return raw_bytes
```

### Change 2: Modify String Handling (around line 278-279)

**Before:**
```python
elif lower_type == "string":
    decoded = decoder_functions[lower_type](objects_count * 2)
```

**After:**
```python
elif lower_type == "string":
    decoded = decoder_functions[lower_type](objects_count * 2)
    # FIX: Apply byte order transformation for strings (pymodbus decode_string ignores byte order)
    decoded = self._apply_byte_order_for_string(decoded, decoder._byteorder, decoder._wordorder)
```

### Change 3: Modify Bytes Handling (around line 281-282)

**Before:**
```python
elif lower_type == "bytes":
    decoded = decoder_functions[lower_type](size=objects_count * 2)
```

**After:**
```python
elif lower_type == "bytes":
    decoded = decoder_functions[lower_type](size=objects_count * 2)
    # FIX: Apply byte order transformation for raw bytes (same issue as strings)
    decoded = self._apply_byte_order_for_string(decoded, decoder._byteorder, decoder._wordorder)
```

## How to Apply Fix in Docker Container

### Step 1: Enter the Container

```bash
# List running containers
docker ps

# Enter the container
docker exec -it <container_name> bash

# Or with docker-compose
docker-compose exec <service_name> bash
```

### Step 2: Find and Open the File

```bash
# Find installation location
pip show thingsboard-gateway | grep Location

# Navigate to the file (path may vary)
cd /usr/local/lib/python3.X/site-packages/thingsboard_gateway/connectors/modbus/

# Install nano if needed
apt-get update && apt-get install -y nano

# Open the file
nano bytes_modbus_uplink_converter.py
```

### Step 3: Nano Editor Commands

| Command | Action |
|---------|--------|
| `Ctrl + O` | Save file |
| `Ctrl + X` | Exit nano |
| `Ctrl + W` | Search for text |
| `Alt + G` | Go to line number |

### Step 4: Make Changes and Restart

```bash
# After editing, exit container and restart
exit

# Restart the gateway
docker restart <container_name>
```

## Testing

### Verification Command

After applying the fix, verify it's in place:

```bash
grep -n "_apply_byte_order_for_string" bytes_modbus_uplink_converter.py
# Should show the method definition and two call sites
```

### Expected Behavior After Fix

| Setting | Before Fix | After Fix |
|---------|------------|-----------|
| `byteOrder=BIG` | Strings: raw bytes | Strings: raw bytes (no change) |
| `byteOrder=LITTLE` | Strings: **raw bytes (BUG)** | Strings: **byte-swapped within each register** |
| `wordOrder=LITTLE` | Strings: **raw bytes (BUG)** | Strings: **register order reversed** |

### Example

Device sends string "ABCD" across 2 registers: `[0x4142, 0x4344]`

- **BIG endian:** Returns "ABCD" correctly
- **LITTLE endian:**
  - Before fix: "ABCD" (wrong - bytes not swapped)
  - After fix: "BADC" (correct - bytes within each register swapped)

## Files Reference

| File | Purpose |
|------|---------|
| `bytes_modbus_uplink_converter.py` | Main file to modify |
| `bytes_uplink_converter_config.py` | Config class (byteOrder/wordOrder settings) |
| `slave.py` | Device configuration handling |

## Related Upstream Issue

This is a known limitation in pymodbus's `BinaryPayloadDecoder.decode_string()` method that ignores endianness settings. The fix works around this by applying the byte order transformation after decoding.

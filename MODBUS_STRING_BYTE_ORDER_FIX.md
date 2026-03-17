# Modbus String Byte Order Fix

## Background

Different PLC manufacturers use different byte ordering for strings vs numeric values:

### Schneider TM241
- **Numeric values**: BIG endian (standard Modbus)
- **Strings**: LITTLE endian (characters reversed within registers)

### Siemens, Allen-Bradley
- **Numeric values**: BIG endian
- **Strings**: BIG endian (same as numerics)

## The Problem

On Schneider TM241, you cannot use a single `byteOrder` setting for both:
- `byteOrder=BIG`: Numbers correct (49418), Strings wrong (`_AXM10`)
- `byteOrder=LITTLE`: Strings correct (`A_MX01`), Numbers wrong (2753)

## The Solution

### New Config Option: `stringByteOrder`

A separate setting for string byte ordering that **defaults to the OPPOSITE** of `byteOrder`:

```json
{
  "byteOrder": "BIG",
  "wordOrder": "BIG"
}
```

For Schneider TM241, strings automatically get LITTLE byte order.

For PLCs where strings use the same byte order as numerics (Siemens, Allen-Bradley), set explicitly:
```json
{
  "byteOrder": "BIG",
  "wordOrder": "BIG",
  "stringByteOrder": "BIG"
}
```

## Your Configuration for Schneider TM241

```json
{
  "byteOrder": "BIG",
  "wordOrder": "BIG"
}
```

With this fix, strings automatically use LITTLE byte order, giving:
- Strings: `A_MX01`, `CD01` (correct!)
- Numbers: 49418 (correct!)

## Test Results

```
REGISTERS:
  String: [0x5f41, 0x584d, 0x3130]  
  Number: 0xC10A

NUMERIC TEST:
  byteOrder=BIG, type=16uint:   49418  (expected)
  
STRING TEST:
  Raw (no fix):              _AXM10 (wrong)
  stringByteOrder=LITTLE:    A_MX01 (CORRECT!)
```

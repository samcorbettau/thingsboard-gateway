#     Copyright 2026. ThingsBoard
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   
#     See the License for the specific language governing permissions and
#     limitations under the License.

from pymodbus.constants import Endian


class BytesUplinkConverterConfig:
    def __init__(self, **kwargs):
        self.report_strategy = kwargs.get('reportStrategy')
        self.device_name = kwargs['deviceName']
        self.device_type = kwargs.get('deviceType', 'default')
        self.byte_order = Endian.BIG if kwargs.get('byteOrder', 'LITTLE').upper() == "BIG" else Endian.LITTLE
        self.word_order = Endian.BIG if kwargs.get('wordOrder', 'LITTLE').upper() == "BIG" else Endian.LITTLE
        
        # String/bytes byte order - defaults to same as byteOrder for backwards compatibility
        # Set explicitly for PLCs like Schneider that use different byte order for strings
        self.string_byte_order = Endian.BIG if kwargs.get('stringByteOrder', 
                                                          kwargs.get('byteOrder', 'LITTLE')).upper() == "BIG" else Endian.LITTLE

        # String terminator configuration
        # Allows truncating strings at a specific terminator byte (for PLCs like CODESYS)
        # 
        # Usage:
        #   stringTerminator: "0x00"  - Truncate at null byte (C-style strings)
        #   stringTerminator: null    - No truncation (default, original behavior)
        #   stringTerminator: "0xFF"  - Truncate at 0xFF byte
        #
        # Example for CODESYS String(15):
        #   Raw bytes: 44 43 30 31 00 36 37 38 00 39 00 00 00 00 00
        #              D  C  0  1  ␀  garbage...
        #   With stringTerminator="0x00" → "DC01" (truncated at first ␀)
        #
        # Default: None (no truncation, original behavior for backwards compatibility)
        terminator_value = kwargs.get('stringTerminator', None)
        self.string_terminator = self._parse_terminator(terminator_value)
        
        self.telemetry = kwargs.get('timeseries', [])
        self.attributes = kwargs.get('attributes', [])
        self.unit_id = kwargs['unitId']

    def _parse_terminator(self, value):
        """Parse terminator value to bytes.
        
        Accepts:
        - None or "" or False: disabled (returns None)
        - "0x00": hex notation → b'\\x00'
        - "0xFF": hex notation → b'\\xff'
        - 0: integer → b'\\x00'
        - 255: integer → b'\\xff'
        
        Returns bytes object or None
        """
        if value is None or value == "" or value is False:
            return None
        
        # Handle hex string notation like "0x00" or "0xFF"
        if isinstance(value, str):
            if value.lower().startswith('0x'):
                try:
                    byte_val = int(value, 16)
                    return bytes([byte_val])
                except ValueError:
                    return None
            # Handle literal byte strings like "\x00"
            try:
                return value.encode('latin-1')
            except:
                return None
        
        # Handle integer values
        if isinstance(value, int):
            if 0 <= value <= 255:
                return bytes([value])
        
        return None

    def is_readable(self):
        return len(self.telemetry) > 0 or len(self.attributes) > 0
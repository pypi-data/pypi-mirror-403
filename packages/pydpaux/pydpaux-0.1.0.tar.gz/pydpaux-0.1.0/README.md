# pyDpaux

A Python wrapper for accessing DP/eDP-connected displays via AUX lines using SoC vendor-specific APIs.

## Overview

**pyDpaux** provides a high-level Python interface to interact with DisplayPort-connected displays through the AUX protocol. It enables reading EDID data, performing I2C communication, and accessing DPCD (DisplayPort Configuration Data) registers.

Currently, only **Intel IGCL (Intel Graphics Control Library) API on Windows** is implemented. Support for other platforms and vendors is planned. Contributions are welcome!

**License:** MIT

## System Requirements

- **Processor:** 12th generation (or later) Intel Core processors
- **Operating System:** Windows 10 or later
- **Python:** 3.9 or later
- **Permissions:** Administrator/elevated privileges required for AUX / I2C Write operations

## Key Features

- **Display Discovery:** Enumerate all connected DP/eDP displays
- **Display Search:** Find displays by partial name matching
- **EDID Access:** Read and parse Extended Display Identification Data
- **AUX Channel Communication:** Direct read/write access to DisplayPort AUX channels
- **I2C Bus Access:** Read/write data via AUX-OVER-I2C protocol
- **DPCD Support:** Access DisplayPort Configuration Data registers
- **Display Properties:** Query display name, serial number, and metadata

## Installation

### From PyPI

```bash
pip install pydpaux
```

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/bitlab-rgb/pydpaux.git
cd pydpaux
pip install .
```

## Building from Source

### Prerequisites

- Python 3.9+ with development headers
- Microsoft Visual C++ Build Tools or Visual Studio 2015 or later (for C++ compilation)
- CMake 3.15 or later
- Git

### Build Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bitlab-rgb/pydpaux.git
   cd pydpaux
   ```

2. **Install build dependencies:**
   ```bash
   pip install build scikit-build-core pybind11
   ```

3. **Build the extension:**
   ```bash
   python -m build
   ```

   Or for development/editable installation:
   ```bash
   pip install -e .
   ```

4. **Verify installation:**
   ```bash
   python -c "import pydpaux; print(pydpaux.__version__)"
   ```

## Quick Start

### Basic Usage

Here's a simple example to discover and interact with displays:

```python
import pydpaux

# Get all connected displays
displays = pydpaux.get_displays()

if displays:
    display = displays[0]
    print(f"Found display: {display.name}")
    print(f"Serial: {display.serial}")
    print(f"EDID Size: {display.edid_size} bytes")
else:
    print("No displays found")
```

### Finding a Specific Display

```python
import pydpaux

# Find a display by partial name match
display = pydpaux.find_display_by_name("LG")

if display:
    print(f"Found: {display.name}")
else:
    print("No matching display found")
```

### Reading EDID Data

```python
import pydpaux

display = pydpaux.get_displays()[0]

# Read EDID via I2C (first 8 bytes)
edid_header = display.i2c_read(0xa0, 0x00, 8)
print("EDID Header:", ", ".join(f"0x{b:02x}" for b in edid_header))

# Access complete EDID
full_edid = display.edid
print(f"Full EDID size: {len(full_edid)} bytes")
```

### Reading DPCD Registers

```python
import pydpaux

display = pydpaux.get_displays()[0]

# Read individual DPCD registers
print("Reading DPCD registers:")
for addr in [0x00, 0x01, 0x02, 0x03, 0x0C, 0x22, 0x101]:
    value = display.aux_read(addr, 1)[0]
    print(f"  0x{addr:04x}: 0x{value:02x}")
```

### Writing to I2C Bus

```python
import pydpaux

display = pydpaux.get_displays()[0]

# Write data to I2C device at address 0x6e, offset 0x51
data = bytes([0x82, 0x01, 0x10, 0xAC])
try:
    result = display.i2c_write(0x6e, 0x51, data)
    if result == 0:
        print("Write successful")
    else:
        print(f"Write failed with code: 0x{result:08x}")
except PermissionError:
    print("Error: Insufficient permissions. Please run with elevated privileges.")
except RuntimeError as e:
    print(f"Error: {e}")
```

### Complete Example Script

For a comprehensive example, see [test/test.py](test/test.py):

```python
import pydpaux
import sys

# Find display by name (if provided as argument) or use first available
name = sys.argv[1] if len(sys.argv) > 1 else ""

if name:
    display = pydpaux.find_display_by_name(name)
    if not display:
        print(f"No display named {name}")
        exit()
else:
    displays = pydpaux.get_displays()
    if not displays:
        print("No display found")
        exit()
    display = displays[0]

print(f"Found display: {display.name}")

# Read EDID via I2C
print("\nTest EDID read with i2c_read():")
edid_data = display.i2c_read(0xa0, 0x00, 8)
print(", ".join(map(lambda x: f'0x{x:02x}', edid_data)))

# Read DPCD registers
print("\nTest DPCD read with aux_read():")
for addr in [0x00, 0x01, 0x02, 0x03, 0x0C, 0x22, 0x101]:
    value = display.aux_read(addr, 1)[0]
    print(f"0x{addr:04x}: 0x{value:02x}")
```

## API Reference

### Module Functions

#### `get_displays() -> List[Display]`
Get all connected DP/eDP displays.

**Returns:** List of `Display` objects

#### `find_display_by_name(keyword: str) -> Display | None`
Find a display by partial name match (case-sensitive).

**Parameters:**
- `keyword` - Search keyword to match in display names

**Returns:** First matching `Display` object or `None`

### Display Class

#### Properties

- **`name: str`** - Display name/identifier
- **`serial: str`** - Display serial number
- **`edid_size: int`** - Size of EDID data in bytes
- **`edid: bytes`** - Complete EDID data

#### Methods

- **`aux_read(address: int, size: int) -> bytes`** - Read from AUX channel
- **`aux_write(address: int, data: bytes) -> int`** - Write to AUX channel
- **`i2c_read(address: int, offset: int, size: int) -> bytes`** - Read from I2C bus
- **`i2c_write(address: int, offset: int, data: bytes) -> int`** - Write to I2C bus
- **`refresh_handle() -> int`** - Refresh display output handle

All methods may raise:
- `PermissionError` - If insufficient privileges (requires administrator mode)
- `RuntimeError` - If the operation fails

## Troubleshooting

### "PermissionError: Insufficient permission"

This error indicates that administrator/elevated privileges are required. Run your Python script or terminal with administrator privileges:

- **Command Prompt:** Right-click and select "Run as administrator"
- **PowerShell:** Right-click and select "Run as administrator"
- Or use `pypy` in administrator mode

### "No display found"

- Verify that your display is connected via DisplayPort or eDP
- Check that your system has a 12th-gen or later Intel Core processor
- Some systems may have DisplayPort functionality disabled in BIOS

### AUX/I2C operations failing with RuntimeError

- Ensure you have a supported Intel GPU with IGCL API support
- Verify display connection is stable
- Try calling `refresh_handle()` to update the display handle

## Contributing

Contributions are welcome! Areas for improvement include:

- Support for other platforms (Linux, macOS)
- Support for other GPU vendors (AMD, NVIDIA)
- Additional display control functionality
- Bug reports and fixes

## Supported Platforms

| Platform | Status | GPU Support |
|----------|--------|-------------|
| Windows 10+ | ✅ Supported | Intel IGCL API (12th gen+) |
| Linux | 📋 Planned | - |
| macOS | 📋 Planned | - |

## Resources

- [DisplayPort Standard](https://en.wikipedia.org/wiki/DisplayPort)
- [EDID Format](https://en.wikipedia.org/wiki/Extended_Display_Identification_Data)
- [I2C Protocol](https://en.wikipedia.org/wiki/I%C2%B2C)
- [Intel IGCL API Documentation](https://www.intel.com/)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions:

- 📝 [Create an Issue](https://github.com/bitlab-rgb/pydpaux/issues)
- 💬 [Discussions](https://github.com/bitlab-rgb/pydpaux/discussions)

## Disclaimer

This software provides direct access to display hardware interfaces. Improper use may affect display functionality. Use at your own risk and always test in a controlled environment.


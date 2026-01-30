# polono-p31s

A Python library for printing labels on Polono P31S thermal printers via Bluetooth Low Energy (BLE).

## Installation

```bash
pip install polono-p31s
```

## Quick Start

### As a Library

```python
import asyncio
from polono_p31s import PolonoP31S

async def print_label():
    printer = PolonoP31S(width_mm=14, height_mm=40)
    
    # Render text to image
    img = printer.render_text("Hello World", font_size=48)
    
    # Connect and print
    if await printer.connect_ble():
        await printer.print_ble(img)
        await printer.disconnect_ble()

asyncio.run(print_label())
```

### As a CLI Tool

```bash
# Print text
polono text "Hello World" --font-size 48

# Print QR code
polono qr "https://example.com"

# Print image
polono image logo.png

# Print barcode
polono barcode "123456789" --type code128

# Preview without printing
polono text "Test" --preview

# Scan for printers
polono scan
```

## Features

- **BLE Communication**: Connect to P31S printers via Bluetooth Low Energy
- **Text Rendering**: Print text with customizable fonts, sizes, and alignment
- **QR Codes**: Generate and print QR codes
- **Barcodes**: Support for Code128, Code39, EAN13, and more
- **Image Printing**: Print any image file
- **Preview Mode**: Generate preview images without printing
- **Auto-fit**: Automatically scale text to fit labels

## Label Specifications

- **Default size**: 14mm × 40mm with 5mm gap
- **Resolution**: 203 DPI (8 dots/mm)
- **Density**: Adjustable 1-15 (default: 15)

## API Reference

### PolonoP31S Class

```python
class PolonoP31S:
    def __init__(
        self,
        width_mm: float = 14.0,
        height_mm: float = 40.0,
        gap_mm: float = 5.0,
        density: int = 15,
    ): ...

    # Connection
    async def connect_ble(self, address: Optional[str] = None) -> bool: ...
    async def disconnect_ble(self) -> None: ...

    # Rendering (returns PIL Image)
    def render_text(self, text: str, font_size: int = 24, ...) -> Image: ...
    def render_image(self, image_path: str) -> Image: ...
    def render_qr(self, data: str) -> Optional[Image]: ...
    def render_barcode(self, data: str, barcode_type: str = "code128") -> Optional[Image]: ...

    # Printing
    async def print_ble(self, img: Image, copies: int = 1) -> None: ...

    # Utilities
    def check_text_fit(self, text: str, font_size: int) -> dict: ...
    def find_fitting_font_size(self, text: str, max_font_size: int = 200) -> int: ...
```

## Environment Variables

- `POLONO_ADDRESS`: Default printer BLE address (skips scanning)

## Dependencies

- `bleak` - BLE communication
- `Pillow` - Image processing
- `click` - CLI framework
- `rich` - Console output formatting
- `qrcode` - QR code generation
- `python-barcode` - Barcode generation

## License

MIT License

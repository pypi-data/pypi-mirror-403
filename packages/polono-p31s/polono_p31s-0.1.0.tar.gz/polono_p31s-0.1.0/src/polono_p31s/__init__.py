"""
Polono P31S Thermal Label Printer Library

A Python library for printing labels on Polono P31S thermal printers via Bluetooth Low Energy (BLE).
Uses TSPL (Taiwan Semiconductor Programming Language) commands over BLE.

Example usage:
    from polono_p31s import PolonoP31S

    printer = PolonoP31S()
    img = printer.render_text("Hello World", font_size=48)
    
    # Connect and print
    await printer.connect_ble()
    await printer.print_ble(img)
    await printer.disconnect_ble()
"""

from .printer import (
    PolonoP31S,
    BLE_WRITE_CHAR,
    BLE_NOTIFY_CHAR,
    ADDRESS_CACHE_FILE,
)

__version__ = "0.1.0"
__all__ = [
    "PolonoP31S",
    "BLE_WRITE_CHAR",
    "BLE_NOTIFY_CHAR",
    "ADDRESS_CACHE_FILE",
    "__version__",
]

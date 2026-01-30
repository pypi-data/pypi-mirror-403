"""
Polono P31S Thermal Label Printer Library

Core printer interface class using TSPL commands over BLE.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("polono_p31s")

# BLE UUIDs for P31S printer (discovered via packet capture)
BLE_WRITE_CHAR = "0000ff02-0000-1000-8000-00805f9b34fb"
BLE_NOTIFY_CHAR = "0000ff01-0000-1000-8000-00805f9b34fb"

# Cache file for printer address
ADDRESS_CACHE_FILE = Path.home() / ".polono_address"


def save_preview(img: Image.Image, output_path: str):
    """Save a label image as a preview file."""
    # Convert 1-bit to RGB for better compatibility
    img_rgb = img.convert('RGB')
    img_rgb.save(output_path)
    logger.info(f"Preview saved to {output_path}")


class PolonoP31S:
    """Polono P31S thermal label printer interface using TSPL commands over BLE."""
    
    # Default label dimensions (mm)
    DEFAULT_WIDTH_MM = 14.0
    DEFAULT_HEIGHT_MM = 40.0
    DEFAULT_GAP_MM = 5.0
    DEFAULT_DENSITY = 15  # 1-15
    
    # Printer resolution: 203 DPI (8 dots/mm)
    DPI = 203
    DOTS_PER_MM = 8
    
    def __init__(
        self,
        width_mm: float = DEFAULT_WIDTH_MM,
        height_mm: float = DEFAULT_HEIGHT_MM,
        gap_mm: float = DEFAULT_GAP_MM,
        density: int = DEFAULT_DENSITY,
    ):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.gap_mm = gap_mm
        self.density = min(15, max(1, density))
        self.ble_client = None
        self.ble_address: Optional[str] = None
        
        # Calculate pixel dimensions
        self.width_px = int(width_mm * self.DOTS_PER_MM)
        self.height_px = int(height_mm * self.DOTS_PER_MM)
    
    @staticmethod
    def _load_cached_address() -> Optional[str]:
        """Load cached printer address from file."""
        try:
            if ADDRESS_CACHE_FILE.exists():
                return ADDRESS_CACHE_FILE.read_text().strip()
        except Exception:
            pass
        return None
    
    @staticmethod
    def _save_cached_address(address: str):
        """Save printer address to cache file."""
        try:
            ADDRESS_CACHE_FILE.write_text(address)
        except Exception:
            pass
    
    @staticmethod
    async def find_printer_ble() -> Optional[str]:
        """Scan for P31S printer via BLE and return its address."""
        try:
            from bleak import BleakScanner
        except ImportError:
            return None
        
        try:
            # Use find_device_by_filter which stops as soon as it finds a match
            device = await BleakScanner.find_device_by_filter(
                lambda d, adv: d.name and 'P31S' in d.name,
                timeout=10.0
            )
            if device:
                return device.address
        except Exception:
            pass
        return None
    
    async def connect_ble(self, address: Optional[str] = None) -> bool:
        """Connect to printer via BLE.
        
        Args:
            address: Optional BLE address to connect directly (skips scanning)
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            from bleak import BleakClient, BleakScanner
        except ImportError:
            logger.error("bleak library required: pip install bleak")
            return False
        
        # Try sources for address: parameter > env var > cache
        target_address = address or os.environ.get('POLONO_ADDRESS') or self._load_cached_address()
        
        try:
            if target_address:
                # Try direct connection to known address
                logger.info(f"Connecting to {target_address}...")
                self.ble_client = BleakClient(target_address, timeout=10.0)
                try:
                    await self.ble_client.connect()
                    self.ble_address = target_address
                    logger.info("Connected via BLE")
                    return True
                except Exception:
                    # Direct connection failed, fall through to scanning
                    logger.warning("Cached address failed, scanning...")
                    self.ble_client = None
            
            # Scan for printer (stops as soon as it finds one)
            logger.info("Scanning for P31S...")
            device = await BleakScanner.find_device_by_filter(
                lambda d, adv: d.name and 'P31S' in d.name,
                timeout=10.0
            )
            
            if not device:
                logger.error("P31S not found. Is the printer on?")
                logger.debug("Press the printer button to wake it up")
                return False
            
            logger.info(f"Found {device.name}")
            
            self.ble_client = BleakClient(device.address, timeout=10.0)
            await self.ble_client.connect()
            self.ble_address = device.address
            
            # Cache the address for next time
            self._save_cached_address(device.address)
            
            logger.info("Connected via BLE")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect_ble(self):
        """Disconnect BLE connection."""
        if self.ble_client and self.ble_client.is_connected:
            await self.ble_client.disconnect()
            logger.info("Disconnected")
        self.ble_client = None
    
    async def _send_ble(self, data: bytes):
        """Send data via BLE in chunks."""
        if not self.ble_client or not self.ble_client.is_connected:
            raise RuntimeError("Not connected to printer")
        
        # Send in MTU-sized chunks
        chunk_size = 180
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            await self.ble_client.write_gatt_char(BLE_WRITE_CHAR, chunk, response=False)
            await asyncio.sleep(0.03)
    
    async def _init_printer_ble(self):
        """Send initialization sequence via BLE."""
        # ESC ! o - Initialize printer (from captured protocol)
        await self._send_ble(b'\x1b!o\r\n')
        await asyncio.sleep(0.2)
        
    async def print_ble(self, img: Image.Image, copies: int = 1):
        """
        Print a pre-rendered image via BLE.
        
        Args:
            img: PIL Image to print (should be in mode '1', landscape orientation)
            copies: Number of copies
        """
        await self._init_printer_ble()
        cmd = self._build_print_command(img)
        
        if copies > 1:
            cmd = cmd.replace(b'PRINT 1\r\n', f'PRINT {copies}\r\n'.encode())
        
        await self._send_ble(cmd)
        await asyncio.sleep(2)  # Wait for print

        
    
    def _image_to_bitmap(self, img: Image.Image) -> tuple[int, int, bytes]:
        """
        Convert PIL Image to TSPL bitmap format.
        
        The image is rotated 90° clockwise for vertical label orientation.
        
        Returns: (width_bytes, height, bitmap_data)
        
        TSPL BITMAP format: 1 bit per pixel, MSB first
        0 = black (printed), 1 = white (not printed)
        """
        # Rotate image 90° clockwise for correct label orientation
        img_rotated = img.rotate(-90, expand=True)
        
        # Convert to 1-bit image (black and white)
        img_bw = img_rotated.convert('1')
        
        width, height = img_bw.size
        width_bytes = (width + 7) // 8  # Round up to byte boundary
        
        # Build bitmap data
        bitmap_data = bytearray()
        pixels = img_bw.load()
        
        for y in range(height):
            for byte_x in range(width_bytes):
                byte_val = 0
                for bit in range(8):
                    x = byte_x * 8 + bit
                    if x < width:
                        # In PIL '1' mode: 0 = black, 255 = white
                        # In TSPL: 0 = print (black), 1 = no print (white)
                        pixel = pixels[x, y]
                        if pixel != 0:  # White pixel
                            byte_val |= (0x80 >> bit)
                    else:
                        # Padding bits are white (not printed)
                        byte_val |= (0x80 >> bit)
                bitmap_data.append(byte_val)
        
        return width_bytes, height, bytes(bitmap_data)
    
    def _build_print_command(self, img: Image.Image) -> bytes:
        """Build complete TSPL print command with bitmap."""
        width_bytes, height, bitmap_data = self._image_to_bitmap(img)
        
        cmd = (
            f'SIZE {self.width_mm:.1f} mm,{self.height_mm:.1f} mm\r\n'
            f'GAP {self.gap_mm:.1f} mm,0 mm\r\n'
            f'DIRECTION 0,0\r\n'
            f'DENSITY {self.density}\r\n'
            f'CLS\r\n'
            f'BITMAP 0,0,{width_bytes},{height},1,'
        ).encode('utf-8')
        
        cmd += bitmap_data
        cmd += b'\r\nPRINT 1\r\n'
        
        return cmd
    
    def _load_font(self, font_size: int, font_path: Optional[str] = None):
        """Load a font for rendering text."""
        try:
            if font_path:
                return ImageFont.truetype(font_path, font_size)
            else:
                # Try common system fonts
                font_names = [
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/System/Library/Fonts/SFNSMono.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans.ttf",
                ]
                for fname in font_names:
                    if Path(fname).exists():
                        return ImageFont.truetype(fname, font_size)
                return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()
    
    def check_text_fit(
        self,
        text: str,
        font_size: int = 24,
        font_path: Optional[str] = None,
    ) -> dict:
        """
        Check if text will fit within the label dimensions.
        
        Args:
            text: Text to check
            font_size: Font size in points
            font_path: Path to TTF font file
        
        Returns:
            dict with keys:
                - fits: bool, True if text fits completely
                - text_width: int, width of text in pixels
                - text_height: int, height of text in pixels
                - label_width: int, available width (long edge) in pixels
                - label_height: int, available height (short edge) in pixels
                - overflow_x: int, pixels overflowing horizontally (0 if fits)
                - overflow_y: int, pixels overflowing vertically (0 if fits)
        """
        font = self._load_font(font_size, font_path)
        
        # Create temporary image just to measure text
        img = Image.new('1', (1, 1))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Label dimensions (height_px is long edge, width_px is short edge)
        label_width = self.height_px  # Long edge (text flows along this)
        label_height = self.width_px  # Short edge
        
        overflow_x = max(0, text_width - label_width)
        overflow_y = max(0, text_height - label_height)
        
        return {
            'fits': overflow_x == 0 and overflow_y == 0,
            'text_width': text_width,
            'text_height': text_height,
            'label_width': label_width,
            'label_height': label_height,
            'overflow_x': overflow_x,
            'overflow_y': overflow_y,
        }
    
    def find_fitting_font_size(
        self,
        text: str,
        max_font_size: int = 200,
        min_font_size: int = 8,
        font_path: Optional[str] = None,
    ) -> int:
        """
        Find the largest font size that fits the text within the label.
        
        Uses binary search for efficiency.
        
        Args:
            text: Text to fit
            max_font_size: Maximum font size to try
            min_font_size: Minimum font size to try
            font_path: Path to TTF font file
        
        Returns:
            Largest font size that fits
        """
        low, high = min_font_size, max_font_size
        best_size = min_font_size
        
        while low <= high:
            mid = (low + high) // 2
            fit = self.check_text_fit(text, font_size=mid, font_path=font_path)
            
            if fit['fits']:
                best_size = mid
                low = mid + 1  # Try larger
            else:
                high = mid - 1  # Try smaller
        
        return best_size
    
    def render_text(
        self,
        text: str,
        font_size: int = 24,
        font_path: Optional[str] = None,
        bold: bool = False,
        align: str = "center",
    ) -> Image.Image:
        """
        Render text to a bitmap image suitable for the label.
        
        Image is created in LANDSCAPE orientation (height_px × width_px)
        because it will be rotated 90° clockwise during bitmap conversion.
        
        Args:
            text: Text to render
            font_size: Font size in points
            font_path: Path to TTF font file (uses default if None)
            bold: Use bold font variant
            align: Text alignment - "left", "center", or "right"
        
        Returns:
            PIL Image in mode '1' (1-bit pixels), landscape orientation
        """
        # Create image in LANDSCAPE (height_px × width_px) - will be rotated later
        img = Image.new('1', (self.height_px, self.width_px), color=1)
        draw = ImageDraw.Draw(img)
        
        font = self._load_font(font_size, font_path)
        
        # Calculate text dimensions
        # textbbox returns (x0, y0, x1, y1) - need to account for offsets
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate horizontal position based on alignment
        # Subtract bbox[0] to account for font's left bearing
        padding = 4  # Small padding from edges
        if align == "left":
            x = padding - bbox[0]
        elif align == "right":
            x = self.height_px - text_width - padding - bbox[0]
        else:  # center
            x = (self.height_px - text_width) // 2 - bbox[0]
        
        # Vertical position is always centered
        # Subtract bbox[1] to account for font's top bearing/ascent offset
        # Additional -5 adjustment for better visual centering
        y = (self.width_px - text_height) // 2 - bbox[1] - 5
        
        # Draw text (black on white)
        # PIL's align parameter controls multi-line text alignment
        draw.text((x, y), text, font=font, fill=0, align=align)
        
        return img
    
    def render_image(self, image_path: str) -> Image.Image:
        """
        Render an image file to a label-sized bitmap.
        
        Args:
            image_path: Path to image file
        
        Returns:
            PIL Image in mode '1' (1-bit pixels), landscape orientation
        """
        # Load and resize image to fit label (in landscape orientation)
        img = Image.open(image_path)
        
        # Resize to fit label while maintaining aspect ratio
        # Use landscape dimensions since rotation happens in _image_to_bitmap
        img.thumbnail((self.height_px, self.width_px), Image.Resampling.LANCZOS)
        
        # Create white background in landscape orientation
        label_img = Image.new('1', (self.height_px, self.width_px), color=1)
        
        # Convert to grayscale then to 1-bit
        if img.mode != '1':
            img = img.convert('L')  # Grayscale first
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
        
        # Center the image
        x = (self.height_px - img.width) // 2
        y = (self.width_px - img.height) // 2
        label_img.paste(img, (x, y))
        
        return label_img
    
    def render_qr(self, data: str) -> Optional[Image.Image]:
        """
        Render a QR code to a label-sized bitmap.
        
        Args:
            data: Data to encode in QR code
        
        Returns:
            PIL Image in mode '1' (1-bit pixels), landscape orientation, or None if qrcode not installed
        """
        try:
            import qrcode
        except ImportError:
            logger.error("qrcode library required: pip install qrcode")
            return None
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to fit label (landscape orientation)
        qr_img = qr_img.convert('L')
        qr_img.thumbnail((min(self.height_px, self.width_px) - 20,) * 2, Image.Resampling.LANCZOS)
        
        # Create label image in landscape
        label_img = Image.new('1', (self.height_px, self.width_px), color=1)
        
        # Center QR code
        qr_img = qr_img.point(lambda x: 0 if x < 128 else 255, '1')
        x = (self.height_px - qr_img.width) // 2
        y = (self.width_px - qr_img.height) // 2
        label_img.paste(qr_img, (x, y))
        
        return label_img
    
    def render_barcode(
        self,
        data: str,
        barcode_type: str = "code128",
        height: int = 60,
    ) -> Optional[Image.Image]:
        """
        Render a barcode to a label-sized bitmap.
        
        Args:
            data: Data to encode
            barcode_type: Barcode type (code128, code39, ean13, etc.)
            height: Barcode height in pixels
        
        Returns:
            PIL Image in mode '1' (1-bit pixels), landscape orientation, or None if python-barcode not installed
        """
        try:
            from barcode import get_barcode_class
            from barcode.writer import ImageWriter
        except ImportError:
            logger.error("python-barcode library required: pip install python-barcode")
            return None
        
        # Generate barcode
        barcode_cls = get_barcode_class(barcode_type)
        barcode_obj = barcode_cls(data, writer=ImageWriter())
        
        # Write to image
        from io import BytesIO
        buffer = BytesIO()
        barcode_obj.write(buffer, options={'write_text': True, 'module_height': height / 10})
        buffer.seek(0)
        barcode_img = Image.open(buffer)
        
        # Resize to fit label (landscape orientation)
        barcode_img.thumbnail((self.height_px - 20, self.width_px - 20), Image.Resampling.LANCZOS)
        
        # Create label image in landscape
        label_img = Image.new('1', (self.height_px, self.width_px), color=1)
        
        # Convert and center barcode
        barcode_img = barcode_img.convert('L').point(lambda x: 0 if x < 128 else 255, '1')
        x = (self.height_px - barcode_img.width) // 2
        y = (self.width_px - barcode_img.height) // 2
        label_img.paste(barcode_img, (x, y))
        
        return label_img
    
    async def feed_ble(self, count: int = 1):
        """Feed labels without printing via BLE."""
        await self._init_printer_ble()
        cmd = f'FEED {count}\r\n'.encode()
        await self._send_ble(cmd)
    
    async def get_status_ble(self) -> Optional[str]:
        """Query printer status via BLE."""
        if not self.ble_client or not self.ble_client.is_connected:
            return None
        
        response = []
        
        def notify_handler(sender, data):
            response.append(data)
        
        await self.ble_client.start_notify(BLE_NOTIFY_CHAR, notify_handler)
        await self._send_ble(b'CONFIG?\r\n')
        await asyncio.sleep(1)
        await self.ble_client.stop_notify(BLE_NOTIFY_CHAR)
        
        if response:
            return b''.join(response).decode('utf-8', errors='ignore')
        return None

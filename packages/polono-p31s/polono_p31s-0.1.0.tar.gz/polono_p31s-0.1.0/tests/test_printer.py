"""Tests for polono_p31s printer module."""

import pytest
from PIL import Image

from polono_p31s import PolonoP31S


class TestPolonoP31S:
    """Tests for the PolonoP31S class."""

    def test_init_default_dimensions(self):
        """Test default printer initialization."""
        printer = PolonoP31S()
        assert printer.width_mm == 14.0
        assert printer.height_mm == 40.0
        assert printer.gap_mm == 5.0
        assert printer.density == 15
        assert printer.width_px == 112  # 14 * 8
        assert printer.height_px == 320  # 40 * 8

    def test_init_custom_dimensions(self):
        """Test printer with custom dimensions."""
        printer = PolonoP31S(width_mm=20, height_mm=50, gap_mm=3, density=10)
        assert printer.width_mm == 20
        assert printer.height_mm == 50
        assert printer.gap_mm == 3
        assert printer.density == 10
        assert printer.width_px == 160  # 20 * 8
        assert printer.height_px == 400  # 50 * 8

    def test_density_clamping(self):
        """Test density is clamped to valid range."""
        printer_low = PolonoP31S(density=0)
        printer_high = PolonoP31S(density=20)
        assert printer_low.density == 1
        assert printer_high.density == 15

    def test_render_text_returns_image(self):
        """Test text rendering returns a valid image."""
        printer = PolonoP31S()
        img = printer.render_text("Test", font_size=24)
        assert isinstance(img, Image.Image)
        assert img.mode == '1'  # 1-bit image
        assert img.size == (printer.height_px, printer.width_px)  # Landscape

    def test_check_text_fit(self):
        """Test text fit checking."""
        printer = PolonoP31S()
        fit = printer.check_text_fit("Test", font_size=24)
        assert 'fits' in fit
        assert 'text_width' in fit
        assert 'text_height' in fit
        assert 'label_width' in fit
        assert 'label_height' in fit
        assert 'overflow_x' in fit
        assert 'overflow_y' in fit

    def test_find_fitting_font_size(self):
        """Test auto-fit font size finding."""
        printer = PolonoP31S()
        size = printer.find_fitting_font_size("Test", max_font_size=200)
        assert isinstance(size, int)
        assert size >= 8
        assert size <= 200

    def test_render_image(self, tmp_path):
        """Test image rendering."""
        # Create a test image
        test_img = Image.new('RGB', (100, 100), color='white')
        img_path = tmp_path / "test.png"
        test_img.save(img_path)

        printer = PolonoP31S()
        result = printer.render_image(str(img_path))
        assert isinstance(result, Image.Image)
        assert result.mode == '1'

    def test_image_to_bitmap(self):
        """Test bitmap conversion."""
        printer = PolonoP31S()
        img = Image.new('1', (320, 112), color=1)  # White image
        width_bytes, height, bitmap_data = printer._image_to_bitmap(img)
        assert width_bytes > 0
        assert height > 0
        assert len(bitmap_data) == width_bytes * height

    def test_build_print_command(self):
        """Test TSPL command building."""
        printer = PolonoP31S()
        img = printer.render_text("Test", font_size=24)
        cmd = printer._build_print_command(img)
        assert b'SIZE' in cmd
        assert b'GAP' in cmd
        assert b'DENSITY' in cmd
        assert b'BITMAP' in cmd
        assert b'PRINT 1' in cmd

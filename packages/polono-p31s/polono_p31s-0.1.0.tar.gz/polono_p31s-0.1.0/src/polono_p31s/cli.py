#!/usr/bin/env python3
"""
Polono P31S Thermal Label Printer CLI

A command-line tool to print labels on Polono P31S thermal printers via Bluetooth.
Uses TSPL (Taiwan Semiconductor Programming Language) commands over BLE.

Usage:
    polono text "Hello World"
    polono qr "https://example.com"
    polono image logo.png
"""

import asyncio
import logging

import click
from rich.console import Console
from rich.logging import RichHandler

from .printer import PolonoP31S, save_preview

console = Console()


def setup_cli_logging(verbose: bool = False):
    """Configure rich logging for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=False,
            show_path=False,
        )]
    )


# CLI Interface
@click.group()
@click.option('--width', '-w', default=14.0, help='Label width in mm')
@click.option('--height', '-h', default=40.0, help='Label height in mm')
@click.option('--density', '-d', default=15, help='Print density (1-15)')
@click.option('--address', '-a', default=None, help='BLE address (skip scanning)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, width, height, density, address, verbose):
    """Polono P31S Thermal Label Printer CLI (BLE)"""
    setup_cli_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj['width'] = width
    ctx.obj['height'] = height
    ctx.obj['density'] = density
    ctx.obj['address'] = address


@cli.command()
@click.argument('text')
@click.option('--copies', '-c', default=1, help='Number of copies')
@click.option('--font-size', '-s', default=48, help='Font size in points')
@click.option('--font', '-f', default=None, help='Path to TTF font file')
@click.option('--align', type=click.Choice(['left', 'center', 'right']), default='center', help='Text alignment')
@click.option('--force', is_flag=True, help='Print even if text overflows')
@click.option('--autofit', is_flag=True, help='Automatically shrink font to fit')
@click.option('--preview', is_flag=True, help='Save preview image instead of printing')
@click.pass_context
def text(ctx, text, copies, font_size, font, align, force, autofit, preview):
    """Print text label."""
    # Convert literal \n to actual newlines for multi-line text
    text = text.replace('\\n', '\n')
    
    printer = PolonoP31S(
        width_mm=ctx.obj['width'],
        height_mm=ctx.obj['height'],
        density=ctx.obj['density'],
    )
    
    # Check if text fits
    fit = printer.check_text_fit(text, font_size=font_size, font_path=font)
    
    noprint = False
    if not fit['fits']:
        if autofit:
            # Find the largest font size that fits
            font_size = printer.find_fitting_font_size(text, max_font_size=font_size, font_path=font)
            fit = printer.check_text_fit(text, font_size=font_size, font_path=font)
            console.print(f"[cyan]Autofit:[/cyan] reduced font size to {font_size}pt")
            console.print(f"[green]✓[/green] Text fits ({fit['text_width']}×{fit['text_height']} px)")
        else:
            console.print("[yellow]⚠ Text may be clipped![/yellow]")
            console.print(f"  Text size: {fit['text_width']}×{fit['text_height']} px")
            console.print(f"  Label size: {fit['label_width']}×{fit['label_height']} px")
            if fit['overflow_x'] > 0:
                console.print(f"  [red]→ Overflows by {fit['overflow_x']}px horizontally[/red]")
            if fit['overflow_y'] > 0:
                console.print(f"  [red]→ Overflows by {fit['overflow_y']}px vertically (try smaller font)[/red]")
            
            if not force:
                console.print("\n  [dim]Suggestions:[/dim]")
                # Calculate suggested font size
                suggested_x = int(font_size * fit['label_width'] / fit['text_width'])
                suggested_y = int(font_size * fit['label_height'] / fit['text_height'])
                suggested = min(suggested_x, suggested_y)
                if fit['overflow_x'] > 0 or fit['overflow_y'] > 0:
                    console.print(f"    • Try --font-size {suggested} (or smaller)")
                console.print("    • Use --autofit to automatically shrink font")
                console.print("    • Use --force to print anyway (text will be clipped)")
                console.print("    • Use --preview to see what it looks like")
                noprint = True
            elif not preview:
                console.print("  [dim]Printing anyway (--force)[/dim]\n")
    else:
        console.print(f"[green]✓[/green] Text fits ({fit['text_width']}×{fit['text_height']} px)")
    
    # Generate preview instead of printing
    if preview:
        img = printer.render_text(text, font_size=font_size, font_path=font, align=align)
        save_preview(img, "preview.png")
        return
    
    if noprint:
        raise SystemExit(1)

    # Render the image
    img = printer.render_text(text, font_size=font_size, font_path=font, align=align)
    
    async def _print():
        if not await printer.connect_ble(ctx.obj['address']):
            raise SystemExit(1)
        
        try:
            # Show text with newlines as ↵ for display
            display_text = text.replace('\n', '↵')
            console.print(f"[cyan]Printing '{display_text}'...[/cyan]")
            await printer.print_ble(img, copies=copies)
            console.print("[green]✓ Done![/green]")
        finally:
            await printer.disconnect_ble()
    
    asyncio.run(_print())


@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--copies', '-c', default=1, help='Number of copies')
@click.option('--preview', is_flag=True, help='Save preview image instead of printing')
@click.pass_context
def image(ctx, image_path, copies, preview):
    """Print image label."""
    printer = PolonoP31S(
        width_mm=ctx.obj['width'],
        height_mm=ctx.obj['height'],
        density=ctx.obj['density'],
    )
    
    # Render the image
    img = printer.render_image(image_path)
    
    # Generate preview instead of printing
    if preview:
        save_preview(img, "preview.png")
        return
    
    async def _print():
        if not await printer.connect_ble(ctx.obj['address']):
            raise SystemExit(1)
        
        try:
            console.print("[cyan]Printing image...[/cyan]")
            await printer.print_ble(img, copies=copies)
            console.print("[green]✓ Done![/green]")
        finally:
            await printer.disconnect_ble()
    
    asyncio.run(_print())


@cli.command()
@click.argument('data')
@click.option('--copies', '-c', default=1, help='Number of copies')
@click.option('--preview', is_flag=True, help='Save preview image instead of printing')
@click.pass_context
def qr(ctx, data, copies, preview):
    """Print QR code label."""
    printer = PolonoP31S(
        width_mm=ctx.obj['width'],
        height_mm=ctx.obj['height'],
        density=ctx.obj['density'],
    )
    
    # Render QR code
    img = printer.render_qr(data)
    if img is None:
        return
    
    # Generate preview instead of printing
    if preview:
        save_preview(img, "preview.png")
        return
    
    async def _print():
        if not await printer.connect_ble(ctx.obj['address']):
            raise SystemExit(1)
        
        try:
            console.print("[cyan]Printing QR code...[/cyan]")
            await printer.print_ble(img, copies=copies)
            console.print("[green]✓ Done![/green]")
        finally:
            await printer.disconnect_ble()
    
    asyncio.run(_print())


@cli.command()
@click.argument('data')
@click.option('--copies', '-c', default=1, help='Number of copies')
@click.option('--type', '-t', 'barcode_type', default='code128', help='Barcode type')
@click.option('--preview', is_flag=True, help='Save preview image instead of printing')
@click.pass_context
def barcode(ctx, data, copies, barcode_type, preview):
    """Print barcode label."""
    printer = PolonoP31S(
        width_mm=ctx.obj['width'],
        height_mm=ctx.obj['height'],
        density=ctx.obj['density'],
    )
    
    # Render barcode
    img = printer.render_barcode(data, barcode_type=barcode_type)
    if img is None:
        return
    
    # Generate preview instead of printing
    if preview:
        save_preview(img, "preview.png")
        return
    
    async def _print():
        if not await printer.connect_ble(ctx.obj['address']):
            raise SystemExit(1)
        
        try:
            console.print("[cyan]Printing barcode...[/cyan]")
            await printer.print_ble(img, copies=copies)
            console.print("[green]✓ Done![/green]")
        finally:
            await printer.disconnect_ble()
    
    asyncio.run(_print())


@cli.command()
@click.pass_context
def status(ctx):
    """Query printer status."""
    async def _status():
        printer = PolonoP31S()
        
        if not await printer.connect_ble(ctx.obj['address']):
            raise SystemExit(1)
        
        try:
            response = await printer.get_status_ble()
            if response:
                console.print(f"[cyan]Status:[/cyan] {response}")
            else:
                console.print("[yellow]No response from printer[/yellow]")
        finally:
            await printer.disconnect_ble()
    
    asyncio.run(_status())


@cli.command()
def scan():
    """Scan for Bluetooth printers (BLE scan, requires bleak)."""
    import asyncio
    
    async def do_scan():
        try:
            from bleak import BleakScanner
        except ImportError:
            console.print("[red]Error:[/red] bleak library required for scanning")
            console.print("Install with: pip install bleak")
            return
        
        console.print("[cyan]Scanning for Bluetooth devices...[/cyan]")
        devices = await BleakScanner.discover(timeout=10.0)
        
        console.print(f"\n[green]Found {len(devices)} devices:[/green]\n")
        for d in devices:
            name = d.name or "(unknown)"
            # Highlight potential printers
            if any(x in name.lower() for x in ['polo', 'print', 'p31', 'label']):
                console.print(f"  [bold green]★ {d.address}[/bold green] - {name}")
            else:
                console.print(f"  {d.address} - {name}")
    
    asyncio.run(do_scan())


if __name__ == '__main__':
    cli()

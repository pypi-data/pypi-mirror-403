#!/usr/bin/python3
"""
mk2pdf - Markdown to PDF Converter CLI

A CLI tool that converts Markdown files to beautiful PDF documents with
Mermaid diagram support and syntax highlighting.

This tool uses mk2html to generate HTML first, then uses Playwright to
render the HTML and export it as PDF with full JavaScript execution
(required for Mermaid diagrams and syntax highlighting).

Features:
- All mk2html features (TOC, styling, Mermaid, syntax highlighting)
- High-quality PDF output with proper rendering
- Mermaid diagrams fully rendered
- Syntax highlighting preserved
- Configurable page size and margins

Usage:
    mk2pdf <input.md> [options]
    mk2pdf --help
    mk2pdf --version

Examples:
    mk2pdf README.md
    mk2pdf docs.md -o documentation.pdf
    mk2pdf guide.md --title "User Guide"
    mk2pdf report.md --theme light --page-size letter

Requirements:
    pip install playwright
    playwright install chromium
"""

__version__ = "1.1.0"
__author__ = "Kinshuk"

import sys
import argparse
import tempfile
import time
from pathlib import Path
from typing import Optional, List

# Import mk2html converter
try:
    from mk2html import (
        convert_markdown_to_html,
        get_offline_libraries,
        __version__ as mk2html_version
    )
except ImportError:
    # Try importing from same directory
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mk2html import (
        convert_markdown_to_html,
        get_offline_libraries,
        __version__ as mk2html_version
    )

# Check for Playwright
PLAYWRIGHT_AVAILABLE = False
CHROMIUM_INSTALLED = False
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    
    # Check if Chromium is installed by looking for the executable
    import subprocess
    result = subprocess.run(
        ['playwright', 'install', '--dry-run', 'chromium'],
        capture_output=True,
        text=True
    )
    # If dry-run succeeds without mentioning download, it's installed
    CHROMIUM_INSTALLED = 'chromium' not in result.stdout.lower() or result.returncode == 0
except ImportError:
    pass
except Exception:
    # If we can't check, assume it might be installed
    CHROMIUM_INSTALLED = True


def ensure_chromium_installed(quiet: bool = False) -> bool:
    """Ensure Chromium is installed for Playwright. Returns True if successful."""
    if not PLAYWRIGHT_AVAILABLE:
        return False
    
    try:
        # Try to launch browser to check if it's installed
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if 'executable doesn' in error_msg or 'browser' in error_msg:
            # Chromium not installed, try to install it
            if not quiet:
                print("Chromium not found. Installing automatically...", file=sys.stderr)
                print("(This is a one-time setup, ~150MB download)", file=sys.stderr)
            
            import subprocess
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'playwright', 'install', 'chromium'],
                    capture_output=not quiet,
                    text=True
                )
                if result.returncode == 0:
                    if not quiet:
                        print("✓ Chromium installed successfully!", file=sys.stderr)
                    return True
                else:
                    if not quiet:
                        print(f"Failed to install Chromium: {result.stderr}", file=sys.stderr)
                    return False
            except Exception as install_error:
                if not quiet:
                    print(f"Failed to install Chromium: {install_error}", file=sys.stderr)
                    print("Please run manually: playwright install chromium", file=sys.stderr)
                return False
        else:
            # Some other error
            if not quiet:
                print(f"Browser error: {e}", file=sys.stderr)
            return False


# =============================================================================
# PDF Conversion
# =============================================================================

def convert_html_to_pdf(
    html_content: str,
    output_path: Path,
    page_size: str = "a4",
    margin: str = "1in",
    landscape: bool = False,
    wait_time: int = 2000,
    quiet: bool = False
) -> bool:
    """Convert HTML content to PDF using Playwright.
    
    Args:
        html_content: The HTML content to convert
        output_path: Path to save the PDF
        page_size: Page size (a4, letter, legal, tabloid)
        margin: Page margin (e.g., "1in", "2cm", "20mm")
        landscape: Use landscape orientation
        wait_time: Time to wait for JS execution (ms)
        quiet: Suppress output messages
    
    Returns:
        True if successful, False otherwise
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("Error: Playwright is required for PDF export.", file=sys.stderr)
        print("Install it with:", file=sys.stderr)
        print("  pip install playwright", file=sys.stderr)
        print("  playwright install chromium", file=sys.stderr)
        return False
    
    # Page size dimensions (in inches)
    page_sizes = {
        'a4': {'width': '8.27in', 'height': '11.69in'},
        'letter': {'width': '8.5in', 'height': '11in'},
        'legal': {'width': '8.5in', 'height': '14in'},
        'tabloid': {'width': '11in', 'height': '17in'},
        'a3': {'width': '11.69in', 'height': '16.54in'},
        'a5': {'width': '5.83in', 'height': '8.27in'},
    }
    
    page_dims = page_sizes.get(page_size.lower(), page_sizes['a4'])
    
    if landscape:
        page_dims['width'], page_dims['height'] = page_dims['height'], page_dims['width']
    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_html_path = f.name
    
    try:
        if not quiet:
            print("  Launching browser...", file=sys.stderr)
        
        with sync_playwright() as p:
            # Launch headless browser
            browser = p.chromium.launch(headless=True)
            
            # Create page with appropriate viewport
            page = browser.new_page(
                viewport={'width': 1200, 'height': 800}
            )
            
            # Navigate to the HTML file
            if not quiet:
                print("  Loading HTML...", file=sys.stderr)
            
            page.goto(f'file://{temp_html_path}', wait_until='networkidle')
            
            # Wait for Mermaid diagrams and syntax highlighting to render
            if not quiet:
                print(f"  Waiting for JS rendering ({wait_time}ms)...", file=sys.stderr)
            
            page.wait_for_timeout(wait_time)
            
            # Additional wait for mermaid specifically
            try:
                page.wait_for_function(
                    """() => {
                        const mermaids = document.querySelectorAll('.mermaid');
                        if (mermaids.length === 0) return true;
                        return Array.from(mermaids).every(m => m.querySelector('svg'));
                    }""",
                    timeout=10000
                )
            except Exception:
                # Continue even if mermaid wait times out
                pass
            
            # Inject print-specific CSS to improve PDF output
            page.add_style_tag(content="""
                @media print {
                    /* Hide interactive elements */
                    .header, .sidebar, .theme-toggle, .back-to-top, 
                    .progress-bar, .sidebar-toggle {
                        display: none !important;
                    }
                    
                    /* Reset layout for print */
                    .layout {
                        display: block !important;
                        margin-top: 0 !important;
                    }
                    
                    .main {
                        margin-left: 0 !important;
                        max-width: 100% !important;
                        padding: 0 !important;
                    }
                    
                    /* Ensure proper colors */
                    body {
                        background: white !important;
                        color: #1e293b !important;
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }
                    
                    /* Preserve code block styling */
                    pre {
                        background: #1e293b !important;
                        color: #e2e8f0 !important;
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                        page-break-inside: avoid;
                    }
                    
                    /* Preserve mermaid diagrams */
                    .mermaid {
                        background: white !important;
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                        page-break-inside: avoid;
                    }
                    
                    /* Preserve table styling */
                    table, th, td {
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }
                    
                    th {
                        background: #f1f5f9 !important;
                    }
                    
                    /* Avoid page breaks in awkward places */
                    h1, h2, h3, h4, h5, h6 {
                        page-break-after: avoid;
                    }
                    
                    img, table, pre, blockquote {
                        page-break-inside: avoid;
                    }
                    
                    /* Syntax highlighting colors */
                    .hljs-keyword, .hljs-tag { color: #d73a49 !important; }
                    .hljs-string, .hljs-title { color: #22863a !important; }
                    .hljs-comment { color: #6a737d !important; }
                    .hljs-number { color: #005cc5 !important; }
                    .hljs-function { color: #6f42c1 !important; }
                }
            """)
            
            # Generate PDF
            if not quiet:
                print("  Generating PDF...", file=sys.stderr)
            
            page.pdf(
                path=str(output_path),
                format=page_size.upper() if page_size.lower() in ['a4', 'a3', 'a5'] else None,
                width=page_dims['width'] if page_size.lower() not in ['a4', 'a3', 'a5'] else None,
                height=page_dims['height'] if page_size.lower() not in ['a4', 'a3', 'a5'] else None,
                margin={
                    'top': margin,
                    'right': margin,
                    'bottom': margin,
                    'left': margin
                },
                print_background=True,
                landscape=landscape
            )
            
            browser.close()
        
        return True
        
    except Exception as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        return False
        
    finally:
        # Clean up temp file
        try:
            Path(temp_html_path).unlink()
        except Exception:
            pass


def convert_markdown_to_pdf(
    markdown_text: str,
    output_path: Path,
    title: str = "Document",
    enable_mermaid: bool = True,
    theme: str = "light",
    page_size: str = "a4",
    margin: str = "1in",
    landscape: bool = False,
    wait_time: int = 2000,
    quiet: bool = False,
    enable_line_numbers: bool = True,
    enable_breaks: bool = True
) -> bool:
    """Convert markdown text to PDF.
    
    Args:
        markdown_text: The markdown content to convert
        output_path: Path to save the PDF
        title: Document title
        enable_mermaid: Whether to include Mermaid diagram support
        theme: Theme for rendering ('light' or 'dark')
        page_size: Page size (a4, letter, legal, tabloid)
        margin: Page margin
        landscape: Use landscape orientation
        wait_time: Time to wait for JS execution (ms)
        quiet: Suppress output messages
        enable_line_numbers: Whether to show line numbers in code blocks
        enable_breaks: Whether to treat newlines as <br> tags
    
    Returns:
        True if successful, False otherwise
    """
    if not quiet:
        print("Converting Markdown to HTML...", file=sys.stderr)
    
    # Always use offline mode for PDF to ensure resources are available
    offline_libs = get_offline_libraries(quiet=True)
    
    # Convert markdown to HTML
    html_content = convert_markdown_to_html(
        markdown_text,
        title=title,
        enable_mermaid=enable_mermaid,
        default_theme=theme,
        offline_libs=offline_libs,
        enable_line_numbers=enable_line_numbers,
        enable_breaks=enable_breaks
    )
    
    if not quiet:
        print("Converting HTML to PDF...", file=sys.stderr)
    
    # Convert HTML to PDF
    return convert_html_to_pdf(
        html_content,
        output_path,
        page_size=page_size,
        margin=margin,
        landscape=landscape,
        wait_time=wait_time,
        quiet=quiet
    )


# =============================================================================
# CLI Interface
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog='mk2pdf',
        description='Convert Markdown to PDF with Mermaid diagrams and syntax highlighting.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s README.md                          # Basic conversion
  %(prog)s docs.md -o documentation.pdf       # Specify output file
  %(prog)s guide.md --title "User Guide"      # Custom title
  %(prog)s report.md --page-size letter       # US Letter size
  %(prog)s wide.md --landscape                # Landscape orientation
  %(prog)s spec.md --no-mermaid               # Disable Mermaid support
  %(prog)s input.md --margin 0.5in            # Custom margins

Requirements:
  pip install playwright
  playwright install chromium

For more information, visit: https://github.com/your-repo/mk2html
        '''
    )
    
    parser.add_argument(
        'input',
        metavar='INPUT',
        nargs='?',
        help='Input Markdown file'
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Output PDF file (default: input filename with .pdf extension)'
    )
    
    parser.add_argument(
        '-t', '--title',
        metavar='TITLE',
        help='Document title (default: filename without extension)'
    )
    
    parser.add_argument(
        '--theme',
        choices=['light', 'dark'],
        default='light',
        help='Theme for rendering (default: light)'
    )
    
    parser.add_argument(
        '--no-mermaid',
        action='store_true',
        help='Disable Mermaid diagram support'
    )
    
    parser.add_argument(
        '--no-line-numbers',
        action='store_true',
        help='Disable line numbers in code blocks'
    )
    
    parser.add_argument(
        '--no-breaks',
        action='store_true',
        help='Disable treating newlines as <br> tags (standard Markdown behavior)'
    )
    
    parser.add_argument(
        '--page-size',
        choices=['a4', 'a3', 'a5', 'letter', 'legal', 'tabloid'],
        default='a4',
        help='Page size (default: a4)'
    )
    
    parser.add_argument(
        '--margin',
        default='1in',
        help='Page margin (default: 1in). Supports: in, cm, mm, px'
    )
    
    parser.add_argument(
        '--landscape',
        action='store_true',
        help='Use landscape orientation'
    )
    
    parser.add_argument(
        '--wait',
        type=int,
        default=2000,
        metavar='MS',
        help='Wait time for JS rendering in milliseconds (default: 2000)'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output messages'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__} (using mk2html {mk2html_version})'
    )
    
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    opts = parser.parse_args(args)
    
    # Check for Playwright
    if not PLAYWRIGHT_AVAILABLE:
        print("Error: Playwright is required for PDF export.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Install it with:", file=sys.stderr)
        print("  pip install 'mk2html[pdf]'", file=sys.stderr)
        print("", file=sys.stderr)
        print("Or manually:", file=sys.stderr)
        print("  pip install playwright", file=sys.stderr)
        return 1
    
    # Ensure Chromium is installed (auto-install if needed)
    if not ensure_chromium_installed(quiet=opts.quiet if hasattr(opts, 'quiet') else False):
        print("Error: Chromium browser is required but could not be installed.", file=sys.stderr)
        print("Please run manually: playwright install chromium", file=sys.stderr)
        return 1
    
    # Require input
    if not opts.input:
        parser.error("the following arguments are required: INPUT")
    
    # Read input
    input_path = Path(opts.input)
    if not input_path.exists():
        print(f"Error: Input file '{opts.input}' not found.", file=sys.stderr)
        return 1
    
    markdown_text = input_path.read_text(encoding='utf-8')
    input_name = input_path.name
    
    # Determine output file
    if opts.output:
        output_path = Path(opts.output)
    else:
        output_path = Path(opts.input).with_suffix('.pdf')
    
    # Determine title
    if opts.title:
        title = opts.title
    else:
        title = Path(opts.input).stem.replace('-', ' ').replace('_', ' ').title()
    
    if not opts.quiet:
        print(f"Converting '{input_name}' to PDF...", file=sys.stderr)
    
    # Convert
    success = convert_markdown_to_pdf(
        markdown_text,
        output_path,
        title=title,
        enable_mermaid=not opts.no_mermaid,
        theme=opts.theme,
        page_size=opts.page_size,
        margin=opts.margin,
        landscape=opts.landscape,
        wait_time=opts.wait,
        quiet=opts.quiet,
        enable_line_numbers=not opts.no_line_numbers,
        enable_breaks=not opts.no_breaks
    )
    
    if not success:
        return 1
    
    if not opts.quiet:
        file_size = output_path.stat().st_size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / 1024 / 1024:.1f} MB"
        
        print(f"✓ Successfully converted '{input_name}' to '{output_path}'")
        print(f"  Title: {title}")
        print(f"  Page size: {opts.page_size.upper()}")
        print(f"  Orientation: {'landscape' if opts.landscape else 'portrait'}")
        print(f"  Mermaid: {'enabled' if not opts.no_mermaid else 'disabled'}")
        print(f"  Line numbers: {'enabled' if not opts.no_line_numbers else 'disabled'}")
        print(f"  Line breaks: {'enabled' if not opts.no_breaks else 'disabled'}")
        print(f"  Size: {size_str}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

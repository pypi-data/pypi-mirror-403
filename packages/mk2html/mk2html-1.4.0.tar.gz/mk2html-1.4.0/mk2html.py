#!/usr/bin/python3
"""
mk2html - Markdown to HTML Converter CLI

A powerful CLI tool that converts Markdown files to beautiful, interactive HTML
with Table of Contents, Dark/Light mode, Mermaid diagram support, and more.

Features:
- Auto-generated table of contents from headings
- Beautiful, modern styling with CSS variables
- Dark/Light mode toggle with persistence
- Mermaid diagram rendering
- Responsive design
- Smooth scrolling navigation
- Code syntax highlighting
- Progress bar and back-to-top button

Usage:
    mk2html <input.md> [options]
    mk2html --help
    mk2html --version

Examples:
    mk2html README.md
    mk2html docs.md -o documentation.html
    mk2html guide.md --title "User Guide" --no-mermaid
    mk2html report.md -o report.html --theme dark
"""

__version__ = "1.4.0"
__author__ = "Kinshuk"

import re
import sys
import argparse
import hashlib
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Dict

try:
    import markdown
    from markdown.extensions.toc import TocExtension
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.tables import TableExtension
    from markdown.extensions.codehilite import CodeHiliteExtension
except ImportError:
    print("Error: 'markdown' package is required.")
    print("Install it with: pip install markdown")
    sys.exit(1)

# Check for PDF export capability (optional)
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# Offline Mode - Library Caching
# =============================================================================

# CDN URLs for external libraries
MERMAID_CDN_URL = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"
HIGHLIGHTJS_CDN_URL = "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"

# Default cache directory
CACHE_DIR = Path.home() / ".cache" / "mk2html"


def get_cache_path(url: str) -> Path:
    """Get the cache file path for a given URL."""
    # Use URL hash as filename to avoid path issues
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    filename = url.split("/")[-1]
    return CACHE_DIR / f"{url_hash}_{filename}"


def download_and_cache(url: str, quiet: bool = False) -> Optional[str]:
    """Download a file from URL and cache it locally. Returns the content."""
    cache_path = get_cache_path(url)
    
    # Check if already cached
    if cache_path.exists():
        return cache_path.read_text(encoding='utf-8')
    
    # Create cache directory if needed
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    if not quiet:
        print(f"  Downloading {url.split('/')[-1]}...", file=sys.stderr)
    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'mk2html/1.1.0'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            cache_path.write_text(content, encoding='utf-8')
            return content
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        if not quiet:
            print(f"  Warning: Failed to download {url}: {e}", file=sys.stderr)
        return None


def get_offline_libraries(quiet: bool = False) -> Dict[str, Optional[str]]:
    """Download and cache all required libraries for offline mode."""
    if not quiet:
        print("Preparing offline mode (downloading libraries)...", file=sys.stderr)
    
    return {
        'mermaid': download_and_cache(MERMAID_CDN_URL, quiet),
        'highlightjs': download_and_cache(HIGHLIGHTJS_CDN_URL, quiet),
    }


def clear_cache() -> int:
    """Clear the library cache. Returns number of files removed."""
    if not CACHE_DIR.exists():
        return 0
    
    count = 0
    for f in CACHE_DIR.iterdir():
        if f.is_file():
            f.unlink()
            count += 1
    
    return count


# =============================================================================
# HTML Template
# =============================================================================

def get_html_template(
    enable_mermaid: bool = True,
    default_theme: str = "light",
    offline_libs: Optional[Dict[str, Optional[str]]] = None,
    enable_line_numbers: bool = True
) -> str:
    """Return the complete HTML template with embedded CSS and JavaScript.
    
    Args:
        enable_mermaid: Whether to include Mermaid diagram support
        default_theme: Default theme ('light' or 'dark')
        offline_libs: Dictionary with 'mermaid' and 'highlightjs' content for offline mode
        enable_line_numbers: Whether to show line numbers in code blocks
    """
    
    # Determine if we're in offline mode
    is_offline = offline_libs is not None
    
    # Build Mermaid script section
    if enable_mermaid:
        if is_offline and offline_libs.get('mermaid'):
            mermaid_script_tag = f'''
    <!-- Mermaid.js (embedded for offline use) -->
    <script>
{offline_libs['mermaid']}
    </script>'''
        else:
            mermaid_script_tag = '''
    <!-- Mermaid.js for diagram rendering -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'''
        
        mermaid_script = mermaid_script_tag + '''
    <script>
        // Beautiful custom Mermaid themes
        const mermaidLightTheme = {
            theme: 'base',
            themeVariables: {
                // General
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: '14px',
                
                // Background colors
                primaryColor: '#dbeafe',
                primaryBorderColor: '#3b82f6',
                primaryTextColor: '#1e293b',
                secondaryColor: '#f0fdf4',
                secondaryBorderColor: '#22c55e',
                secondaryTextColor: '#1e293b',
                tertiaryColor: '#fef3c7',
                tertiaryBorderColor: '#f59e0b',
                tertiaryTextColor: '#1e293b',
                
                // Lines and arrows
                lineColor: '#64748b',
                textColor: '#1e293b',
                
                // Flowchart
                nodeBorder: '#3b82f6',
                clusterBkg: '#f1f5f9',
                clusterBorder: '#cbd5e1',
                defaultLinkColor: '#64748b',
                edgeLabelBackground: '#ffffff',
                
                // Sequence diagram
                actorBkg: '#dbeafe',
                actorBorder: '#3b82f6',
                actorTextColor: '#1e293b',
                actorLineColor: '#64748b',
                signalColor: '#1e293b',
                signalTextColor: '#1e293b',
                labelBoxBkgColor: '#f8fafc',
                labelBoxBorderColor: '#e2e8f0',
                labelTextColor: '#1e293b',
                loopTextColor: '#1e293b',
                noteBkgColor: '#fef3c7',
                noteBorderColor: '#f59e0b',
                noteTextColor: '#1e293b',
                activationBkgColor: '#dbeafe',
                activationBorderColor: '#3b82f6',
                sequenceNumberColor: '#ffffff',
                
                // State diagram
                labelColor: '#1e293b',
                altBackground: '#f8fafc',
                
                // Class diagram
                classText: '#1e293b',
                
                // Gantt
                gridColor: '#e2e8f0',
                todayLineColor: '#ef4444',
                taskBkgColor: '#dbeafe',
                taskBorderColor: '#3b82f6',
                taskTextColor: '#1e293b',
                taskTextDarkColor: '#1e293b',
                taskTextOutsideColor: '#1e293b',
                activeTaskBkgColor: '#bfdbfe',
                activeTaskBorderColor: '#2563eb',
                doneTaskBkgColor: '#bbf7d0',
                doneTaskBorderColor: '#22c55e',
                critBkgColor: '#fecaca',
                critBorderColor: '#ef4444',
                sectionBkgColor: '#f1f5f9',
                sectionBkgColor2: '#e2e8f0',
                
                // Pie
                pie1: '#3b82f6',
                pie2: '#22c55e',
                pie3: '#f59e0b',
                pie4: '#ef4444',
                pie5: '#8b5cf6',
                pie6: '#06b6d4',
                pie7: '#ec4899',
                pie8: '#84cc16',
                pie9: '#f97316',
                pie10: '#6366f1',
                pie11: '#14b8a6',
                pie12: '#a855f7',
                pieStrokeColor: '#ffffff',
                pieStrokeWidth: '2px',
                pieOpacity: '0.9',
                pieTitleTextColor: '#1e293b',
                pieSectionTextColor: '#ffffff',
                pieLegendTextColor: '#1e293b',
                
                // Git
                git0: '#3b82f6',
                git1: '#22c55e',
                git2: '#f59e0b',
                git3: '#ef4444',
                git4: '#8b5cf6',
                git5: '#06b6d4',
                git6: '#ec4899',
                git7: '#84cc16',
                gitBranchLabel0: '#ffffff',
                gitBranchLabel1: '#ffffff',
                gitBranchLabel2: '#ffffff',
                gitBranchLabel3: '#ffffff',
                commitLabelColor: '#1e293b',
                commitLabelBackground: '#f8fafc'
            }
        };
        
        const mermaidDarkTheme = {
            theme: 'base',
            themeVariables: {
                // General
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: '14px',
                
                // Background colors
                primaryColor: '#1e3a5f',
                primaryBorderColor: '#60a5fa',
                primaryTextColor: '#f1f5f9',
                secondaryColor: '#14532d',
                secondaryBorderColor: '#4ade80',
                secondaryTextColor: '#f1f5f9',
                tertiaryColor: '#451a03',
                tertiaryBorderColor: '#fbbf24',
                tertiaryTextColor: '#f1f5f9',
                
                // Lines and arrows
                lineColor: '#94a3b8',
                textColor: '#f1f5f9',
                
                // Flowchart
                nodeBorder: '#60a5fa',
                clusterBkg: '#1e293b',
                clusterBorder: '#475569',
                defaultLinkColor: '#94a3b8',
                edgeLabelBackground: '#0f172a',
                
                // Sequence diagram
                actorBkg: '#1e3a5f',
                actorBorder: '#60a5fa',
                actorTextColor: '#f1f5f9',
                actorLineColor: '#94a3b8',
                signalColor: '#f1f5f9',
                signalTextColor: '#f1f5f9',
                labelBoxBkgColor: '#1e293b',
                labelBoxBorderColor: '#334155',
                labelTextColor: '#f1f5f9',
                loopTextColor: '#f1f5f9',
                noteBkgColor: '#451a03',
                noteBorderColor: '#fbbf24',
                noteTextColor: '#f1f5f9',
                activationBkgColor: '#1e3a5f',
                activationBorderColor: '#60a5fa',
                sequenceNumberColor: '#f1f5f9',
                
                // State diagram
                labelColor: '#f1f5f9',
                altBackground: '#1e293b',
                
                // Class diagram
                classText: '#f1f5f9',
                
                // Gantt
                gridColor: '#334155',
                todayLineColor: '#f87171',
                taskBkgColor: '#1e3a5f',
                taskBorderColor: '#60a5fa',
                taskTextColor: '#f1f5f9',
                taskTextDarkColor: '#f1f5f9',
                taskTextOutsideColor: '#f1f5f9',
                activeTaskBkgColor: '#2563eb',
                activeTaskBorderColor: '#93c5fd',
                doneTaskBkgColor: '#14532d',
                doneTaskBorderColor: '#4ade80',
                critBkgColor: '#7f1d1d',
                critBorderColor: '#f87171',
                sectionBkgColor: '#1e293b',
                sectionBkgColor2: '#334155',
                
                // Pie
                pie1: '#60a5fa',
                pie2: '#4ade80',
                pie3: '#fbbf24',
                pie4: '#f87171',
                pie5: '#a78bfa',
                pie6: '#22d3ee',
                pie7: '#f472b6',
                pie8: '#a3e635',
                pie9: '#fb923c',
                pie10: '#818cf8',
                pie11: '#2dd4bf',
                pie12: '#c084fc',
                pieStrokeColor: '#0f172a',
                pieStrokeWidth: '2px',
                pieOpacity: '0.9',
                pieTitleTextColor: '#f1f5f9',
                pieSectionTextColor: '#0f172a',
                pieLegendTextColor: '#f1f5f9',
                
                // Git
                git0: '#60a5fa',
                git1: '#4ade80',
                git2: '#fbbf24',
                git3: '#f87171',
                git4: '#a78bfa',
                git5: '#22d3ee',
                git6: '#f472b6',
                git7: '#a3e635',
                gitBranchLabel0: '#0f172a',
                gitBranchLabel1: '#0f172a',
                gitBranchLabel2: '#0f172a',
                gitBranchLabel3: '#0f172a',
                commitLabelColor: '#f1f5f9',
                commitLabelBackground: '#1e293b'
            }
        };
        
        // Initialize Mermaid with beautiful custom theme
        function initMermaid(theme) {
            const themeConfig = theme === 'dark' ? mermaidDarkTheme : mermaidLightTheme;
            mermaid.initialize({
                startOnLoad: false,
                ...themeConfig,
                securityLevel: 'loose',
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis',
                    padding: 15,
                    nodeSpacing: 50,
                    rankSpacing: 50,
                    diagramPadding: 8
                },
                sequence: {
                    useMaxWidth: true,
                    diagramMarginX: 50,
                    diagramMarginY: 10,
                    actorMargin: 50,
                    width: 150,
                    height: 65,
                    boxMargin: 10,
                    boxTextMargin: 5,
                    noteMargin: 10,
                    messageMargin: 35,
                    mirrorActors: true,
                    bottomMarginAdj: 1,
                    showSequenceNumbers: false
                },
                gantt: {
                    useMaxWidth: true,
                    titleTopMargin: 25,
                    barHeight: 20,
                    barGap: 4,
                    topPadding: 50,
                    leftPadding: 75,
                    gridLineStartPadding: 35,
                    fontSize: 11,
                    sectionFontSize: 11,
                    numberSectionStyles: 4
                },
                pie: {
                    useMaxWidth: true,
                    textPosition: 0.75
                },
                class: {
                    useMaxWidth: true,
                    defaultRenderer: 'dagre-wrapper'
                },
                state: {
                    useMaxWidth: true,
                    dividerMargin: 10,
                    sizeUnit: 5,
                    padding: 8,
                    textHeight: 10,
                    titleShift: -15,
                    noteMargin: 10,
                    forkWidth: 70,
                    forkHeight: 7,
                    miniPadding: 2,
                    fontSizeFactor: 5.02,
                    fontSize: 24,
                    labelHeight: 16,
                    edgeLengthFactor: '20',
                    compositTitleSize: 35,
                    radius: 5
                },
                er: {
                    useMaxWidth: true,
                    diagramPadding: 20,
                    layoutDirection: 'TB',
                    minEntityWidth: 100,
                    minEntityHeight: 75,
                    entityPadding: 15,
                    stroke: 'gray',
                    fill: 'honeydew',
                    fontSize: 12
                }
            });
        }
        
        // Render all mermaid diagrams
        async function renderMermaidDiagrams() {
            const diagrams = document.querySelectorAll('.mermaid');
            for (let i = 0; i < diagrams.length; i++) {
                const element = diagrams[i];
                const graphDefinition = element.getAttribute('data-mermaid-src') || element.textContent;
                element.setAttribute('data-mermaid-src', graphDefinition);
                try {
                    const { svg } = await mermaid.render('mermaid-' + i, graphDefinition);
                    element.innerHTML = svg;
                } catch (error) {
                    console.error('Mermaid rendering error:', error);
                    element.innerHTML = '<pre class="mermaid-error">Diagram Error: ' + error.message + '</pre>';
                }
            }
        }
        
        // Re-render diagrams on theme change
        async function updateMermaidTheme(theme) {
            initMermaid(theme);
            await renderMermaidDiagrams();
        }
        
        // Initial render
        document.addEventListener('DOMContentLoaded', () => {
            const theme = localStorage.getItem('theme') || 'light';
            initMermaid(theme);
            renderMermaidDiagrams();
        });
    </script>
    '''
    else:
        mermaid_script = ''
    
    mermaid_theme_update = "updateMermaidTheme(newTheme);" if enable_mermaid else ""
    
    template = '''<!DOCTYPE html>
<html lang="en" data-theme="DEFAULT_THEME">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="mk2html vVERSION">
    <title>$TITLE$</title>
    <style>
        /* CSS Variables for theming */
        :root {
            --transition-speed: 0.3s;
        }
        
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #1e293b;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --accent-color: #3b82f6;
            --accent-hover: #2563eb;
            --accent-light: #dbeafe;
            --border-color: #e2e8f0;
            --shadow-color: rgba(0, 0, 0, 0.1);
            --code-bg: #1e293b;
            --code-text: #e2e8f0;
            --toc-bg: #f8fafc;
            --toc-active: #3b82f6;
            --table-stripe: #f8fafc;
            --blockquote-border: #3b82f6;
            --blockquote-bg: #f0f9ff;
            --mermaid-bg: #ffffff;
        }
        
        [data-theme="dark"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --accent-color: #60a5fa;
            --accent-hover: #93c5fd;
            --accent-light: #1e3a5f;
            --border-color: #334155;
            --shadow-color: rgba(0, 0, 0, 0.3);
            --code-bg: #0f172a;
            --code-text: #e2e8f0;
            --toc-bg: #1e293b;
            --toc-active: #60a5fa;
            --table-stripe: #1e293b;
            --blockquote-border: #60a5fa;
            --blockquote-bg: #1e293b;
            --mermaid-bg: #1e293b;
        }
        
        /* Reset and base styles */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        html {
            scroll-behavior: smooth;
            scroll-padding-top: 80px;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            transition: background-color var(--transition-speed), color var(--transition-speed);
        }
        
        /* Header */
        .header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 2rem;
            z-index: 1000;
            backdrop-filter: blur(10px);
            transition: all var(--transition-speed);
        }
        
        .header-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 60%;
        }
        
        .header-title .home-link {
            text-decoration: none;
            color: var(--text-primary);
            transition: color var(--transition-speed);
        }
        
        .header-title .home-link:hover {
            color: var(--accent-color);
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        /* Theme Toggle */
        .theme-toggle {
            position: relative;
            width: 60px;
            height: 30px;
            background: var(--bg-tertiary);
            border-radius: 15px;
            cursor: pointer;
            border: 2px solid var(--border-color);
            transition: all var(--transition-speed);
        }
        
        .theme-toggle:hover {
            border-color: var(--accent-color);
        }
        
        .theme-toggle::before {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 22px;
            height: 22px;
            background: var(--accent-color);
            border-radius: 50%;
            transition: transform var(--transition-speed);
        }
        
        [data-theme="dark"] .theme-toggle::before {
            transform: translateX(30px);
        }
        
        .theme-toggle .icon {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
            transition: opacity var(--transition-speed);
        }
        
        .theme-toggle .sun {
            left: 6px;
            opacity: 1;
        }
        
        .theme-toggle .moon {
            right: 6px;
            opacity: 0.5;
        }
        
        [data-theme="dark"] .theme-toggle .sun {
            opacity: 0.5;
        }
        
        [data-theme="dark"] .theme-toggle .moon {
            opacity: 1;
        }
        
        /* Layout */
        .layout {
            display: flex;
            margin-top: 60px;
            min-height: calc(100vh - 60px);
        }
        
        /* Sidebar / TOC */
        .sidebar {
            position: fixed;
            top: 60px;
            left: 0;
            width: 280px;
            height: calc(100vh - 60px);
            background: var(--toc-bg);
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
            padding: 1.5rem;
            transition: all var(--transition-speed);
            z-index: 100;
        }
        
        .sidebar-toggle {
            display: none;
            position: fixed;
            top: 70px;
            left: 10px;
            z-index: 101;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            font-size: 1rem;
        }
        
        .toc-title {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }
        
        .toc {
            list-style: none;
        }
        
        .toc li {
            margin-bottom: 0.5rem;
        }
        
        .toc a {
            display: block;
            color: var(--text-secondary);
            text-decoration: none;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            font-size: 0.9rem;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        
        .toc a:hover {
            color: var(--accent-color);
            background: var(--accent-light);
        }
        
        .toc a.active {
            color: var(--accent-color);
            background: var(--accent-light);
            border-left-color: var(--toc-active);
            font-weight: 500;
        }
        
        .toc .toc-h2 {
            padding-left: 0.75rem;
        }
        
        .toc .toc-h3 {
            padding-left: 1.5rem;
            font-size: 0.85rem;
        }
        
        .toc .toc-h4 {
            padding-left: 2.25rem;
            font-size: 0.8rem;
        }
        
        /* Main Content */
        .main {
            flex: 1;
            margin-left: 280px;
            padding: 2rem 3rem;
            max-width: 900px;
            transition: margin var(--transition-speed);
        }
        
        .content {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary);
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
            line-height: 1.3;
            scroll-margin-top: 80px;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-top: 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border-color);
        }
        
        h2 {
            font-size: 1.875rem;
            padding-bottom: 0.25rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        h3 { font-size: 1.5rem; }
        h4 { font-size: 1.25rem; }
        h5 { font-size: 1.125rem; }
        h6 { font-size: 1rem; }
        
        p {
            margin-bottom: 1rem;
            color: var(--text-secondary);
        }
        
        a {
            color: var(--accent-color);
            text-decoration: none;
            transition: color 0.2s;
        }
        
        a:hover {
            color: var(--accent-hover);
            text-decoration: underline;
        }
        
        /* Lists */
        ul, ol {
            margin-bottom: 1rem;
            padding-left: 2rem;
            color: var(--text-secondary);
        }
        
        li {
            margin-bottom: 0.5rem;
        }
        
        li::marker {
            color: var(--accent-color);
        }
        
        /* Code blocks */
        pre {
            background: var(--code-bg);
            color: var(--code-text);
            padding: 0;
            border-radius: 12px;
            overflow-x: auto;
            margin-bottom: 1.5rem;
            font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            border: 1px solid var(--border-color);
            position: relative;
        }
        
        pre::before {
            content: '';
            display: block;
            background: linear-gradient(90deg, var(--code-bg), var(--border-color));
            height: 36px;
            border-radius: 12px 12px 0 0;
            position: relative;
        }
        
        pre::after {
            content: '';
            position: absolute;
            top: 12px;
            left: 16px;
            width: 12px;
            height: 12px;
            background: #ff5f56;
            border-radius: 50%;
            box-shadow: 20px 0 0 #ffbd2e, 40px 0 0 #27ca40;
        }
        
        pre code {
            display: block;
            padding: 1rem 1.25rem;
            counter-reset: line;
            overflow-x: auto;
        }
        
        /* Line numbers */
        pre code .line {
            display: block;
            position: relative;
            padding-left: 3.5rem;
        }
        
        pre code .line::before {
            counter-increment: line;
            content: counter(line);
            position: absolute;
            left: 0;
            width: 2.5rem;
            text-align: right;
            color: var(--text-muted);
            opacity: 0.5;
            font-size: 0.8em;
            user-select: none;
            border-right: 1px solid var(--border-color);
            padding-right: 0.75rem;
            margin-right: 1rem;
        }
        
        code {
            font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
            font-size: 0.875em;
        }
        
        :not(pre) > code {
            background: var(--bg-tertiary);
            padding: 0.2em 0.4em;
            border-radius: 4px;
            color: var(--accent-color);
        }
        
        /* Syntax Highlighting - Light Theme */
        [data-theme="light"] .hljs-keyword,
        [data-theme="light"] .hljs-selector-tag,
        [data-theme="light"] .hljs-built_in,
        [data-theme="light"] .hljs-name,
        [data-theme="light"] .hljs-tag { color: #d73a49; }
        
        [data-theme="light"] .hljs-string,
        [data-theme="light"] .hljs-title,
        [data-theme="light"] .hljs-section,
        [data-theme="light"] .hljs-attribute,
        [data-theme="light"] .hljs-literal,
        [data-theme="light"] .hljs-template-tag,
        [data-theme="light"] .hljs-template-variable,
        [data-theme="light"] .hljs-type,
        [data-theme="light"] .hljs-addition { color: #22863a; }
        
        [data-theme="light"] .hljs-comment,
        [data-theme="light"] .hljs-deletion,
        [data-theme="light"] .hljs-meta { color: #6a737d; }
        
        [data-theme="light"] .hljs-number,
        [data-theme="light"] .hljs-symbol,
        [data-theme="light"] .hljs-bullet,
        [data-theme="light"] .hljs-link { color: #005cc5; }
        
        [data-theme="light"] .hljs-function { color: #6f42c1; }
        
        [data-theme="light"] .hljs-class { color: #e36209; }
        
        /* Syntax Highlighting - Dark Theme */
        [data-theme="dark"] .hljs-keyword,
        [data-theme="dark"] .hljs-selector-tag,
        [data-theme="dark"] .hljs-built_in,
        [data-theme="dark"] .hljs-name,
        [data-theme="dark"] .hljs-tag { color: #ff7b72; }
        
        [data-theme="dark"] .hljs-string,
        [data-theme="dark"] .hljs-title,
        [data-theme="dark"] .hljs-section,
        [data-theme="dark"] .hljs-attribute,
        [data-theme="dark"] .hljs-literal,
        [data-theme="dark"] .hljs-template-tag,
        [data-theme="dark"] .hljs-template-variable,
        [data-theme="dark"] .hljs-type,
        [data-theme="dark"] .hljs-addition { color: #a5d6ff; }
        
        [data-theme="dark"] .hljs-comment,
        [data-theme="dark"] .hljs-deletion,
        [data-theme="dark"] .hljs-meta { color: #8b949e; }
        
        [data-theme="dark"] .hljs-number,
        [data-theme="dark"] .hljs-symbol,
        [data-theme="dark"] .hljs-bullet,
        [data-theme="dark"] .hljs-link { color: #79c0ff; }
        
        [data-theme="dark"] .hljs-function { color: #d2a8ff; }
        
        [data-theme="dark"] .hljs-class { color: #ffa657; }
        
        /* Mermaid Diagrams */
        .mermaid {
            background: var(--mermaid-bg);
            padding: 2rem;
            border-radius: 16px;
            margin: 2rem 0;
            border: 1px solid var(--border-color);
            text-align: center;
            overflow-x: auto;
            box-shadow: 0 4px 20px var(--shadow-color);
            transition: all 0.3s ease;
        }
        
        .mermaid:hover {
            box-shadow: 0 8px 30px var(--shadow-color);
            transform: translateY(-2px);
        }
        
        .mermaid svg {
            max-width: 100%;
            height: auto;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        }
        
        [data-theme="dark"] .mermaid svg {
            filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
        }
        
        .mermaid-error {
            color: #ef4444;
            background: #fef2f2;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #fecaca;
            font-size: 0.875rem;
        }
        
        [data-theme="dark"] .mermaid-error {
            background: #450a0a;
            border-color: #7f1d1d;
        }
        
        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5rem;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        
        th, td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background: var(--bg-tertiary);
            font-weight: 600;
            color: var(--text-primary);
        }
        
        tr:nth-child(even) {
            background: var(--table-stripe);
        }
        
        tr:hover {
            background: var(--accent-light);
        }
        
        /* Blockquotes */
        blockquote {
            border-left: 4px solid var(--blockquote-border);
            background: var(--blockquote-bg);
            padding: 1rem 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0 8px 8px 0;
            color: var(--text-secondary);
            font-style: italic;
        }
        
        blockquote p:last-child {
            margin-bottom: 0;
        }
        
        /* Horizontal Rule */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(to right, var(--border-color), var(--accent-color), var(--border-color));
            margin: 2rem 0;
            border-radius: 1px;
        }
        
        /* Images */
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 1rem 0;
            box-shadow: 0 4px 12px var(--shadow-color);
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--text-muted);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-color);
        }
        
        /* Progress bar */
        .progress-bar {
            position: fixed;
            top: 60px;
            left: 0;
            height: 3px;
            background: var(--accent-color);
            z-index: 1001;
            transition: width 0.1s;
            width: 0%;
        }
        
        /* Back to top button */
        .back-to-top {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 48px;
            height: 48px;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
            box-shadow: 0 4px 12px var(--shadow-color);
        }
        
        .back-to-top.visible {
            opacity: 1;
            visibility: visible;
        }
        
        .back-to-top:hover {
            background: var(--accent-hover);
            transform: translateY(-2px);
        }
        
        /* Responsive */
        @media (max-width: 1024px) {
            .main {
                margin-left: 0;
                padding: 1.5rem;
            }
            
            .sidebar {
                transform: translateX(-100%);
            }
            
            .sidebar.open {
                transform: translateX(0);
            }
            
            .sidebar-toggle {
                display: block;
            }
        }
        
        @media (max-width: 640px) {
            .header {
                padding: 0 1rem;
            }
            
            .header-title {
                font-size: 1rem;
            }
            
            h1 { font-size: 1.75rem; }
            h2 { font-size: 1.5rem; }
            h3 { font-size: 1.25rem; }
            
            .main {
                padding: 1rem;
            }
        }
        
        /* Print styles */
        @media print {
            .header, .sidebar, .theme-toggle, .back-to-top, .progress-bar, .sidebar-toggle {
                display: none !important;
            }
            
            .main {
                margin-left: 0 !important;
                max-width: 100% !important;
            }
            
            body {
                background: white;
                color: black;
            }
        }
    </style>
</head>
<body>
    <!-- Progress Bar -->
    <div class="progress-bar" id="progressBar"></div>
    
    <!-- Header -->
    <header class="header">
        <h1 class="header-title">$HOME_LINK$$TITLE$</h1>
        <div class="header-controls">
            <div class="theme-toggle" id="themeToggle" role="button" tabindex="0" aria-label="Toggle theme">
                <span class="icon sun">☀️</span>
                <span class="icon moon">🌙</span>
            </div>
        </div>
    </header>
    
    <!-- Sidebar Toggle (Mobile) -->
    <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle sidebar">☰</button>
    
    <!-- Layout -->
    <div class="layout">
        <!-- Sidebar with TOC -->
        <nav class="sidebar" id="sidebar">
            <div class="toc-title">Table of Contents</div>
            $TOC$
        </nav>
        
        <!-- Main Content -->
        <main class="main">
            <article class="content">
                $CONTENT$
            </article>
        </main>
    </div>
    
    <!-- Back to Top Button -->
    <button class="back-to-top" id="backToTop" aria-label="Back to top">↑</button>
    
    MERMAID_SCRIPT
    
    HIGHLIGHTJS_SCRIPT
    LINENUMBERS_SCRIPT
    <script>
        // Theme Toggle
        const themeToggle = document.getElementById('themeToggle');
        const html = document.documentElement;
        
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme') || 'DEFAULT_THEME';
        html.setAttribute('data-theme', savedTheme);
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            MERMAID_THEME_UPDATE
        });
        
        // Keyboard support for theme toggle
        themeToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                themeToggle.click();
            }
        });
        
        // Sidebar Toggle (Mobile)
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('sidebar');
        
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
        
        // Close sidebar when clicking a link (mobile)
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('open');
                }
            });
        });
        
        // Progress Bar
        const progressBar = document.getElementById('progressBar');
        
        function updateProgressBar() {
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
            progressBar.style.width = progress + '%';
        }
        
        // Back to Top Button
        const backToTop = document.getElementById('backToTop');
        
        function updateBackToTop() {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        }
        
        backToTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        // Active TOC link highlighting
        const tocLinks = document.querySelectorAll('.toc a');
        const headings = document.querySelectorAll('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]');
        
        function updateActiveTocLink() {
            let currentHeading = null;
            
            headings.forEach(heading => {
                const rect = heading.getBoundingClientRect();
                if (rect.top <= 100) {
                    currentHeading = heading;
                }
            });
            
            tocLinks.forEach(link => {
                link.classList.remove('active');
                if (currentHeading && link.getAttribute('href') === '#' + currentHeading.id) {
                    link.classList.add('active');
                }
            });
        }
        
        // Scroll event listener
        window.addEventListener('scroll', () => {
            updateProgressBar();
            updateBackToTop();
            updateActiveTocLink();
        });
        
        // Initial calls
        updateProgressBar();
        updateBackToTop();
        updateActiveTocLink();
        
        // Add smooth hover effect to headings
        headings.forEach(heading => {
            heading.style.cursor = 'pointer';
            heading.addEventListener('click', () => {
                const url = window.location.href.split('#')[0] + '#' + heading.id;
                navigator.clipboard.writeText(url).then(() => {
                    heading.style.color = 'var(--accent-color)';
                    setTimeout(() => {
                        heading.style.color = '';
                    }, 500);
                });
            });
        });
    </script>
</body>
</html>'''
    
    # Replace placeholders
    template = template.replace('DEFAULT_THEME', default_theme)
    template = template.replace('VERSION', __version__)
    template = template.replace('MERMAID_SCRIPT', mermaid_script)
    template = template.replace('MERMAID_THEME_UPDATE', mermaid_theme_update)
    
    # Build Highlight.js script
    if is_offline and offline_libs.get('highlightjs'):
        highlightjs_script = f'''<!-- Highlight.js (embedded for offline use) -->
    <script>
{offline_libs['highlightjs']}
    </script>'''
    else:
        highlightjs_script = '''<!-- Highlight.js for syntax highlighting -->
    <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>'''
    
    template = template.replace('HIGHLIGHTJS_SCRIPT', highlightjs_script)
    
    # Build line numbers script (conditional)
    if enable_line_numbers:
        linenumbers_script = '''<script>
        // Apply syntax highlighting and line numbers
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('pre code').forEach((block) => {
                // Apply highlight.js
                hljs.highlightElement(block);
                
                // Add line numbers
                const lines = block.innerHTML.split('\\n');
                // Remove last empty line if exists
                if (lines[lines.length - 1].trim() === '') {
                    lines.pop();
                }
                const numberedLines = lines.map((line, index) => 
                    `<span class="line">${line}</span>`
                ).join('\\n');
                block.innerHTML = numberedLines;
            });
        });
    </script>'''
    else:
        linenumbers_script = '''<script>
        // Apply syntax highlighting only (no line numbers)
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        });
    </script>'''
    
    template = template.replace('LINENUMBERS_SCRIPT', linenumbers_script)
    
    return template


# =============================================================================
# Mermaid Extension for Markdown
# =============================================================================

class MermaidPreprocessor(markdown.preprocessors.Preprocessor):
    """Preprocessor to handle Mermaid code blocks."""
    
    MERMAID_PATTERN = re.compile(
        r'^```mermaid\s*\n(.*?)^```',
        re.MULTILINE | re.DOTALL
    )
    
    def run(self, lines: List[str]) -> List[str]:
        text = '\n'.join(lines)
        
        def replace_mermaid(match):
            diagram_code = match.group(1).strip()
            # Use a placeholder that won't be processed by other extensions
            return f'<div class="mermaid">\n{diagram_code}\n</div>'
        
        text = self.MERMAID_PATTERN.sub(replace_mermaid, text)
        return text.split('\n')


class MermaidExtension(markdown.Extension):
    """Markdown extension for Mermaid diagram support."""
    
    def extendMarkdown(self, md):
        md.preprocessors.register(
            MermaidPreprocessor(md),
            'mermaid',
            priority=175  # Run before fenced_code
        )


# =============================================================================
# Utility Functions
# =============================================================================

def generate_id(text: str) -> str:
    """Generate a URL-friendly ID from heading text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Convert to lowercase and replace spaces with hyphens
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text


def extract_toc_from_html(html_content: str) -> List[Dict]:
    """Extract headings from HTML and build a table of contents."""
    # Pattern to match headings with id attributes
    heading_pattern = r'<h([1-6])\s+id="([^"]+)"[^>]*>(.+?)</h\1>'
    matches = re.findall(heading_pattern, html_content, re.DOTALL)
    
    if not matches:
        # Try pattern without id (will add ids later)
        heading_pattern = r'<h([1-6])>(.+?)</h\1>'
        matches = re.findall(heading_pattern, html_content, re.DOTALL)
        # Generate IDs from heading text
        matches = [(level, generate_id(text), text) for level, text in matches]
    
    toc_items = []
    for level, heading_id, text in matches:
        # Clean the text (remove any HTML tags inside headings)
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        level = int(level)
        toc_items.append({
            'level': level,
            'id': heading_id,
            'text': clean_text
        })
    
    return toc_items


def convert_md_links_to_html(html_content: str) -> str:
    """Convert local .md links to .html links.
    
    This converts links like:
        <a href="getting-started.md">Getting Started</a>
    To:
        <a href="getting-started.html">Getting Started</a>
    
    Only converts local links (not URLs starting with http://, https://, etc.)
    """
    def replace_md_link(match):
        before = match.group(1)  # href="
        path = match.group(2)    # the path before .md
        after = match.group(3)   # everything after .md up to "
        
        # Convert .md to .html
        return f'{before}{path}.html{after}'
    
    # Match href="...*.md" but not http:// or https:// URLs
    # Captures: (href=")(path-before-.md)(.md and optional anchor)(")
    pattern = r'(href=")(?!https?://|mailto:|tel:|ftp://|//)([^"]*?)(\.md)((?:#[^"]*)?)"'
    
    return re.sub(pattern, r'\1\2.html\4"', html_content)


def add_ids_to_headings(html_content: str) -> str:
    """Add IDs to headings that don't have them."""
    def replace_heading(match):
        full_match = match.group(0)
        level = match.group(1)
        text = match.group(2)
        
        # Check if already has an id
        if 'id="' in full_match:
            return full_match
        
        heading_id = generate_id(text)
        return f'<h{level} id="{heading_id}">{text}</h{level}>'
    
    pattern = r'<h([1-6])(?:\s+id="[^"]*")?[^>]*>(.+?)</h\1>'
    return re.sub(pattern, replace_heading, html_content, flags=re.DOTALL)


def build_toc_html(toc_items: List[Dict]) -> str:
    """Build HTML for the table of contents."""
    if not toc_items:
        return '<ul class="toc"><li><em>No headings found</em></li></ul>'
    
    html = '<ul class="toc">\n'
    for item in toc_items:
        level_class = f'toc-h{item["level"]}'
        html += f'    <li><a href="#{item["id"]}" class="{level_class}">{item["text"]}</a></li>\n'
    html += '</ul>'
    
    return html


# =============================================================================
# Main Converter
# =============================================================================

def convert_markdown_to_html(
    markdown_text: str,
    title: str = "Document",
    enable_mermaid: bool = True,
    default_theme: str = "light",
    offline_libs: Optional[Dict[str, Optional[str]]] = None,
    enable_line_numbers: bool = True,
    enable_breaks: bool = True,
    convert_md_links: bool = True,
    home_link: bool = False
) -> str:
    """Convert markdown text to a fully styled HTML document.
    
    Args:
        markdown_text: The markdown content to convert
        title: Document title
        enable_mermaid: Whether to include Mermaid diagram support
        default_theme: Default theme ('light' or 'dark')
        offline_libs: Dictionary with embedded library content for offline mode
        enable_line_numbers: Whether to show line numbers in code blocks
        enable_breaks: Whether to treat newlines as <br> tags (default: True)
        convert_md_links: Whether to convert local .md links to .html (default: True)
        home_link: Whether to add a home link (🏠 >) before the title (default: False)
    """
    
    # Build extension list
    extensions = [
        'fenced_code',
        'tables',
        'codehilite',
        'toc',
        'attr_list',
        'md_in_html',
        'sane_lists',
    ]
    
    # Add nl2br extension if breaks are enabled
    if enable_breaks:
        extensions.append('nl2br')
    
    if enable_mermaid:
        extensions.append(MermaidExtension())
    
    # Configure markdown
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': True,
            },
            'toc': {
                'permalink': False,
                'slugify': lambda value, separator: generate_id(value),
            }
        }
    )
    
    # Convert markdown to HTML
    content_html = md.convert(markdown_text)
    
    # Ensure all headings have IDs
    content_html = add_ids_to_headings(content_html)
    
    # Convert local .md links to .html links if enabled
    if convert_md_links:
        content_html = convert_md_links_to_html(content_html)
    
    # Extract TOC items
    toc_items = extract_toc_from_html(content_html)
    
    # Build TOC HTML
    toc_html = build_toc_html(toc_items)
    
    # Get the full HTML template
    template = get_html_template(enable_mermaid, default_theme, offline_libs, enable_line_numbers)
    
    # Build home link HTML if enabled
    home_link_html = '<a href="index.html" class="home-link" title="Home">🏠</a> &gt; ' if home_link else ''
    
    # Fill in the template using replace instead of format to avoid issues with CSS braces
    final_html = template.replace('$HOME_LINK$', home_link_html)
    final_html = final_html.replace('$TITLE$', title)
    final_html = final_html.replace('$TOC$', toc_html)
    final_html = final_html.replace('$CONTENT$', content_html)
    
    return final_html


# =============================================================================
# CLI Interface
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog='mk2html',
        description='Convert Markdown to beautiful, interactive HTML with TOC and Mermaid support.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s README.md                          # Basic conversion
  %(prog)s docs.md -o documentation.html      # Specify output file
  %(prog)s guide.md --title "User Guide"      # Custom title
  %(prog)s report.md --theme dark             # Start with dark theme
  %(prog)s spec.md --no-mermaid               # Disable Mermaid support
  %(prog)s input.md -o out.html -t "Title"    # Short options
  %(prog)s input.md --offline                 # Embed JS for offline use
  cat input.md | %(prog)s - -o output.html    # Read from stdin
  %(prog)s --clear-cache                      # Clear cached libraries
  %(prog)s "*" -o ./html/                     # Convert all .md files to ./html/
  %(prog)s "*" -o ./html/ -r                  # Recursively convert all .md files

For more information, visit: https://github.com/your-repo/mk2html
        '''
    )
    
    parser.add_argument(
        'input',
        metavar='INPUT',
        nargs='*',
        help='Input Markdown file(s), "-" for stdin, or "*" for all .md files in current directory'
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='FILE_OR_DIR',
        help='Output HTML file or directory (for multiple files/batch mode)'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Recursively process subdirectories (only with "*" input)'
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
        help='Default theme (default: light)'
    )
    
    parser.add_argument(
        '--no-mermaid',
        action='store_true',
        help='Disable Mermaid diagram support'
    )
    
    parser.add_argument(
        '--no-toc',
        action='store_true',
        help='Disable table of contents generation'
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
        '--no-convert-md-links',
        action='store_true',
        help='Disable converting local .md links to .html (default: convert .md to .html)'
    )
    
    parser.add_argument(
        '--home-link',
        action='store_true',
        help='Add a home link (🏠 >) before the title linking to index.html'
    )
    
    parser.add_argument(
        '--offline',
        action='store_true',
        help='Embed JavaScript libraries for offline use (larger file size)'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear cached library files and exit'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output messages'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser


def convert_single_file(
    input_path: Path,
    output_path: Path,
    opts,
    offline_libs: Optional[Dict[str, Optional[str]]] = None,
    base_input_dir: Optional[Path] = None
) -> bool:
    """Convert a single markdown file to HTML.
    
    Args:
        input_path: Path to the input markdown file
        output_path: Path to the output HTML file
        opts: Parsed command line options
        offline_libs: Pre-downloaded offline libraries (for batch mode efficiency)
        base_input_dir: Base input directory for relative path calculation (batch mode)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        markdown_text = input_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading '{input_path}': {e}", file=sys.stderr)
        return False
    
    # Determine title
    if opts.title and not base_input_dir:
        # Only use custom title for single file mode
        title = opts.title
    else:
        title = input_path.stem.replace('-', ' ').replace('_', ' ').title()
    
    # Determine if home link should be shown
    # Skip home link for index.md/index.html (it's already the home page)
    show_home_link = opts.home_link
    if show_home_link:
        input_stem = input_path.stem.lower()
        if input_stem == 'index':
            show_home_link = False
        output_stem = output_path.stem.lower()
        if output_stem == 'index':
            show_home_link = False
    
    # Convert
    try:
        html_content = convert_markdown_to_html(
            markdown_text,
            title=title,
            enable_mermaid=not opts.no_mermaid,
            default_theme=opts.theme,
            offline_libs=offline_libs,
            enable_line_numbers=not opts.no_line_numbers,
            enable_breaks=not opts.no_breaks,
            convert_md_links=not opts.no_convert_md_links,
            home_link=show_home_link
        )
    except Exception as e:
        print(f"Error converting '{input_path}': {e}", file=sys.stderr)
        return False
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    try:
        output_path.write_text(html_content, encoding='utf-8')
    except Exception as e:
        print(f"Error writing '{output_path}': {e}", file=sys.stderr)
        return False
    
    if not opts.quiet:
        file_size = output_path.stat().st_size
        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / 1024 / 1024:.1f} MB"
        print(f"✓ {input_path} → {output_path} ({size_str})")
    
    return True


def find_markdown_files(base_dir: Path, recursive: bool = False) -> List[Path]:
    """Find all markdown files in a directory.
    
    Args:
        base_dir: Base directory to search
        recursive: Whether to search subdirectories
    
    Returns:
        List of Path objects for markdown files
    """
    if recursive:
        return sorted(base_dir.rglob('*.md'))
    else:
        return sorted(base_dir.glob('*.md'))


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    opts = parser.parse_args(args)
    
    # Handle --clear-cache
    if opts.clear_cache:
        count = clear_cache()
        if not opts.quiet:
            print(f"✓ Cleared {count} cached file(s) from {CACHE_DIR}")
        return 0
    
    # Require input if not clearing cache
    if not opts.input:
        parser.error("the following arguments are required: INPUT")
    
    # Check for batch mode (wildcard)
    if len(opts.input) == 1 and opts.input[0] == '*':
        return main_batch(opts)
    
    # Check for multiple files mode (shell glob expansion like ./docs/*.md)
    if len(opts.input) > 1:
        return main_multiple_files(opts)
    
    # Single file mode
    single_input = opts.input[0]
    
    # Check for recursive without wildcard/multiple files
    if opts.recursive and len(opts.input) == 1 and opts.input[0] != '*':
        print("Error: -r/--recursive can only be used with '*' input or multiple files.", file=sys.stderr)
        return 1
    
    # Read input
    if single_input == '-':
        # Read from stdin
        markdown_text = sys.stdin.read()
        input_name = 'stdin'
        
        if not opts.output:
            print("Error: Output file (-o) is required when reading from stdin.", file=sys.stderr)
            return 1
        
        # Determine title
        if opts.title:
            title = opts.title
        else:
            title = "Document"
        
        # Determine if home link should be shown
        show_home_link = opts.home_link
        if show_home_link and opts.output:
            output_stem = Path(opts.output).stem.lower()
            if output_stem == 'index':
                show_home_link = False
        
        # Get offline libraries if requested
        offline_libs = None
        if opts.offline:
            offline_libs = get_offline_libraries(opts.quiet)
            if not offline_libs.get('highlightjs'):
                print("Warning: Could not download Highlight.js for offline mode. Using CDN.", file=sys.stderr)
            if not opts.no_mermaid and not offline_libs.get('mermaid'):
                print("Warning: Could not download Mermaid.js for offline mode. Using CDN.", file=sys.stderr)
        
        # Convert
        try:
            html_content = convert_markdown_to_html(
                markdown_text,
                title=title,
                enable_mermaid=not opts.no_mermaid,
                default_theme=opts.theme,
                offline_libs=offline_libs,
                enable_line_numbers=not opts.no_line_numbers,
                enable_breaks=not opts.no_breaks,
                convert_md_links=not opts.no_convert_md_links,
                home_link=show_home_link
            )
        except Exception as e:
            print(f"Error during conversion: {e}", file=sys.stderr)
            return 1
        
        # Write output
        output_path = Path(opts.output)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_content, encoding='utf-8')
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
        
        if not opts.quiet:
            file_size = output_path.stat().st_size
            size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / 1024 / 1024:.1f} MB"
            print(f"✓ Successfully converted '{input_name}' to '{output_path}'")
            print(f"  Title: {title}")
            print(f"  Theme: {opts.theme}")
            print(f"  Mermaid: {'enabled' if not opts.no_mermaid else 'disabled'}")
            print(f"  Line numbers: {'enabled' if not opts.no_line_numbers else 'disabled'}")
            print(f"  Line breaks: {'enabled' if not opts.no_breaks else 'disabled'}")
            print(f"  MD→HTML links: {'enabled' if not opts.no_convert_md_links else 'disabled'}")
            print(f"  Home link: {'enabled' if opts.home_link else 'disabled'}")
            print(f"  Offline: {'yes' if opts.offline else 'no'}")
            print(f"  Size: {size_str}")
        
        return 0
    
    # File input mode
    input_path = Path(single_input)
    if not input_path.exists():
        print(f"Error: Input file '{single_input}' not found.", file=sys.stderr)
        return 1
    
    # Determine output file
    if opts.output:
        output_path = Path(opts.output)
    else:
        output_path = input_path.with_suffix('.html')
    
    # Get offline libraries if requested
    offline_libs = None
    if opts.offline:
        offline_libs = get_offline_libraries(opts.quiet)
        if not offline_libs.get('highlightjs'):
            print("Warning: Could not download Highlight.js for offline mode. Using CDN.", file=sys.stderr)
        if not opts.no_mermaid and not offline_libs.get('mermaid'):
            print("Warning: Could not download Mermaid.js for offline mode. Using CDN.", file=sys.stderr)
    
    # Convert single file
    success = convert_single_file(input_path, output_path, opts, offline_libs)
    
    if success and not opts.quiet:
        # Print detailed info for single file mode
        file_size = output_path.stat().st_size
        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / 1024 / 1024:.1f} MB"
        title = opts.title if opts.title else input_path.stem.replace('-', ' ').replace('_', ' ').title()
        print(f"  Title: {title}")
        print(f"  Theme: {opts.theme}")
        print(f"  Mermaid: {'enabled' if not opts.no_mermaid else 'disabled'}")
        print(f"  Line numbers: {'enabled' if not opts.no_line_numbers else 'disabled'}")
        print(f"  Line breaks: {'enabled' if not opts.no_breaks else 'disabled'}")
        print(f"  MD→HTML links: {'enabled' if not opts.no_convert_md_links else 'disabled'}")
        print(f"  Home link: {'enabled' if opts.home_link else 'disabled'}")
        print(f"  Offline: {'yes' if opts.offline else 'no'}")
    
    return 0 if success else 1


def main_batch(opts) -> int:
    """Handle batch conversion mode (input='*').
    
    Args:
        opts: Parsed command line options
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Determine base input directory (current directory)
    base_input_dir = Path('.')
    
    # Require output directory for batch mode
    if not opts.output:
        print("Error: Output directory (-o) is required for batch mode.", file=sys.stderr)
        return 1
    
    output_dir = Path(opts.output)
    
    # Find all markdown files
    md_files = find_markdown_files(base_input_dir, opts.recursive)
    
    if not md_files:
        print("No .md files found.", file=sys.stderr)
        return 1
    
    if not opts.quiet:
        mode = "recursively" if opts.recursive else "in current directory"
        print(f"Found {len(md_files)} markdown file(s) {mode}")
        print(f"Output directory: {output_dir}")
        print()
    
    # Get offline libraries once for efficiency
    offline_libs = None
    if opts.offline:
        offline_libs = get_offline_libraries(opts.quiet)
        if not offline_libs.get('highlightjs'):
            print("Warning: Could not download Highlight.js for offline mode. Using CDN.", file=sys.stderr)
        if not opts.no_mermaid and not offline_libs.get('mermaid'):
            print("Warning: Could not download Mermaid.js for offline mode. Using CDN.", file=sys.stderr)
    
    # Convert each file
    success_count = 0
    error_count = 0
    
    for md_file in md_files:
        # Calculate relative path from base input directory
        relative_path = md_file.relative_to(base_input_dir)
        
        # Build output path preserving directory structure
        output_path = output_dir / relative_path.with_suffix('.html')
        
        if convert_single_file(md_file, output_path, opts, offline_libs, base_input_dir):
            success_count += 1
        else:
            error_count += 1
    
    # Print summary
    if not opts.quiet:
        print()
        print(f"Batch conversion complete:")
        print(f"  ✓ {success_count} file(s) converted successfully")
        if error_count > 0:
            print(f"  ✗ {error_count} file(s) failed")
        print(f"  Output: {output_dir}/")
    
    return 0 if error_count == 0 else 1


def main_multiple_files(opts) -> int:
    """Handle multiple files mode (shell glob expansion like ./docs/*.md).
    
    Args:
        opts: Parsed command line options
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Get list of input files
    input_files = [Path(f) for f in opts.input]
    
    # Filter to only .md files that exist
    md_files = []
    for f in input_files:
        if not f.exists():
            print(f"Warning: File '{f}' not found, skipping.", file=sys.stderr)
            continue
        if f.suffix.lower() == '.md':
            md_files.append(f)
        else:
            print(f"Warning: File '{f}' is not a .md file, skipping.", file=sys.stderr)
    
    if not md_files:
        print("No valid .md files found.", file=sys.stderr)
        return 1
    
    # Require output directory for multiple files mode
    if not opts.output:
        print("Error: Output directory (-o) is required when converting multiple files.", file=sys.stderr)
        return 1
    
    output_dir = Path(opts.output)
    
    # Determine base input directory (common parent of all files)
    # For simplicity, we'll use the parent of the first file as reference
    # and just use the filename for output
    if not opts.quiet:
        print(f"Converting {len(md_files)} markdown file(s)")
        print(f"Output directory: {output_dir}")
        print()
    
    # Get offline libraries once for efficiency
    offline_libs = None
    if opts.offline:
        offline_libs = get_offline_libraries(opts.quiet)
        if not offline_libs.get('highlightjs'):
            print("Warning: Could not download Highlight.js for offline mode. Using CDN.", file=sys.stderr)
        if not opts.no_mermaid and not offline_libs.get('mermaid'):
            print("Warning: Could not download Mermaid.js for offline mode. Using CDN.", file=sys.stderr)
    
    # Convert each file
    success_count = 0
    error_count = 0
    
    for md_file in sorted(md_files):
        # Build output path - just use filename in output directory
        output_path = output_dir / md_file.with_suffix('.html').name
        
        if convert_single_file(md_file, output_path, opts, offline_libs, md_file.parent):
            success_count += 1
        else:
            error_count += 1
    
    # Print summary
    if not opts.quiet:
        print()
        print(f"Conversion complete:")
        print(f"  ✓ {success_count} file(s) converted successfully")
        if error_count > 0:
            print(f"  ✗ {error_count} file(s) failed")
        print(f"  Output: {output_dir}/")
    
    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

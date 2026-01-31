import os
import re
from termcolor import cprint
from typing import List, Dict, Tuple, Optional

def visible_length(text: str) -> int:
    """Calculate the visible length of a string, excluding ANSI color codes"""
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return len(ansi_escape.sub('', text))

def pad_with_color(text: str, width: int) -> str:
    """Pad a string to a specific width, accounting for ANSI color codes"""
    visible_len = visible_length(text)
    padding_needed = width - visible_len
    if padding_needed > 0:
        return text + ' ' * padding_needed
    return text

def format_table(title: str, headers: List[str], rows: List[List[str]]) -> str:
    """Format data as a table similar to nvidia-smi style"""
    if not rows:
        return f"{title}\nNo data available"
    
    # Calculate column widths based on visible length
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], visible_length(str(cell)))
    
    # Build table string
    lines = []
    
    # Title line
    total_width = sum(col_widths) + len(headers) - 1
    title_line = f"╭─ {title} " + "─" * (total_width - len(title) - 4) + "╮"
    lines.append(title_line)
    
    # Header line
    header_line = "│"
    for i, header in enumerate(headers):
        padded_header = header.ljust(col_widths[i])
        header_line += f" {padded_header}│"
    lines.append(header_line)
    
    # Separator line
    separator = "│"
    for width in col_widths:
        separator += " " + "─" * width + " │"
    lines.append(separator)
    
    # Data rows
    for row in rows:
        if all(cell == "" for cell in row):  # Separator row (horizontal line)
            sep_parts = []
            for width in col_widths:
                sep_parts.append("─" * width)
            separator_line = "│ " + " │ ".join(sep_parts) + " │"
            lines.append(separator_line)
        else:
            data_line = "│"
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    padded_cell = pad_with_color(str(cell), col_widths[i])
                    data_line += f" {padded_cell}│"
            lines.append(data_line)
    
    # Bottom line
    bottom_line = "╰" + "─" * (total_width + 2) + "╯"
    lines.append(bottom_line)
    
    return "\n".join(lines)

def print_table(title: str, headers: List[str], rows: List[List[str]], color: str = 'white') -> None:
    """Print a formatted table"""
    table_str = format_table(title, headers, rows)
    cprint(table_str, color)

def print_server_info(host: str = "localhost", port: int = 8081) -> None:
    """Print server information in table format similar to nvidia-smi"""
    headers = ["Protocol", "Address"]
    rows = [
        ["HTTP", f"http://{host}:{port}"],
        ["WebSocket", f"ws://{host}:{port}"]
    ]
    
    title = f"MVIZ (listening *:{port})"
    print_table(title, headers, rows, 'cyan')

def print_iceoryx2_status(services: List[Dict[str, str]]) -> None:
    """Print iceoryx2 services status in table format"""
    headers = ["Service", "Status"]
    rows = []
    
    for service in services:
        service_name = service.get('name', '')
        status = service.get('status', 'unknown')
        status_color = 'green' if status == 'initialized' else 'red'
        status_display = f"✓ {status}" if status == 'initialized' else f"✗ {status}"
        rows.append([service_name, status_display])
    
    if rows:
        title = "iceoryx2 Services"
        print_table(title, headers, rows, 'white')
    else:
        cprint("No iceoryx2 services initialized", 'yellow')

def print_plugin_status(plugins: List[Dict[str, str]]) -> None:
    """Print plugin registration status in table format"""
    headers = ["Plugin", "Status"]
    rows = []
    
    for plugin in plugins:
        plugin_name = plugin.get('name', '')
        status = plugin.get('status', 'unknown')
        status_color = 'green' if status == 'registered' else 'red'
        status_display = f"✓ {status}" if status == 'registered' else f"✗ {status}"
        rows.append([plugin_name, status_display])
    
    if rows:
        title = "Plugin Registry"
        print_table(title, headers, rows, 'white')

def print_config_status(config_info: Dict[str, str]) -> None:
    """Print configuration status in table format"""
    headers = ["Component", "Status"]
    rows = []
    
    for component, status in config_info.items():
        status_color = 'green' if 'loaded' in status.lower() or 'default' in status.lower() else 'yellow'
        status_display = f"✓ {status}" if status_color == 'green' else f"⚠ {status}"
        rows.append([component, status_display])
    
    if rows:
        title = "Configuration"
        print_table(title, headers, rows, 'white')

def print_motion_library_status(library_info: Dict[str, str]) -> None:
    """Print motion library status in table format"""
    headers = ["Library", "Status"]
    rows = []
    
    for lib_name, status in library_info.items():
        status_color = 'green' if 'loaded' in status.lower() else 'yellow'
        status_display = f"✓ {status}" if status_color == 'green' else f"⚠ {status}"
        rows.append([lib_name, status_display])
    
    if rows:
        title = "Motion Library"
        print_table(title, headers, rows, 'white')

def print_startup_info(host: str, port: int, plugins: List[Dict[str, str]], config_status: str = "default") -> None:
    """Print all startup information in one unified table"""
    from termcolor import colored
    
    headers = ["Category", "Item", "Status"]
    rows = []
    
    # Server information section
    rows.append(["Server", "Listening", colored(f"*:{port}", 'green')])
    rows.append(["", "HTTP", colored(f"http://{host}:{port}", 'green')])
    rows.append(["", "WebSocket", colored(f"ws://{host}:{port}", 'green')])
    rows.append(["", "", ""])  # Separator line
    
    # Plugin information section
    if plugins:
        registered_count = len([p for p in plugins if p['status'] == 'registered'])
        total_count = len(plugins)
        rows.append(["Plugins", "Summary", f"{registered_count}/{total_count} registered"])
        
        for plugin in plugins:
            status = plugin.get('status', 'unknown')
            plugin_name = plugin.get('name', '').replace('Module', '').strip()
            
            if status == 'registered':
                status_display = "✓ Registered"
            elif status.startswith('failed'):
                status_display = f"✗ Failed"
            else:
                status_display = f"⚠ {status}"
            
            rows.append(["", plugin_name, status_display])
    else:
        rows.append(["Plugins", "Summary", "No plugins loaded"])
    
    title = f"MVIZ Startup (port {port})"
    print_table(title, headers, rows, 'white')
"""
Dracoon Pyclient - Utility-Funktionen
Wiederverwendbare TUI-Komponenten mit einheitlichem Design
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.align import Align
from rich import box
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv


# Farbschema-Konstanten für einheitliches Design
COLOR_PRIMARY = "cyan"
COLOR_SUCCESS = "green"
COLOR_ERROR = "red"
COLOR_WARNING = "yellow"
COLOR_DIM = "dim"
TABLE_BOX = box.ROUNDED


def show_header(console: Console, title: str) -> None:
    """Zeigt einen zentrierten Header mit Titel-Panel an."""
    panel = Panel.fit(
        f"[bold {COLOR_PRIMARY}]{title}[/bold {COLOR_PRIMARY}]",
        border_style=COLOR_PRIMARY,
        padding=(0, 4),
    )
    console.print()
    console.print(Align.center(panel))
    console.print()


def get_credentials() -> tuple:
    """
    Loads credentials from .env or asks interactively
    Returns: (base_url, client_id, client_secret, username, password)
    """
    console = Console()
    load_dotenv()
    
    base_url = os.getenv('DRACOON_BASE_URL')
    if not base_url:
        base_url = Prompt.ask(f"[{COLOR_PRIMARY}]Dracoon URL[/{COLOR_PRIMARY}]")
    else:
        console.print(f"[{COLOR_DIM}]Dracoon URL from .env: {base_url}[/{COLOR_DIM}]")
    
    client_id = os.getenv('DRACOON_CLIENT_ID')
    if not client_id:
        console.print(f"\n[{COLOR_PRIMARY}]OAuth-App Credentials:[/{COLOR_PRIMARY}]")
        client_id = Prompt.ask(f"[{COLOR_PRIMARY}]Client ID[/{COLOR_PRIMARY}]")
    else:
        console.print(f"[{COLOR_DIM}]Client ID from .env: {client_id[:8]}...[/{COLOR_DIM}]")
    
    client_secret = os.getenv('DRACOON_CLIENT_SECRET')
    if not client_secret:
        client_secret = Prompt.ask(f"[{COLOR_PRIMARY}]Client Secret[/{COLOR_PRIMARY}]", password=True)
    else:
        console.print(f"[{COLOR_DIM}]Client Secret from .env: ********[/{COLOR_DIM}]")
    
    username = os.getenv('DRACOON_USERNAME')
    if not username:
        console.print(f"\n[{COLOR_PRIMARY}]Your Dracoon Login:[/{COLOR_PRIMARY}]")
        username = Prompt.ask(f"[{COLOR_PRIMARY}]Username[/{COLOR_PRIMARY}]")
    else:
        console.print(f"[{COLOR_DIM}]Username from .env: {username}[/{COLOR_DIM}]")
    
    password = os.getenv('DRACOON_PASSWORD')
    if not password:
        password = Prompt.ask(f"[{COLOR_PRIMARY}]Password[/{COLOR_PRIMARY}]", password=True)
    else:
        console.print(f"[{COLOR_DIM}]Password from .env: ********[/{COLOR_DIM}]")
    
    return base_url, client_id, client_secret, username, password


def search_and_select_user(console: Console, all_users: List[Dict], prompt_text: str = "Search for user") -> Optional[Dict]:
    """Interactive user search and selection"""
    console.print(f"\n[bold {COLOR_PRIMARY}]{prompt_text}[/bold {COLOR_PRIMARY}]")
    search = Prompt.ask(f"[{COLOR_PRIMARY}]Name or email (Enter for list)[/{COLOR_PRIMARY}]", default="")
    
    if search:
        filtered_users = [
            u for u in all_users
            if search.lower() in f"{u.get('firstName', '')} {u.get('lastName', '')}".lower()
            or search.lower() in u.get('email', '').lower()
            or search.lower() in u.get('userName', '').lower()
        ]
    else:
        filtered_users = all_users
    
    if not filtered_users:
        console.print(f"[{COLOR_ERROR}]No users found![/{COLOR_ERROR}]")
        return None
    
    table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
    table.add_column("#", style=COLOR_DIM, width=6)
    table.add_column("Name", width=25)
    table.add_column("Email", width=35)
    table.add_column("Username", width=20)
    
    display_users = filtered_users[:20]
    
    for idx, user in enumerate(display_users, 1):
        name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
        table.add_row(str(idx), name, user.get('email', ''), user.get('userName', ''))
    
    console.print(table)
    
    if len(filtered_users) > 20:
        console.print(f"\n[{COLOR_WARNING}]Note: {len(filtered_users) - 20} additional results not shown.[/{COLOR_WARNING}]")
    
    console.print()
    choice = Prompt.ask(f"[{COLOR_PRIMARY}]Select user (number) or 's' for new search[/{COLOR_PRIMARY}]", default="1")
    
    if choice.lower() == 's':
        return search_and_select_user(console, all_users, prompt_text)
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(display_users):
            return display_users[idx]
        console.print(f"[{COLOR_ERROR}]Invalid selection![/{COLOR_ERROR}]")
        return None
    except ValueError:
        console.print(f"[{COLOR_ERROR}]Invalid input![/{COLOR_ERROR}]")
        return None


def export_to_csv(file_path: str, headers: list, rows: list) -> bool:
    """
    Exportiert Daten als CSV
    
    Args:
        file_path: Pfad zur CSV-Datei
        headers: Liste der Spaltenüberschriften
        rows: Liste von Zeilen (jede Zeile ist eine Liste von Werten)
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        
        return True
    except Exception:
        return False


def pause(console: Console, message: str = "Press Enter to continue"):
    """Pauses and waits for Enter"""
    Prompt.ask(f"\n[{COLOR_DIM}]{message}[/{COLOR_DIM}]")
#!/usr/bin/env python3
"""
Dracoon Pyclient - Modulares Support-Toolset
Hauptmenü zur Auswahl verschiedener Module

Nutzt offizielles dracoon SDK!
https://github.com/unbekanntes-pferd/dracoon-python-api
"""

__version__ = "0.1.2"

import sys
import asyncio
import argparse
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from dracoon import DRACOON, OAuth2ConnectionType

from lib import (
    show_header, get_credentials, pause,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_DIM, TABLE_BOX
)
from modules import user_to_group, room_admin_report, group_members_report


class DracoonPyclient:
    def __init__(self):
        self.console = Console()
        self.dracoon = None
        self.god_mode = False
        
        # Verfügbare Module
        self.modules = [
            {
                'id': 1,
                'name': 'User zu Gruppe hinzufügen',
                'description': 'Fügt Benutzer zu Gruppen hinzu - einzeln, gefiltert oder als Massenoperation',
                'module': user_to_group
            },
            {
                'id': 2,
                'name': 'Room Admin Report',
                'description': 'Zeigt (löscht) Räume eines Benutzers in denen er letzter Admin ist',
                'module': room_admin_report
            },
            {
                'id': 3,
                'name': 'Gruppenmitglieder auflisten',
                'description': 'Listet alle Mitglieder einer Gruppe auf und exportiert optional als CSV',
                'module': group_members_report
            }
        ]
    
    async def connect(self):
        """Stellt Verbindung zur Dracoon API her"""
        self.console.clear()
        show_header(self.console, f"Dracoon Pyclient v{__version__}")
        
        if self.god_mode:
            self.console.print(f"[{COLOR_ERROR}]⚠️  GOD-MODE AKTIV ⚠️[/{COLOR_ERROR}]\n")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Verbindung zu Dracoon herstellen[/bold {COLOR_PRIMARY}]\n")
        self.console.print(f"[{COLOR_DIM}]OAuth Password Grant Flow[/{COLOR_DIM}]\n")
        
        # Credentials laden
        base_url, client_id, client_secret, username, password = get_credentials()
        
        self.console.print(f"\n[{COLOR_WARNING}]Verbinde mit Dracoon...[/{COLOR_WARNING}]")
        
        try:
            self.dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret)
            
            # God-Mode am DRACOON-Objekt setzen
            self.dracoon.god_mode = self.god_mode
            
            await self.dracoon.connect(OAuth2ConnectionType.password_flow, username, password)
            
            user_info = await self.dracoon.user.get_account_information()
            first_name = getattr(user_info, 'firstName', '')
            last_name = getattr(user_info, 'lastName', '')
            
            self.console.print(f"[{COLOR_SUCCESS}]✓ Verbunden als: {first_name} {last_name}[/{COLOR_SUCCESS}]\n")
            return True
                
        except Exception as e:
            self.console.print(f"[{COLOR_ERROR}]✗ Fehler: {str(e)}[/{COLOR_ERROR}]\n")
            if Confirm.ask("Nochmal versuchen?"):
                return await self.connect()
            return False
    
    def show_main_menu(self):
        """Zeigt das Hauptmenü"""
        self.console.clear()
        show_header(self.console, f"Dracoon Pyclient v{__version__} - Hauptmenü")
        
        if self.god_mode:
            self.console.print(f"[{COLOR_ERROR}]⚠️  GOD-MODE AKTIV ⚠️[/{COLOR_ERROR}]\n")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Verfügbare Module:[/bold {COLOR_PRIMARY}]\n")
        
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("#", style=COLOR_DIM, width=4)
        table.add_column("Modul", width=30)
        table.add_column("Beschreibung", width=60)
        
        for module in self.modules:
            table.add_row(
                str(module['id']),
                module['name'],
                module['description']
            )
        
        self.console.print(table)
        
        self.console.print(f"\n[bold {COLOR_PRIMARY}]Optionen:[/bold {COLOR_PRIMARY}]")
        self.console.print(f"  [{COLOR_PRIMARY}]<Nummer>[/{COLOR_PRIMARY}] - Modul starten")
        self.console.print(f"  [{COLOR_PRIMARY}]q[/{COLOR_PRIMARY}] - Beenden\n")
        
        choice = Prompt.ask("Auswahl")
        
        if choice.lower() == 'q':
            return None
        
        try:
            module_id = int(choice)
            selected_module = next((m for m in self.modules if m['id'] == module_id), None)
            
            if selected_module:
                return selected_module
            else:
                self.console.print(f"[{COLOR_ERROR}]Ungültiges Modul! Bitte Nummer zwischen 1 und {len(self.modules)} eingeben.[/{COLOR_ERROR}]\n")
                pause(self.console)
                return self.show_main_menu()
        except ValueError:
            self.console.print(f"[{COLOR_ERROR}]Ungültige Eingabe! Bitte nur Zahlen eingeben.[/{COLOR_ERROR}]\n")
            pause(self.console)
            return self.show_main_menu()
    
    async def run_module(self, module):
        """Startet das ausgewählte Modul"""
        try:
            await module['module'].main(self.dracoon)
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Fehler beim Ausführen des Moduls: {str(e)}[/{COLOR_ERROR}]\n")
            pause(self.console)
    
    async def run(self):
        """Hauptschleife"""
        try:
            # Startbildschirm
            self.console.clear()
            self.console.print()  # Leerzeile
            show_header(self.console, f"Dracoon Pyclient v{__version__}")
            
            self.console.print(f"[bold {COLOR_PRIMARY}]Willkommen beim Dracoon Pyclient![/bold {COLOR_PRIMARY}]\n")
            self.console.print(f"[{COLOR_DIM}]Modulares Support-Toolset[/{COLOR_DIM}]")
            self.console.print(f"[{COLOR_DIM}]Nutzt offizielles Dracoon SDK[/{COLOR_DIM}]")
            
            if self.god_mode:
                self.console.print(f"\n[{COLOR_ERROR}]⚠️  GOD-MODE ist aktiviert! ⚠️[/{COLOR_ERROR}]")
            
            self.console.print()
            pause(self.console, "Enter drücken um zu starten")
            
            if not await self.connect():
                return
            
            pause(self.console)
            
            while True:
                selected_module = self.show_main_menu()
                
                if selected_module is None:
                    break
                
                await self.run_module(selected_module)
            
            await self.dracoon.logout()
            self.console.print(f"\n[{COLOR_PRIMARY}]Auf Wiedersehen![/{COLOR_PRIMARY}]\n")
            
        except KeyboardInterrupt:
            self.console.print(f"\n\n[{COLOR_WARNING}]Abgebrochen durch Benutzer[/{COLOR_WARNING}]\n")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Fehler: {str(e)}[/{COLOR_ERROR}]\n")


def main():
    parser = argparse.ArgumentParser(
        description=f'Dracoon Pyclient v{__version__} - Modulares Support-Toolset',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--god-mode',
        action='store_true',
        help='Aktiviert God-Mode (löscht Räume ohne Nachfrage - GEFÄHRLICH!)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    app = DracoonPyclient()
    app.god_mode = args.god_mode
    
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
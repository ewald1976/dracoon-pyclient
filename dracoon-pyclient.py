#!/usr/bin/env python3
"""
Dracoon Pyclient - Modulares Support-Toolset
Hauptmenü zur Auswahl verschiedener Module

Nutzt offizielles dracoon SDK!
https://github.com/unbekanntes-pferd/dracoon-python-api
"""

__version__ = "0.3.1"

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
from modules import user_to_group, room_admin_report, group_members_report, customer_email_export


class DracoonPyclient:
    def __init__(self):
        self.console = Console()
        self.dracoon = None
        self.god_mode = False
        
        # Available modules
        self.modules = [
            {
                'id': 1,
                'name': 'Add Users to Group',
                'description': 'Add users to groups - individually, filtered or as bulk operation',
                'module': user_to_group,
                'requires_connection': True
            },
            {
                'id': 2,
                'name': 'Room Admin Report',
                'description': 'Shows (deletes) rooms where a user is the last admin',
                'module': room_admin_report,
                'requires_connection': True
            },
            {
                'id': 3,
                'name': 'List Group Members',
                'description': 'Lists all members of a group and optionally exports as CSV',
                'module': group_members_report,
                'requires_connection': True
            },
            {
                'id': 4,
                'name': 'Customer Email Export (Reseller)',
                'description': 'Export all email addresses from all customers (Multi-Tenant)',
                'module': customer_email_export,
                'requires_connection': False  # Nutzt Provisioning API statt normalem SDK
            }
        ]
    
    def has_oauth_modules_enabled(self):
        """Prüft ob Module vorhanden sind die OAuth benötigen"""
        return any(m.get('requires_connection', True) for m in self.modules)
    
    async def connect(self, skip_on_error=False):
        """Establishes connection to Dracoon API"""
        self.console.clear()
        show_header(self.console, f"Dracoon Pyclient v{__version__}")
        
        if self.god_mode:
            self.console.print(f"[{COLOR_ERROR}]⚠️  GOD-MODE ACTIVE ⚠️[/{COLOR_ERROR}]\n")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Connect to Dracoon[/bold {COLOR_PRIMARY}]\n")
        self.console.print(f"[{COLOR_DIM}]OAuth Password Grant Flow[/{COLOR_DIM}]\n")
        
        # Credentials laden
        base_url, client_id, client_secret, username, password = get_credentials()
        
        # Wenn alle Felder leer sind, OAuth überspringen
        if not any([client_id, client_secret, username, password]):
            if skip_on_error:
                self.console.print(f"[{COLOR_WARNING}]No OAuth credentials found. Skipping OAuth authentication.[/{COLOR_WARNING}]")
                return False
        
        self.console.print(f"\n[{COLOR_WARNING}]Connecting to Dracoon...[/{COLOR_WARNING}]")
        
        try:
            self.dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret)
            
            # God-Mode am DRACOON-Objekt setzen
            self.dracoon.god_mode = self.god_mode
            
            await self.dracoon.connect(OAuth2ConnectionType.password_flow, username, password)
            
            user_info = await self.dracoon.user.get_account_information()
            first_name = getattr(user_info, 'firstName', '')
            last_name = getattr(user_info, 'lastName', '')
            
            self.console.print(f"[{COLOR_SUCCESS}]✓ Connected as: {first_name} {last_name}[/{COLOR_SUCCESS}]\n")
            return True
                
        except Exception as e:
            self.console.print(f"[{COLOR_ERROR}]✗ Error: {str(e)}[/{COLOR_ERROR}]\n")
            
            if skip_on_error:
                return False
            
            if Confirm.ask("Try again?"):
                return await self.connect(skip_on_error)
            return False
    
    def show_main_menu(self):
        """Shows the main menu"""
        self.console.clear()
        show_header(self.console, f"Dracoon Pyclient v{__version__} - Main Menu")
        
        if self.god_mode:
            self.console.print(f"[{COLOR_ERROR}]⚠️  GOD-MODE ACTIVE ⚠️[/{COLOR_ERROR}]\n")
        
        # Info über verfügbare Auth-Methoden
        if self.dracoon:
            self.console.print(f"[{COLOR_SUCCESS}]✓ OAuth connected[/{COLOR_SUCCESS}]")
        else:
            self.console.print(f"[{COLOR_WARNING}]⚠ OAuth not connected (Provisioning API only)[/{COLOR_WARNING}]")
        
        self.console.print(f"\n[bold {COLOR_PRIMARY}]Available Modules:[/bold {COLOR_PRIMARY}]\n")
        
        # Tabelle ohne separate Nummer-Spalte - Nummer wird in Modulnamen integriert
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("Module", width=35)
        table.add_column("Auth", width=14)
        table.add_column("Description", width=50)
        
        for module in self.modules:
            auth_type = "OAuth" if module.get('requires_connection', True) else "Service Token"
            auth_color = COLOR_SUCCESS if (module.get('requires_connection', True) and self.dracoon) or \
                         (not module.get('requires_connection', True)) else COLOR_DIM
            
            # Nummer direkt im Modulnamen anzeigen
            module_display = f"[bold {COLOR_PRIMARY}]{module['id']}.[/bold {COLOR_PRIMARY}] {module['name']}"
            
            table.add_row(
                module_display,
                f"[{auth_color}]{auth_type}[/{auth_color}]",
                module['description']
            )
        
        self.console.print(table)
        
        self.console.print(f"\n[bold {COLOR_PRIMARY}]Options:[/bold {COLOR_PRIMARY}]")
        self.console.print(f"  [{COLOR_PRIMARY}]<Number>[/{COLOR_PRIMARY}] - Start module")
        self.console.print(f"  [{COLOR_PRIMARY}]q[/{COLOR_PRIMARY}] - Quit\n")
        
        choice = Prompt.ask("Selection")
        
        if choice.lower() == 'q':
            return None
        
        try:
            module_id = int(choice)
            selected_module = next((m for m in self.modules if m['id'] == module_id), None)
            
            if selected_module:
                return selected_module
            else:
                self.console.print(f"[{COLOR_ERROR}]Invalid module! Please enter a number between 1 and {len(self.modules)}.[/{COLOR_ERROR}]\n")
                pause(self.console)
                return self.show_main_menu()
        except ValueError:
            self.console.print(f"[{COLOR_ERROR}]Invalid input! Please enter numbers only.[/{COLOR_ERROR}]\n")
            pause(self.console)
            return self.show_main_menu()
    
    async def run_module(self, module):
        """Starts the selected module"""
        try:
            # Prüfen ob Modul OAuth benötigt aber keine Verbindung besteht
            if module.get('requires_connection', True) and self.dracoon is None:
                self.console.print(f"\n[{COLOR_ERROR}]✗ This module requires OAuth authentication![/{COLOR_ERROR}]")
                self.console.print(f"[{COLOR_WARNING}]Please configure OAuth credentials in .env[/{COLOR_WARNING}]\n")
                pause(self.console)
                return
            
            # Manche Module benötigen keine DRACOON-Connection (z.B. Provisioning API)
            if module.get('requires_connection', True):
                await module['module'].main(self.dracoon)
            else:
                await module['module'].main()
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Error running module: {str(e)}[/{COLOR_ERROR}]\n")
            import traceback
            traceback.print_exc()
            pause(self.console)
    
    async def run(self):
        """Main loop"""
        try:
            # Start screen
            self.console.clear()
            self.console.print()  # Empty line
            show_header(self.console, f"Dracoon Pyclient v{__version__}")
            
            self.console.print(f"[bold {COLOR_PRIMARY}]Welcome to Dracoon Pyclient![/bold {COLOR_PRIMARY}]\n")
            self.console.print(f"[{COLOR_DIM}]Modular Support Toolset[/{COLOR_DIM}]")
            self.console.print(f"[{COLOR_DIM}]Using official Dracoon SDK[/{COLOR_DIM}]")
            
            if self.god_mode:
                self.console.print(f"\n[{COLOR_ERROR}]⚠️  GOD-MODE is enabled! ⚠️[/{COLOR_ERROR}]")
            
            self.console.print()
            pause(self.console, "Press Enter to start")
            
            # OAuth-Verbindung versuchen, aber nicht zwingend erforderlich
            oauth_connected = await self.connect(skip_on_error=True)
            
            if not oauth_connected:
                self.console.print(f"\n[{COLOR_WARNING}]OAuth not configured or connection failed.[/{COLOR_WARNING}]")
                self.console.print(f"[{COLOR_DIM}]Only Provisioning API modules (Service Token) will be available.[/{COLOR_DIM}]\n")
            
            pause(self.console)
            
            while True:
                selected_module = self.show_main_menu()
                
                if selected_module is None:
                    break
                
                await self.run_module(selected_module)
            
            if self.dracoon:
                await self.dracoon.logout()
            
            self.console.print(f"\n[{COLOR_PRIMARY}]Goodbye![/{COLOR_PRIMARY}]\n")
            
        except KeyboardInterrupt:
            self.console.print(f"\n\n[{COLOR_WARNING}]Cancelled by user[/{COLOR_WARNING}]\n")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Error: {str(e)}[/{COLOR_ERROR}]\n")


def main():
    parser = argparse.ArgumentParser(
        description=f'Dracoon Pyclient v{__version__} - Modular Support Toolset',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--god-mode',
        action='store_true',
        help='Activates God-Mode (deletes rooms without confirmation - DANGEROUS!)'
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

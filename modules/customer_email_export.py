#!/usr/bin/env python3
"""
Dracoon Pyclient - Customer Email Export
Exportiert E-Mail-Adressen aller User über alle Kunden eines Tenants (Reseller)
"""

import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.panel import Panel
from dotenv import load_dotenv

from lib import (
    show_header, pause, export_to_csv,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_DIM, TABLE_BOX
)
from lib.provisioning import ProvisioningClient


class CustomerEmailExport:
    def __init__(self):
        self.console = Console()
        self.prov_client = None
        self.all_emails = []
        self.customer_limit = None
        
    async def run(self):
        """Main function of the module"""
        try:
            self.console.clear()
            show_header(self.console, "Dracoon Pyclient - Customer Email Export")
            
            # Provisioning Token laden
            if not await self._load_provisioning_credentials():
                return
            
            # Verbindung testen
            if not await self._test_connection():
                return
            
            pause(self.console)
            
            # Kunden laden und E-Mails sammeln
            await self._collect_all_emails()
            
            # Ergebnisse anzeigen
            self._show_results()
            
            # Export anbieten
            if self.all_emails:
                await self._export_emails()
            
            self.console.print(f"\n[{COLOR_PRIMARY}]Back to main menu...[/{COLOR_PRIMARY}]\n")
            pause(self.console)
            
        except KeyboardInterrupt:
            self.console.print(f"\n\n[{COLOR_WARNING}]Cancelled by user[/{COLOR_WARNING}]\n")
            pause(self.console)
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Error: {str(e)}[/{COLOR_ERROR}]\n")
            import traceback
            traceback.print_exc()
            pause(self.console)
    
    async def _load_provisioning_credentials(self) -> bool:
        """Lädt Provisioning Token aus .env oder fragt interaktiv ab"""
        load_dotenv()
        
        base_url = os.getenv('DRACOON_BASE_URL')
        if not base_url:
            base_url = Prompt.ask(f"[{COLOR_PRIMARY}]Dracoon URL[/{COLOR_PRIMARY}]")
        else:
            self.console.print(f"[{COLOR_DIM}]Dracoon URL from .env: {base_url}[/{COLOR_DIM}]")
        
        service_token = os.getenv('DRACOON_SERVICE_TOKEN')
        if not service_token:
            self.console.print(f"\n[{COLOR_PRIMARY}]Provisioning API Access:[/{COLOR_PRIMARY}]")
            self.console.print(f"[{COLOR_DIM}]You need a X-SDS-Service-Token for Multi-Tenant access[/{COLOR_DIM}]")
            service_token = Prompt.ask(f"[{COLOR_PRIMARY}]Service Token[/{COLOR_PRIMARY}]", password=True)
        else:
            self.console.print(f"[{COLOR_DIM}]Service Token from .env: ********[/{COLOR_DIM}]")
        
        if not service_token:
            self.console.print(f"\n[{COLOR_ERROR}]✗ No Service Token provided![/{COLOR_ERROR}]")
            pause(self.console)
            return False
        
        # DEBUG-MODUS AKTIVIERT!
        self.prov_client = ProvisioningClient(base_url, service_token, debug=True)
        return True
    
    async def _test_connection(self) -> bool:
        """Testet die Verbindung zur Provisioning API"""
        self.console.print(f"\n[{COLOR_WARNING}]Testing connection to Provisioning API...[/{COLOR_WARNING}]")
        
        try:
            if await self.prov_client.test_connection():
                self.console.print(f"[{COLOR_SUCCESS}]✓ Connection successful![/{COLOR_SUCCESS}]")
                return True
            else:
                self.console.print(f"[{COLOR_ERROR}]✗ Connection failed![/{COLOR_ERROR}]")
                pause(self.console)
                return False
        except Exception as e:
            self.console.print(f"[{COLOR_ERROR}]✗ Error: {str(e)}[/{COLOR_ERROR}]")
            self.console.print(f"\n[{COLOR_WARNING}]Hint: Check if the Service Token is valid[/{COLOR_WARNING}]")
            pause(self.console)
            return False
    
    async def _collect_all_emails(self):
        """Sammelt alle E-Mail-Adressen von allen Kunden mit detaillierter Progress-Anzeige"""
        self.console.clear()
        show_header(self.console, "Collecting Email Addresses")
        
        try:
            # Alle Kunden laden
            self.console.print(f"[{COLOR_WARNING}]Loading customers (fetching first page to count)...[/{COLOR_WARNING}]")
            
            # Erst mal nur erste Page holen um Anzahl zu sehen
            first_page = await self.prov_client.get_customers(offset=0, limit=500)
            total_available = first_page.get('range', {}).get('total', 0)
            
            self.console.print(f"[{COLOR_SUCCESS}]✓ Found {total_available:,} total customers in tenant[/{COLOR_SUCCESS}]\n")
            
            # Warnung bei sehr vielen Kunden
            if total_available > 1000:
                self.console.print(f"[{COLOR_WARNING}]⚠️  Warning: This tenant has {total_available:,} customers![/{COLOR_WARNING}]")
                self.console.print(f"[{COLOR_WARNING}]   Processing all customers could take hours![/{COLOR_WARNING}]\n")
            
            # Limit abfragen
            self.console.print(f"[bold {COLOR_PRIMARY}]Limit Options:[/bold {COLOR_PRIMARY}]")
            self.console.print(f"  [{COLOR_DIM}]1. Process ALL customers ({total_available:,})[/{COLOR_DIM}]")
            self.console.print(f"  [{COLOR_DIM}]2. Limit to first N customers[/{COLOR_DIM}]")
            self.console.print(f"  [{COLOR_DIM}]3. Cancel[/{COLOR_DIM}]\n")
            
            choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="2")
            
            if choice == "3":
                return
            elif choice == "2":
                while True:
                    limit_input = IntPrompt.ask(
                        f"[{COLOR_PRIMARY}]How many customers to process?[/{COLOR_PRIMARY}]",
                        default=100
                    )
                    if limit_input > 0 and limit_input <= total_available:
                        self.customer_limit = limit_input
                        break
                    else:
                        self.console.print(f"[{COLOR_ERROR}]Please enter a number between 1 and {total_available}[/{COLOR_ERROR}]")
            else:
                self.customer_limit = None
            
            # Kunden laden (mit oder ohne Limit)
            self.console.print(f"\n[{COLOR_WARNING}]Loading customers...[/{COLOR_WARNING}]")
            
            if self.customer_limit:
                # Mit Limit: Manuell Pagination bis Limit erreicht
                customers = []
                offset = 0
                while len(customers) < self.customer_limit:
                    remaining = self.customer_limit - len(customers)
                    fetch_count = min(500, remaining)
                    
                    page = await self.prov_client.get_customers(offset=offset, limit=fetch_count)
                    page_customers = page.get('items', [])
                    customers.extend(page_customers)
                    
                    if not page_customers:
                        break
                    
                    offset += len(page_customers)
            else:
                # Ohne Limit: Alle holen
                customers = await self.prov_client.get_all_customers()
            
            if not customers:
                self.console.print(f"[{COLOR_WARNING}]No customers found![/{COLOR_WARNING}]")
                pause(self.console)
                return
            
            total_customers = len(customers)
            self.console.print(f"[{COLOR_SUCCESS}]✓ Processing {total_customers:,} customer(s)[/{COLOR_SUCCESS}]\n")
            
            # E-Mails von allen Kunden sammeln mit detaillierter Progress-Anzeige
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
                expand=True
            ) as progress:
                
                # Hauptaufgabe: Kunden durchlaufen
                main_task = progress.add_task(
                    f"[{COLOR_PRIMARY}]Overall Progress",
                    total=total_customers
                )
                
                # Detail-Aufgabe: Aktueller Kunde
                detail_task = progress.add_task(
                    f"[{COLOR_DIM}]Initializing...",
                    total=None
                )
                
                for idx, customer in enumerate(customers, 1):
                    customer_id = customer.get('id')
                    customer_name = customer.get('companyName', 'Unknown')

                    # Kunden-Namen kürzen für bessere Anzeige
                    display_name = customer_name[:40] + "..." if len(customer_name) > 40 else customer_name

                    # Detail-Task aktualisieren
                    progress.update(
                        detail_task,
                        description=f"[{COLOR_WARNING}]Processing ({idx}/{total_customers}): {display_name}"
                    )

                    # Neue Kunden-Felder extrahieren
                    contract_type = customer.get('customerContractType', '')
                    user_max = customer.get('userMax', 0)
                    quota_max_bytes = customer.get('quotaMax', 0)
                    quota_gb = round(quota_max_bytes / (1024 ** 3), 1) if quota_max_bytes else 0
                    created_at_raw = customer.get('createdAt', '')
                    if created_at_raw:
                        try:
                            from datetime import timezone
                            dt = datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
                            created_at = dt.strftime('%d.%m.%Y')
                        except Exception:
                            created_at = created_at_raw
                    else:
                        created_at = ''

                    try:
                        # Alle User des Kunden laden
                        users = await self.prov_client.get_all_customer_users(customer_id)

                        user_count = 0
                        # E-Mails extrahieren
                        for user in users:
                            email = user.get('email')
                            if email:
                                self.all_emails.append({
                                    'customer_id': customer_id,
                                    'customer_name': customer_name,
                                    'contract_type': contract_type,
                                    'user_max': user_max,
                                    'quota_gb': quota_gb,
                                    'created_at': created_at,
                                    'user_id': user.get('id'),
                                    'first_name': user.get('firstName', ''),
                                    'last_name': user.get('lastName', ''),
                                    'email': email,
                                    'username': user.get('userName', ''),
                                    'is_locked': user.get('isLocked', False),
                                    'is_admin': user.get('isAdmin', False),
                                    'is_config_manager': user.get('isConfigManager', False),
                                    'is_user_manager': user.get('isUserManager', False),
                                    'is_group_manager': user.get('isGroupManager', False),
                                    'is_room_manager': user.get('isRoomManager', False),
                                    'is_audit_log': user.get('isAuditLog', False),
                                })
                                user_count += 1
                        
                        # Detail-Task mit Ergebnis aktualisieren
                        progress.update(
                            detail_task,
                            description=f"[{COLOR_SUCCESS}]✓ {display_name}: {user_count} emails | Total: {len(self.all_emails):,}"
                        )
                        
                    except Exception as e:
                        error_msg = str(e)[:50]
                        progress.update(
                            detail_task,
                            description=f"[{COLOR_ERROR}]✗ {display_name}: {error_msg}[/{COLOR_ERROR}]"
                        )
                    
                    # Haupt-Task fortschritt
                    progress.update(main_task, advance=1)
            
            # Abschluss-Meldung
            self.console.print(f"\n[{COLOR_SUCCESS}]✓ Collection complete![/{COLOR_SUCCESS}]")
            self.console.print(f"[{COLOR_PRIMARY}]Collected {len(self.all_emails):,} email addresses from {total_customers:,} customer(s)[/{COLOR_PRIMARY}]")
            
            if self.customer_limit and total_available > self.customer_limit:
                self.console.print(f"[{COLOR_DIM}]Note: {total_available - self.customer_limit:,} customers were skipped (limit applied)[/{COLOR_DIM}]\n")
            
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Error during collection: {str(e)}[/{COLOR_ERROR}]")
            import traceback
            traceback.print_exc()
            pause(self.console)
    
    def _show_results(self):
        """Zeigt eine Zusammenfassung der gesammelten E-Mails"""
        self.console.clear()
        show_header(self.console, "Email Collection Results")
        
        if not self.all_emails:
            self.console.print(f"[{COLOR_WARNING}]No email addresses found![/{COLOR_WARNING}]\n")
            return
        
        # Statistiken
        total_emails = len(self.all_emails)
        unique_customers = len(set(email['customer_id'] for email in self.all_emails))
        locked_users = sum(1 for email in self.all_emails if email.get('is_locked', False))
        
        self.console.print(f"[bold {COLOR_SUCCESS}]Collection Summary:[/bold {COLOR_SUCCESS}]\n")
        self.console.print(f"  [{COLOR_PRIMARY}]Total email addresses:[/{COLOR_PRIMARY}] {total_emails:,}")
        self.console.print(f"  [{COLOR_PRIMARY}]Customers processed:[/{COLOR_PRIMARY}] {unique_customers:,}")
        self.console.print(f"  [{COLOR_PRIMARY}]Locked users:[/{COLOR_PRIMARY}] {locked_users:,}")
        
        # Erste 10 E-Mails anzeigen
        self.console.print(f"\n[bold {COLOR_PRIMARY}]Preview (first 10 entries):[/bold {COLOR_PRIMARY}]\n")
        
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("Customer", width=18)
        table.add_column("Type", width=10)
        table.add_column("Max", justify="right", width=5)
        table.add_column("GB", justify="right", width=6)
        table.add_column("Since", width=11)
        table.add_column("Name", width=22)
        table.add_column("Email", width=30)
        table.add_column("Status", width=10)

        for email_data in self.all_emails[:10]:
            name = f"{email_data['first_name']} {email_data['last_name']}".strip()
            status = "Locked" if email_data.get('is_locked') else "Active"
            status_color = COLOR_ERROR if email_data.get('is_locked') else COLOR_SUCCESS
            cust_name = email_data['customer_name']

            table.add_row(
                cust_name[:16] + ".." if len(cust_name) > 16 else cust_name,
                email_data.get('contract_type', '')[:10],
                str(email_data.get('user_max', '')),
                str(email_data.get('quota_gb', '')),
                email_data.get('created_at', ''),
                name[:20] + ".." if len(name) > 20 else name,
                email_data['email'],
                f"[{status_color}]{status}[/{status_color}]"
            )
        
        self.console.print(table)
        
        if len(self.all_emails) > 10:
            self.console.print(f"\n[{COLOR_DIM}]... and {len(self.all_emails) - 10:,} more[/{COLOR_DIM}]")
    
    async def _export_emails(self):
        """Exportiert die E-Mails als CSV"""
        self.console.print(f"\n[bold {COLOR_PRIMARY}]Export Options:[/bold {COLOR_PRIMARY}]")
        
        if not Confirm.ask("Export to CSV?", default=True):
            return
        
        # Dateiname generieren
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"dracoon_emails_{timestamp}.csv"
        
        filename = Prompt.ask(
            f"[{COLOR_PRIMARY}]Filename[/{COLOR_PRIMARY}]",
            default=default_filename
        )
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # CSV Header
        headers = [
            'Customer ID',
            'Customer Name',
            'Contract Type',
            'User Max',
            'Quota GB',
            'Created At',
            'User ID',
            'First Name',
            'Last Name',
            'Email',
            'Username',
            'Is Locked',
            'Is Tenant Admin',
            'Is Config Manager',
            'Is User Manager',
            'Is Group Manager',
            'Is Room Manager',
            'Is Audit Log',
        ]

        # CSV Rows
        rows = [
            [
                email['customer_id'],
                email['customer_name'],
                email.get('contract_type', ''),
                email.get('user_max', ''),
                email.get('quota_gb', ''),
                email.get('created_at', ''),
                email['user_id'],
                email['first_name'],
                email['last_name'],
                email['email'],
                email['username'],
                'Yes' if email.get('is_locked') else 'No',
                'Yes' if email.get('is_admin') else 'No',
                'Yes' if email.get('is_config_manager') else 'No',
                'Yes' if email.get('is_user_manager') else 'No',
                'Yes' if email.get('is_group_manager') else 'No',
                'Yes' if email.get('is_room_manager') else 'No',
                'Yes' if email.get('is_audit_log') else 'No',
            ]
            for email in self.all_emails
        ]
        
        try:
            if export_to_csv(filename, headers, rows):
                self.console.print(f"\n[{COLOR_SUCCESS}]✓ Exported {len(rows):,} email addresses to: {filename}[/{COLOR_SUCCESS}]")
            else:
                self.console.print(f"\n[{COLOR_ERROR}]✗ Export failed![/{COLOR_ERROR}]")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]✗ Error: {str(e)}[/{COLOR_ERROR}]")


async def main(dracoon=None):
    """Entry point für das Modul"""
    # Dieses Modul benötigt keinen normalen DRACOON-Client
    # Es nutzt direkt die Provisioning API
    manager = CustomerEmailExport()
    await manager.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

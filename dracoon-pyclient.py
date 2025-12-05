#!/usr/bin/env python3
"""
Dracoon Pyclient - User-zu-Gruppe Manager
Interaktive Konsolen-Oberfläche zum Hinzufügen von Usern zu Gruppen

Teil des Dracoon Pyclient Projekts
https://github.com/ewald1976/dracoon-pyclient
"""

import requests
import sys
import os
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.layout import Layout
from rich import box
from dotenv import load_dotenv


class DracoonAPI:
    def __init__(self, base_url: str, client_id: str, client_secret: str, username: str, password: str):
        """Initialisiert die Dracoon API Verbindung mit OAuth Password Grant"""
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        
        # Access Token holen
        self.access_token = self._get_access_token()
        
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _get_access_token(self) -> str:
        """
        Holt einen Access Token mit OAuth Password Grant Flow
        Verwendet Client-ID, Client-Secret, Username und Password
        """
        url = f"{self.base_url}/oauth/token"
        
        data = {
            'grant_type': 'password',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = requests.post(
                url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data['access_token']
            else:
                error_msg = f"Token-Abruf fehlgeschlagen: {response.status_code}"
                try:
                    error_json = response.json()
                    error_msg += f"\n{error_json.get('error_description', error_json.get('error', response.text[:200]))}"
                except:
                    error_msg += f"\n{response.text[:300]}"
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Verbindungsfehler beim Token-Abruf: {str(e)}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Testet die API-Verbindung"""
        try:
            url = f"{self.base_url}/api/v4/user/account"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}"
            else:
                # Debug-Info
                error_detail = f"Status: {response.status_code}"
                try:
                    error_json = response.json()
                    error_detail += f"\n{error_json.get('message', error_json.get('error_description', response.text[:200]))}"
                except:
                    error_detail += f"\n{response.text[:300]}"
                return False, error_detail
        except Exception as e:
            return False, f"Verbindungsfehler: {str(e)}"
    
    def get_all_users(self, filter_str: Optional[str] = None) -> List[Dict]:
        """Holt alle Benutzer vom Dracoon-System"""
        users = []
        offset = 0
        limit = 500
        
        while True:
            url = f"{self.base_url}/api/v4/users"
            params = {'offset': offset, 'limit': limit}
            
            if filter_str:
                params['filter'] = filter_str
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Fehler beim Laden der Benutzer: {response.status_code}")
            
            data = response.json()
            items = data.get('items', [])
            users.extend(items)
            
            if len(items) < limit:
                break
            
            offset += limit
        
        return users
    
    def get_all_groups(self) -> List[Dict]:
        """Holt alle Gruppen vom Dracoon-System"""
        groups = []
        offset = 0
        limit = 500
        
        while True:
            url = f"{self.base_url}/api/v4/groups"
            params = {'offset': offset, 'limit': limit}
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Fehler beim Laden der Gruppen: {response.status_code}")
            
            data = response.json()
            items = data.get('items', [])
            groups.extend(items)
            
            if len(items) < limit:
                break
            
            offset += limit
        
        return groups
    
    def get_group_users(self, group_id: int) -> List[Dict]:
        """Holt alle Benutzer, die bereits in der Gruppe sind"""
        members = []
        offset = 0
        limit = 500
        
        while True:
            url = f"{self.base_url}/api/v4/groups/{group_id}/users"
            params = {'offset': offset, 'limit': limit}
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Fehler beim Laden der Gruppenmitglieder: {response.status_code}")
            
            data = response.json()
            items = data.get('items', [])
            members.extend(items)
            
            if len(items) < limit:
                break
            
            offset += limit
        
        return members
    
    def add_users_to_group(self, group_id: int, user_ids: List[int]) -> bool:
        """Fügt mehrere Benutzer zu einer Gruppe hinzu"""
        if not user_ids:
            return True
        
        url = f"{self.base_url}/api/v4/groups/{group_id}/users"
        payload = {"ids": user_ids}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            # 200, 201 und 204 sind alle erfolgreich
            if response.status_code in [200, 201, 204]:
                return True
            else:
                return False
                
        except Exception as e:
            return False


class DracoonTUI:
    def __init__(self):
        self.console = Console()
        self.api = None
        self.all_users = []
        self.all_groups = []
        self.selected_group = None
        self.group_members = []
    
    def clear(self):
        """Löscht den Bildschirm"""
        self.console.clear()
    
    def show_header(self):
        """Zeigt den Header"""
        self.console.print(Panel.fit(
            "[bold cyan]Dracoon Pyclient - User Manager[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()
    
    def connect(self):
        """Verbindungsaufbau"""
        self.clear()
        self.show_header()
        
        self.console.print("[bold]Verbindung zu Dracoon herstellen[/bold]\n")
        self.console.print("[dim]OAuth Password Grant Flow mit Client Credentials[/dim]\n")
        
        # Lade .env Datei
        load_dotenv()
        
        # Werte aus .env oder manuell eingeben
        base_url = os.getenv('DRACOON_BASE_URL')
        if not base_url:
            base_url = Prompt.ask("Dracoon URL", default="https://demo-hw.dracoon.com")
        else:
            self.console.print(f"[dim]Dracoon URL aus .env: {base_url}[/dim]")
        
        client_id = os.getenv('DRACOON_CLIENT_ID')
        if not client_id:
            self.console.print("\n[yellow]OAuth-App Credentials:[/yellow]")
            client_id = Prompt.ask("Client ID")
        else:
            self.console.print(f"[dim]Client ID aus .env: {client_id[:8]}...[/dim]")
        
        client_secret = os.getenv('DRACOON_CLIENT_SECRET')
        if not client_secret:
            client_secret = Prompt.ask("Client Secret", password=True)
        else:
            self.console.print(f"[dim]Client Secret aus .env: ********[/dim]")
        
        username = os.getenv('DRACOON_USERNAME')
        if not username:
            self.console.print("\n[yellow]Dein Dracoon-Login:[/yellow]")
            username = Prompt.ask("Benutzername")
        else:
            self.console.print(f"[dim]Benutzername aus .env: {username}[/dim]")
        
        password = os.getenv('DRACOON_PASSWORD')
        if not password:
            password = Prompt.ask("Passwort", password=True)
        else:
            self.console.print(f"[dim]Passwort aus .env: ********[/dim]")
        
        self.console.print("\n[yellow]Hole Access Token...[/yellow]")
        
        try:
            self.api = DracoonAPI(base_url, client_id, client_secret, username, password)
            
            self.console.print("[yellow]Teste Verbindung...[/yellow]")
            success, message = self.api.test_connection()
            
            if success:
                self.console.print(f"[green]✓ Verbunden als: {message}[/green]\n")
                return True
            else:
                self.console.print(f"[red]✗ {message}[/red]\n")
                if not Confirm.ask("Nochmal versuchen?"):
                    return False
                return self.connect()
                
        except Exception as e:
            self.console.print(f"[red]✗ Fehler: {str(e)}[/red]\n")
            if not Confirm.ask("Nochmal versuchen?"):
                return False
            return self.connect()
    
    def load_data(self):
        """Lädt Gruppen und Benutzer"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task1 = progress.add_task("[cyan]Lade Gruppen...", total=None)
            self.all_groups = self.api.get_all_groups()
            progress.update(task1, completed=True)
            
            task2 = progress.add_task("[cyan]Lade Benutzer...", total=None)
            self.all_users = self.api.get_all_users()
            progress.update(task2, completed=True)
        
        self.console.print(f"[green]✓ {len(self.all_groups)} Gruppen geladen[/green]")
        self.console.print(f"[green]✓ {len(self.all_users)} Benutzer geladen[/green]\n")
    
    def select_group(self):
        """Gruppenauswahl"""
        self.clear()
        self.show_header()
        
        self.console.print("[bold]Gruppe auswählen[/bold]\n")
        
        # Suche
        search = Prompt.ask("Suche nach Gruppe (Enter für alle)", default="")
        
        # Filter anwenden
        filtered_groups = [
            g for g in self.all_groups 
            if search.lower() in g['name'].lower()
        ]
        
        if not filtered_groups:
            self.console.print("[red]Keine Gruppen gefunden![/red]\n")
            Prompt.ask("Enter drücken um fortzufahren")
            return self.select_group()
        
        # Tabelle erstellen
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("#", style="dim", width=6)
        table.add_column("Gruppen-ID", width=12)
        table.add_column("Name")
        table.add_column("Mitglieder", justify="right")
        
        for idx, group in enumerate(filtered_groups, 1):
            table.add_row(
                str(idx),
                str(group['id']),
                group['name'],
                str(group.get('cntUsers', '?'))
            )
        
        self.console.print(table)
        self.console.print()
        
        # Auswahl
        choice = Prompt.ask(
            "Wähle Gruppe (Nummer aus Spalte '#')",
            default="1"
        )
        
        if choice.lower() == 's':
            return self.select_group()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(filtered_groups):
                self.selected_group = filtered_groups[idx]
                
                # Gruppenmitglieder laden
                self.console.print(f"\n[yellow]Lade Gruppenmitglieder...[/yellow]")
                self.group_members = self.api.get_group_users(self.selected_group['id'])
                self.console.print(f"[green]✓ {len(self.group_members)} Mitglieder in der Gruppe[/green]\n")
                
                return True
            else:
                self.console.print(f"[red]Ungültige Auswahl! Bitte eine Nummer zwischen 1 und {len(filtered_groups)} eingeben.[/red]\n")
                Prompt.ask("Enter drücken um fortzufahren")
                return self.select_group()
        except ValueError:
            self.console.print("[red]Ungültige Eingabe! Bitte nur Zahlen eingeben.[/red]\n")
            Prompt.ask("Enter drücken um fortzufahren")
            return self.select_group()
    
    def select_users(self):
        """Benutzerauswahl"""
        self.clear()
        self.show_header()
        
        self.console.print(f"[bold]Benutzer für Gruppe '[cyan]{self.selected_group['name']}[/cyan]' auswählen[/bold]\n")
        
        # Gruppenmitglieder-IDs
        member_ids = {m['id'] for m in self.group_members}
        
        # Menü
        self.console.print("[bold]Optionen:[/bold]")
        self.console.print("  [cyan]1[/cyan] - Alle Benutzer zur Gruppe hinzufügen")
        self.console.print("  [cyan]2[/cyan] - Nur Benutzer hinzufügen, die noch nicht in der Gruppe sind")
        self.console.print("  [cyan]3[/cyan] - Benutzer manuell auswählen")
        self.console.print("  [cyan]4[/cyan] - Andere Gruppe wählen")
        self.console.print("  [cyan]q[/cyan] - Beenden\n")
        
        choice = Prompt.ask("Auswahl", default="2")
        
        if choice == "1":
            users_to_add = self.all_users
        elif choice == "2":
            users_to_add = [u for u in self.all_users if u['id'] not in member_ids]
        elif choice == "3":
            users_to_add = self.manual_user_selection(member_ids)
            if users_to_add is None:
                return self.select_users()
        elif choice == "4":
            return self.select_group()
        elif choice.lower() == "q":
            return None
        else:
            self.console.print("[red]Ungültige Auswahl![/red]\n")
            Prompt.ask("Enter drücken um fortzufahren")
            return self.select_users()
        
        # Filtern: Nur User, die noch nicht in der Gruppe sind
        users_to_add = [u for u in users_to_add if u['id'] not in member_ids]
        
        if not users_to_add:
            self.console.print("\n[yellow]Alle ausgewählten Benutzer sind bereits in der Gruppe![/yellow]\n")
            Prompt.ask("Enter drücken um fortzufahren")
            return self.select_users()
        
        return users_to_add
    
    def manual_user_selection(self, member_ids):
        """Manuelle Benutzerauswahl mit Suche und Paginierung"""
        self.clear()
        self.show_header()
        
        self.console.print("[bold]Benutzer manuell auswählen[/bold]\n")
        
        # Suche
        search = Prompt.ask("Suche nach Benutzer (Name oder E-Mail, Enter für alle)", default="")
        
        # Filter anwenden
        filtered_users = [
            u for u in self.all_users
            if search.lower() in f"{u.get('firstName', '')} {u.get('lastName', '')}".lower()
            or search.lower() in u.get('email', '').lower()
        ]
        
        if not filtered_users:
            self.console.print("[red]Keine Benutzer gefunden![/red]\n")
            Prompt.ask("Enter drücken um fortzufahren")
            return None
        
        # Paginierung
        page_size = 20
        page = 0
        selected_ids = set()
        
        while True:
            self.clear()
            self.show_header()
            
            self.console.print(f"[bold]Benutzer auswählen ({len(selected_ids)} ausgewählt)[/bold]\n")
            
            start = page * page_size
            end = start + page_size
            page_users = filtered_users[start:end]
            
            # Tabelle erstellen
            table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
            table.add_column("#", style="dim", width=6)
            table.add_column("✓", width=3)
            table.add_column("Name", width=25)
            table.add_column("E-Mail", width=35)
            table.add_column("Status", width=15)
            
            for idx, user in enumerate(page_users, start + 1):
                is_selected = user['id'] in selected_ids
                is_in_group = user['id'] in member_ids
                
                check = "✓" if is_selected else " "
                status = "In Gruppe" if is_in_group else "Nicht in Gruppe"
                status_style = "dim" if is_in_group else "green"
                
                name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                email = user.get('email', '')
                
                table.add_row(
                    str(idx),
                    f"[bold cyan]{check}[/bold cyan]",
                    name[:25],
                    email[:35],
                    f"[{status_style}]{status}[/{status_style}]"
                )
            
            self.console.print(table)
            self.console.print()
            
            # Navigation
            self.console.print("[bold]Befehle:[/bold]")
            self.console.print("  [cyan]<Nummer>[/cyan] - User auswählen/abwählen")
            self.console.print("  [cyan]a[/cyan] - Alle auf dieser Seite auswählen")
            self.console.print("  [cyan]n[/cyan] - Nächste Seite")
            self.console.print("  [cyan]p[/cyan] - Vorherige Seite")
            self.console.print("  [cyan]d[/cyan] - Fertig (Auswahl übernehmen)")
            self.console.print("  [cyan]c[/cyan] - Abbrechen\n")
            
            total_pages = (len(filtered_users) + page_size - 1) // page_size
            self.console.print(f"Seite {page + 1} von {total_pages}\n")
            
            cmd = Prompt.ask("Befehl")
            
            if cmd.lower() == 'n' and end < len(filtered_users):
                page += 1
            elif cmd.lower() == 'p' and page > 0:
                page -= 1
            elif cmd.lower() == 'a':
                for user in page_users:
                    if user['id'] not in member_ids:
                        selected_ids.add(user['id'])
            elif cmd.lower() == 'd':
                if not selected_ids:
                    self.console.print("[yellow]Keine Benutzer ausgewählt![/yellow]\n")
                    Prompt.ask("Enter drücken um fortzufahren")
                    continue
                return [u for u in self.all_users if u['id'] in selected_ids]
            elif cmd.lower() == 'c':
                return None
            else:
                try:
                    # Die eingegebene Nummer entspricht der absoluten Position
                    idx = int(cmd) - 1
                    
                    # Prüfe ob die Nummer im Bereich der aktuellen Seite liegt
                    if start <= idx < end and idx < len(filtered_users):
                        user = filtered_users[idx]
                        if user['id'] in member_ids:
                            self.console.print("[yellow]User ist bereits in der Gruppe![/yellow]")
                            Prompt.ask("Enter drücken um fortzufahren")
                            continue
                        
                        if user['id'] in selected_ids:
                            selected_ids.remove(user['id'])
                        else:
                            selected_ids.add(user['id'])
                    else:
                        self.console.print("[red]Ungültige Nummer! Bitte eine Nummer von dieser Seite wählen.[/red]")
                        Prompt.ask("Enter drücken um fortzufahren")
                except ValueError:
                    self.console.print("[red]Ungültige Eingabe![/red]")
                    Prompt.ask("Enter drücken um fortzufahren")
    
    def add_users(self, users_to_add):
        """Fügt Benutzer zur Gruppe hinzu"""
        self.console.print(f"\n[bold]Zusammenfassung:[/bold]")
        self.console.print(f"  Gruppe: [cyan]{self.selected_group['name']}[/cyan]")
        self.console.print(f"  Benutzer: [cyan]{len(users_to_add)}[/cyan]\n")
        
        if not Confirm.ask("Benutzer jetzt hinzufügen?"):
            return
        
        user_ids = [u['id'] for u in users_to_add]
        batch_size = 100
        success_count = 0
        failed_batches = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                f"[cyan]Füge {len(user_ids)} Benutzer hinzu...",
                total=len(user_ids)
            )
            
            for i in range(0, len(user_ids), batch_size):
                batch = user_ids[i:i + batch_size]
                batch_num = i//batch_size + 1
                
                try:
                    if self.api.add_users_to_group(self.selected_group['id'], batch):
                        success_count += len(batch)
                        progress.update(task, advance=len(batch))
                    else:
                        failed_batches.append(batch_num)
                        self.console.print(f"[red]✗ Fehler bei Batch {batch_num}[/red]")
                        
                        # Versuche detaillierten Fehler zu bekommen
                        url = f"{self.api.base_url}/api/v4/groups/{self.selected_group['id']}/users"
                        payload = {"ids": batch}
                        response = requests.post(url, headers=self.api.headers, json=payload, timeout=30)
                        
                        try:
                            error_json = response.json()
                            error_msg = error_json.get('message', error_json.get('error_description', 'Unbekannter Fehler'))
                            self.console.print(f"[yellow]  → {error_msg}[/yellow]")
                        except:
                            self.console.print(f"[yellow]  → Status: {response.status_code}[/yellow]")
                            
                except Exception as e:
                    failed_batches.append(batch_num)
                    self.console.print(f"[red]✗ Exception bei Batch {batch_num}: {str(e)}[/red]")
        
        self.console.print(f"\n[green]✓ {success_count} von {len(user_ids)} Benutzern erfolgreich hinzugefügt![/green]")
        
        if failed_batches:
            self.console.print(f"[yellow]⚠ Fehler bei Batches: {', '.join(map(str, failed_batches))}[/yellow]")
        
        self.console.print()
        Prompt.ask("Enter drücken um fortzufahren")
    
    def run(self):
        """Hauptschleife"""
        try:
            # Verbindung herstellen
            if not self.connect():
                return
            
            # Daten laden
            self.console.print()
            self.load_data()
            Prompt.ask("Enter drücken um fortzufahren")
            
            # Hauptschleife
            while True:
                # Gruppe auswählen
                if not self.select_group():
                    continue
                
                # Benutzer auswählen
                users_to_add = self.select_users()
                if users_to_add is None:
                    break
                
                # Benutzer hinzufügen
                self.add_users(users_to_add)
                
                # Weitermachen?
                if not Confirm.ask("\nWeitere Benutzer hinzufügen?"):
                    break
            
            self.console.print("\n[cyan]Auf Wiedersehen![/cyan]\n")
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Abgebrochen durch Benutzer[/yellow]\n")
        except Exception as e:
            self.console.print(f"\n[red]Fehler: {str(e)}[/red]\n")


def main():
    tui = DracoonTUI()
    tui.run()


if __name__ == "__main__":
    main()

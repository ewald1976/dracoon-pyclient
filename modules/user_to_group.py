#!/usr/bin/env python3
"""
Dracoon Pyclient - User-zu-Gruppe Manager
Interaktive Konsolen-Oberfläche zum Hinzufügen von Usern zu Gruppen
"""

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from dracoon import DRACOON

from lib import (
    show_header, pause,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_DIM, TABLE_BOX
)


class UserToGroupManager:
    def __init__(self, dracoon: DRACOON):
        self.dracoon = dracoon
        self.console = Console()
        self.all_users = []
        self.all_groups = []
        self.selected_group = None
        self.group_members = []
    
    async def run(self):
        """Hauptfunktion des Moduls"""
        try:
            self.console.clear()
            show_header(self.console, "Dracoon Pyclient - User-zu-Gruppe Manager")
            await self._load_data()
            pause(self.console)
            
            while True:
                if not await self._select_group():
                    continue
                
                users_to_add = await self._select_users()
                if not users_to_add:
                    continue
                
                await self._add_users(users_to_add)
                
                if not Confirm.ask("\nWeitere Benutzer hinzufügen?"):
                    break
            
            self.console.print(f"\n[{COLOR_PRIMARY}]Zurück zum Hauptmenü...[/{COLOR_PRIMARY}]\n")
            
        except KeyboardInterrupt:
            self.console.print(f"\n\n[{COLOR_WARNING}]Abgebrochen durch Benutzer[/{COLOR_WARNING}]\n")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Fehler: {str(e)}[/{COLOR_ERROR}]\n")
            pause(self.console)
    
    async def _load_data(self):
        """Lädt Gruppen und Benutzer"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task1 = progress.add_task(f"[{COLOR_PRIMARY}]Lade Gruppen...[/{COLOR_PRIMARY}]", total=None)
            groups_response = await self.dracoon.groups.get_groups()
            self.all_groups = groups_response.items
            progress.update(task1, completed=True)
            
            task2 = progress.add_task(f"[{COLOR_PRIMARY}]Lade Benutzer...[/{COLOR_PRIMARY}]", total=None)
            users_response = await self.dracoon.users.get_users()
            self.all_users = users_response.items
            progress.update(task2, completed=True)
        
        self.console.print(f"[{COLOR_SUCCESS}]✓ {len(self.all_groups)} Gruppen geladen[/{COLOR_SUCCESS}]")
        self.console.print(f"[{COLOR_SUCCESS}]✓ {len(self.all_users)} Benutzer geladen[/{COLOR_SUCCESS}]\n")
    
    async def _select_group(self):
        """Gruppenauswahl"""
        self.console.clear()
        show_header(self.console, "Dracoon Pyclient - User-zu-Gruppe Manager")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Gruppe auswählen[/bold {COLOR_PRIMARY}]\n")
        
        search = Prompt.ask(f"[{COLOR_PRIMARY}]Suche nach Gruppe (Enter für alle)[/{COLOR_PRIMARY}]", default="")
        
        filtered_groups = [g for g in self.all_groups if search.lower() in g.name.lower()]
        
        if not filtered_groups:
            self.console.print(f"[{COLOR_ERROR}]Keine Gruppen gefunden![/{COLOR_ERROR}]\n")
            pause(self.console)
            return await self._select_group()
        
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("#", style=COLOR_DIM, width=6)
        table.add_column("Gruppen-ID", width=12)
        table.add_column("Name", width=50)
        table.add_column("Mitglieder", justify="right", width=12)
        
        for idx, group in enumerate(filtered_groups, 1):
            cnt = getattr(group, 'cntUsers', 0)
            table.add_row(str(idx), str(group.id), group.name, str(cnt if cnt else 0))
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(f"[{COLOR_PRIMARY}]Wähle Gruppe (Nummer)[/{COLOR_PRIMARY}]", default="1")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(filtered_groups):
                self.selected_group = filtered_groups[idx]
                
                self.console.print(f"\n[{COLOR_WARNING}]Lade Gruppenmitglieder...[/{COLOR_WARNING}]")
                members_response = await self.dracoon.groups.get_group_users(group_id=self.selected_group.id)
                self.group_members = members_response.items
                self.console.print(f"[{COLOR_SUCCESS}]✓ {len(self.group_members)} Mitglieder in der Gruppe[/{COLOR_SUCCESS}]\n")
                
                return True
            else:
                self.console.print(f"[{COLOR_ERROR}]Ungültige Auswahl![/{COLOR_ERROR}]\n")
                pause(self.console)
                return await self._select_group()
        except ValueError:
            self.console.print(f"[{COLOR_ERROR}]Ungültige Eingabe![/{COLOR_ERROR}]\n")
            pause(self.console)
            return await self._select_group()
    
    async def _select_users(self):
        """Benutzerauswahl"""
        self.console.clear()
        show_header(self.console, "Dracoon Pyclient - User-zu-Gruppe Manager")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Benutzer für Gruppe '[{COLOR_PRIMARY}]{self.selected_group.name}[/{COLOR_PRIMARY}]' auswählen[/bold {COLOR_PRIMARY}]\n")
        
        member_ids = {
            getattr(m, 'userInfo', getattr(m, 'id', None)).id 
            for m in self.group_members 
            if getattr(m, 'userInfo', None) or getattr(m, 'id', None)
        }
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Optionen:[/bold {COLOR_PRIMARY}]")
        self.console.print(f"  [{COLOR_PRIMARY}]1[/{COLOR_PRIMARY}] - Alle Benutzer hinzufügen (überspringe bereits vorhandene)")
        self.console.print(f"  [{COLOR_PRIMARY}]2[/{COLOR_PRIMARY}] - Einzelne Benutzer auswählen")
        self.console.print(f"  [{COLOR_PRIMARY}]3[/{COLOR_PRIMARY}] - Andere Gruppe wählen\n")
        
        choice = Prompt.ask("Auswahl", default="1")
        
        if choice == "1":
            # Alle User die noch nicht in der Gruppe sind
            users_to_add = [u for u in self.all_users if u.id not in member_ids]
        elif choice == "2":
            # Einzelne User auswählen
            users_to_add = await self._select_individual_users(member_ids)
            if not users_to_add:
                return await self._select_users()
        elif choice == "3":
            return await self._select_group()
        else:
            self.console.print(f"[{COLOR_ERROR}]Ungültige Auswahl![/{COLOR_ERROR}]\n")
            pause(self.console)
            return await self._select_users()
        
        # Nochmal filtern (Sicherheit) - User die schon Mitglied sind werden übersprungen
        users_to_add = [u for u in users_to_add if u.id not in member_ids]
        
        if not users_to_add:
            self.console.print(f"\n[{COLOR_WARNING}]Alle ausgewählten Benutzer sind bereits in der Gruppe![/{COLOR_WARNING}]\n")
            pause(self.console)
            return await self._select_users()
        
        return users_to_add
    
    async def _select_individual_users(self, member_ids: set) -> list:
        """Ermöglicht die Auswahl einzelner Benutzer"""
        self.console.clear()
        show_header(self.console, "Dracoon Pyclient - User-zu-Gruppe Manager")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Einzelne Benutzer für Gruppe '[{COLOR_PRIMARY}]{self.selected_group.name}[/{COLOR_PRIMARY}]' auswählen[/bold {COLOR_PRIMARY}]\n")
        
        # Filtere User die noch nicht in der Gruppe sind
        available_users = [u for u in self.all_users if u.id not in member_ids]
        
        if not available_users:
            self.console.print(f"[{COLOR_WARNING}]Alle Benutzer sind bereits in der Gruppe![/{COLOR_WARNING}]")
            pause(self.console)
            return []
        
        self.console.print(f"[{COLOR_PRIMARY}]Suche nach Benutzern[/{COLOR_PRIMARY}]")
        search = Prompt.ask(f"[{COLOR_PRIMARY}]Name oder E-Mail (Enter für Liste)[/{COLOR_PRIMARY}]", default="")
        
        if search:
            filtered_users = [
                u for u in available_users
                if search.lower() in f"{getattr(u, 'firstName', '')} {getattr(u, 'lastName', '')}".lower()
                or search.lower() in getattr(u, 'email', '').lower()
                or search.lower() in getattr(u, 'userName', '').lower()
            ]
        else:
            filtered_users = available_users
        
        if not filtered_users:
            self.console.print(f"[{COLOR_ERROR}]Keine passenden Benutzer gefunden![/{COLOR_ERROR}]")
            pause(self.console)
            return []
        
        # Zeige User in Tabelle
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("#", style=COLOR_DIM, width=6)
        table.add_column("Name", width=30)
        table.add_column("E-Mail", width=40)
        table.add_column("Username", width=20)
        
        display_users = filtered_users[:20]
        
        for idx, user in enumerate(display_users, 1):
            first_name = getattr(user, 'firstName', '')
            last_name = getattr(user, 'lastName', '')
            name = f"{first_name} {last_name}".strip()
            
            table.add_row(
                str(idx),
                name if name else '-',
                getattr(user, 'email', ''),
                getattr(user, 'userName', '')
            )
        
        self.console.print(table)
        
        if len(filtered_users) > 20:
            self.console.print(f"\n[{COLOR_WARNING}]Hinweis: {len(filtered_users) - 20} weitere Benutzer nicht angezeigt.[/{COLOR_WARNING}]")
        
        self.console.print()
        self.console.print(f"[{COLOR_PRIMARY}]Wähle Benutzer:[/{COLOR_PRIMARY}]")
        self.console.print(f"  - Einzelne Nummer: z.B. '5'")
        self.console.print(f"  - Mehrere Nummern: z.B. '1,3,5'")
        self.console.print(f"  - Bereich: z.B. '1-5'")
        self.console.print(f"  - Kombiniert: z.B. '1,3,5-8'")
        self.console.print(f"  - 's' für neue Suche\n")
        
        choice = Prompt.ask("Auswahl")
        
        if choice.lower() == 's':
            return await self._select_individual_users(member_ids)
        
        try:
            selected_indices = set()
            parts = choice.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Bereich
                    start, end = part.split('-')
                    selected_indices.update(range(int(start), int(end) + 1))
                else:
                    # Einzelne Nummer
                    selected_indices.add(int(part))
            
            selected_users = []
            for idx in selected_indices:
                if 1 <= idx <= len(display_users):
                    selected_users.append(display_users[idx - 1])
            
            if not selected_users:
                self.console.print(f"[{COLOR_ERROR}]Keine gültigen Benutzer ausgewählt![/{COLOR_ERROR}]")
                pause(self.console)
                return []
            
            # Bestätigung
            self.console.print(f"\n[{COLOR_SUCCESS}]{len(selected_users)} Benutzer ausgewählt:[/{COLOR_SUCCESS}]")
            for user in selected_users:
                first_name = getattr(user, 'firstName', '')
                last_name = getattr(user, 'lastName', '')
                name = f"{first_name} {last_name}".strip()
                self.console.print(f"  - {name} ({getattr(user, 'email', '')})")
            
            self.console.print()
            if Confirm.ask("Diese Benutzer hinzufügen?"):
                return selected_users
            else:
                return await self._select_individual_users(member_ids)
            
        except (ValueError, IndexError):
            self.console.print(f"[{COLOR_ERROR}]Ungültige Eingabe![/{COLOR_ERROR}]")
            pause(self.console)
            return await self._select_individual_users(member_ids)
    
    async def _add_users(self, users_to_add):
        """Fügt Benutzer zur Gruppe hinzu"""
        self.console.print(f"\n[bold {COLOR_PRIMARY}]Zusammenfassung:[/bold {COLOR_PRIMARY}]")
        self.console.print(f"  Gruppe: [{COLOR_PRIMARY}]{self.selected_group.name}[/{COLOR_PRIMARY}]")
        self.console.print(f"  Benutzer: [{COLOR_PRIMARY}]{len(users_to_add)}[/{COLOR_PRIMARY}]\n")
        
        if not Confirm.ask("Benutzer jetzt hinzufügen?"):
            return
        
        success_count = 0
        failed_count = 0
        failed_users = []  # Liste der fehlgeschlagenen User
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                f"[{COLOR_PRIMARY}]Füge {len(users_to_add)} Benutzer einzeln hinzu...[/{COLOR_PRIMARY}]",
                total=len(users_to_add)
            )
            
            # Füge jeden User einzeln hinzu
            for user in users_to_add:
                # Unterdrücke SDK-Log-Ausgaben
                import sys
                import io
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                try:
                    await self.dracoon.groups.add_group_users(
                        group_id=self.selected_group.id,
                        user_list=[user.id],
                        raise_on_err=True  # Damit wir echte API-Fehler fangen
                    )
                    # Wenn wir hier ankommen, war es erfolgreich
                    success_count += 1
                        
                except Exception as e:
                    error_msg = str(e)
                    # Ignoriere nur Pydantic-Fehler (User wurde trotzdem hinzugefügt)
                    if "validation error" in error_msg.lower():
                        success_count += 1
                    else:
                        # Echter Fehler
                        failed_count += 1
                        first_name = getattr(user, 'firstName', '')
                        last_name = getattr(user, 'lastName', '')
                        user_name = f"{first_name} {last_name}".strip()
                        email = getattr(user, 'email', '')
                        failed_users.append({
                            'name': user_name if user_name else email,
                            'email': email,
                            'id': user.id,
                            'error': error_msg[:100]
                        })
                finally:
                    sys.stderr = old_stderr
                
                progress.update(task, advance=1)
        
        # Ergebnis ausgeben
        self.console.print(f"\n[{COLOR_SUCCESS}]✓ {success_count} von {len(users_to_add)} Benutzern erfolgreich hinzugefügt![/{COLOR_SUCCESS}]")
        
        if failed_count > 0:
            self.console.print(f"[{COLOR_ERROR}]✗ {failed_count} Benutzer konnten nicht hinzugefügt werden:[/{COLOR_ERROR}]\n")
            
            # Zeige fehlgeschlagene User in Tabelle
            from rich.table import Table
            table = Table(show_header=True, header_style=f"bold {COLOR_ERROR}", box=TABLE_BOX)
            table.add_column("Name", width=30)
            table.add_column("E-Mail", width=35)
            table.add_column("User-ID", style=COLOR_DIM, width=10)
            
            for failed_user in failed_users:
                table.add_row(
                    failed_user['name'],
                    failed_user['email'],
                    str(failed_user['id'])
                )
            
            self.console.print(table)
            self.console.print(f"\n[{COLOR_DIM}]Hinweis: Diese User können z.B. Gastbenutzer sein oder spezielle Berechtigungen haben.[/{COLOR_DIM}]")
        
        self.console.print()
        pause(self.console)


def main(dracoon: DRACOON):
    """Entry Point für das Modul"""
    manager = UserToGroupManager(dracoon)
    return manager.run()
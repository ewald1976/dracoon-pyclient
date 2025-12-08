#!/usr/bin/env python3
"""
Dracoon Pyclient - Room Admin Report Modul
Zeigt an, in welchen Räumen ein User Room-Admin ist und bietet Löschfunktion
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Confirm
from datetime import datetime
import os

from dracoon import DRACOON

from lib import (
    show_header, search_and_select_user, pause,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_DIM, TABLE_BOX
)


class RoomAdminReport:
    def __init__(self, dracoon: DRACOON):
        self.dracoon = dracoon
        self.console = Console()
        self.god_mode = getattr(dracoon, "god_mode", False)
    
    async def run(self):
        """Hauptfunktion des Moduls"""
        try:
            self.console.clear()
            show_header(self.console, "Dracoon Pyclient - Room Admin Report")
            
            if self.god_mode:
                self.console.print(f"[{COLOR_ERROR}]⚠️  GOD-MODE ACTIVE - Rooms will be deleted without confirmation! ⚠️[/{COLOR_ERROR}]\n")
            
            self.console.print(f"[bold {COLOR_PRIMARY}]This module shows in which rooms a user is Room-Admin.[/bold {COLOR_PRIMARY}]")
            self.console.print(f"[{COLOR_DIM}]Useful for preparing user deletion.[/{COLOR_DIM}]\n")
            
            self.console.print(f"[{COLOR_WARNING}]Loading user list...[/{COLOR_WARNING}]")
            users_response = await self.dracoon.users.get_users()
            all_users = users_response.items
            self.console.print(f"[{COLOR_SUCCESS}]✓ {len(all_users)} users loaded[/{COLOR_SUCCESS}]\n")
            
            pause(self.console)
            
            while True:
                self.console.clear()
                show_header(self.console, "Dracoon Pyclient - Room Admin Report")
                
                all_users_dict = [
                    {
                        'id': u.id,
                        'firstName': getattr(u, 'firstName', ''),
                        'lastName': getattr(u, 'lastName', ''),
                        'email': getattr(u, 'email', ''),
                        'userName': getattr(u, 'userName', '')
                    }
                    for u in all_users
                ]
                
                selected_user = search_and_select_user(self.console, all_users_dict, "Select a user")
                
                if not selected_user:
                    self.console.print(f"[{COLOR_WARNING}]No selection made.[/{COLOR_WARNING}]")
                    pause(self.console)
                    if not Confirm.ask("\nCheck another user?"):
                        break
                    continue
                
                user_name = f"{selected_user.get('firstName', '')} {selected_user.get('lastName', '')}".strip()
                user_email = selected_user.get('email', '')
                user_id = selected_user['id']
                
                self.console.print(f"\n[bold {COLOR_PRIMARY}]Selected User:[/bold {COLOR_PRIMARY}]")
                self.console.print(f"  Name: [{COLOR_PRIMARY}]{user_name}[/{COLOR_PRIMARY}]")
                self.console.print(f"  E-Mail: [{COLOR_PRIMARY}]{user_email}[/{COLOR_PRIMARY}]")
                self.console.print(f"  User-ID: [{COLOR_PRIMARY}]{user_id}[/{COLOR_PRIMARY}]\n")
             
                self.console.print(f"[{COLOR_WARNING}]Searching for rooms with admin permissions...[/{COLOR_WARNING}]")
                self.console.print(f"[{COLOR_DIM}]This may take some time...[/{COLOR_DIM}]\n")
                
                admin_rooms = await self._find_admin_rooms(user_id)
                
                if not admin_rooms:
                    self.console.print(f"\n[{COLOR_SUCCESS}]✓ User '{user_name}' ist in keinem Raum als letzter Admin eingetragen.[/{COLOR_SUCCESS}]")
                    self.console.print(f"[{COLOR_SUCCESS}]The user can be deleted without issues.[/{COLOR_SUCCESS}]\n")
                else:
                    self._display_results(user_name, user_email, admin_rooms)
                    
                    if Confirm.ask("\nExport as CSV?"):
                        self._export_csv(user_name, user_email, admin_rooms)
                    
                    if self.god_mode:
                        self.console.print(
                            f"\n[bold {COLOR_ERROR}]GOD-MODE active:[/bold {COLOR_ERROR}] "
                            "All listed data rooms will be deleted without further confirmation."
                        )
                        await self._delete_last_admin_rooms(user_name, admin_rooms)
                    else:
                        if Confirm.ask(f"\n[bold {COLOR_ERROR}]Do you want to delete the data rooms where the user is the last Room-Admin?[/bold {COLOR_ERROR}]"):
                            await self._delete_last_admin_rooms(user_name, admin_rooms)
                
                if not Confirm.ask("\nCheck another user?"):
                    break
            
            self.console.print(f"\n[{COLOR_PRIMARY}]Back to main menu...[/{COLOR_PRIMARY}]\n")
            
        except KeyboardInterrupt:
            self.console.print(f"\n\n[{COLOR_WARNING}]Cancelled by user[/{COLOR_WARNING}]\n")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Error: {str(e)}[/{COLOR_ERROR}]\n")
            pause(self.console)
    
    async def _find_admin_rooms(self, user_id: int) -> list:
        """Sucht alle Räume, in denen der User LETZTER Room-Admin ist"""
        admin_rooms = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:

            task = progress.add_task(
                f"[{COLOR_PRIMARY}]Querying DRACOON for rooms...[/{COLOR_PRIMARY}]",
                total=None
            )

            try:
                response = await self.dracoon.users.get_user_last_admin_rooms(user_id=user_id)
                progress.update(task, completed=True)
            except Exception as e:
                self.console.print(f"[{COLOR_ERROR}]Error during query: {e}[/{COLOR_ERROR}]")
                return []

            for room in getattr(response, "items", []):
                admin_rooms.append({
                    "id": room.id,
                    "name": room.name,
                    "parentPath": getattr(room, "parentPath", "/"),
                })

        return admin_rooms
    
    async def _delete_last_admin_rooms(self, user_name: str, admin_rooms: list) -> None:
        """Löscht Datenräume, in denen der User letzter Room-Admin ist"""
        if not admin_rooms:
            return

        self.console.print("\n" + "=" * 100)
        self.console.print(f"[bold {COLOR_ERROR}]Delete Operation: Data Rooms with Last Room-Admin[/bold {COLOR_ERROR}]")
        self.console.print("=" * 100)

        self.console.print(
            f"User: [{COLOR_PRIMARY}]{user_name}[/{COLOR_PRIMARY}] is last Room-Admin in "
            f"[bold {COLOR_WARNING}]{len(admin_rooms)}[/bold {COLOR_WARNING}] room(s)."
        )

        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("Room-ID", style=COLOR_DIM, width=10)
        table.add_column("Room Name", width=40)
        table.add_column("Path", width=40)

        for room in admin_rooms:
            room_id = room.get("id")
            name = room.get("name", "")
            parent_path = room.get("parentPath", "/") or "/"
            full_path = f"{parent_path}{name}"
            table.add_row(str(room_id), name, full_path)

        self.console.print()
        self.console.print(table)
        self.console.print()

        deleted = []
        failed = []

        if self.god_mode:
            for room in admin_rooms:
                room_id = room.get("id")
                name = room.get("name", "")
                parent_path = room.get("parentPath", "/") or "/"
                full_path = f"{parent_path}{name}"
                
                try:
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console) as progress:
                        task = progress.add_task(f"[{COLOR_ERROR}]Deleting room {full_path} (ID {room_id})...[/{COLOR_ERROR}]", total=None)
                        await self.dracoon.nodes.delete_nodes(node_list=[room_id])
                        progress.update(task, completed=True)

                    self.console.print(f"[{COLOR_SUCCESS}]✓ Room deleted (God-Mode):[/{COLOR_SUCCESS}] [{COLOR_PRIMARY}]{full_path}[/{COLOR_PRIMARY}]")
                    deleted.append(room_id)
                except Exception as e:
                    self.console.print(f"[{COLOR_ERROR}]✗ Deletion failed for room ID {room_id}: {e}[/{COLOR_ERROR}]")
                    failed.append(room_id)
        else:
            for room in admin_rooms:
                room_id = room.get("id")
                name = room.get("name", "")
                parent_path = room.get("parentPath", "/") or "/"
                full_path = f"{parent_path}{name}"

                self.console.print("\n" + "-" * 100)
                self.console.print(f"[bold {COLOR_PRIMARY}]Data Room:[/bold {COLOR_PRIMARY}] [{COLOR_PRIMARY}]{full_path}[/{COLOR_PRIMARY}] (ID: [{COLOR_WARNING}]{room_id}[/{COLOR_WARNING}])")
                self.console.print(f"[{COLOR_ERROR}]The room and all its contents will be permanently deleted.[/{COLOR_ERROR}]")

                if not Confirm.ask(f"[bold {COLOR_ERROR}]Delete this data room?[/bold {COLOR_ERROR}]"):
                    self.console.print(f"[{COLOR_WARNING}]→ Room will NOT be deleted.[/{COLOR_WARNING}]")
                    continue

                if not Confirm.ask(f"[bold {COLOR_ERROR}]Are you sure? This action cannot be undone.[/bold {COLOR_ERROR}]"):
                    self.console.print(f"[{COLOR_WARNING}]→ Safety check cancelled, room will remain.[/{COLOR_WARNING}]")
                    continue

                try:
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console) as progress:
                        task = progress.add_task(f"[{COLOR_ERROR}]Deleting room {full_path} (ID {room_id})...[/{COLOR_ERROR}]", total=None)
                        await self.dracoon.nodes.delete_nodes(node_list=[room_id])
                        progress.update(task, completed=True)

                    self.console.print(f"[{COLOR_SUCCESS}]✓ Room deleted:[/{COLOR_SUCCESS}] [{COLOR_PRIMARY}]{full_path}[/{COLOR_PRIMARY}]")
                    deleted.append(room_id)
                except Exception as e:
                    self.console.print(f"[{COLOR_ERROR}]✗ Deletion failed for room ID {room_id}: {e}[/{COLOR_ERROR}]")
                    failed.append(room_id)

        self.console.print("\n" + "=" * 100)
        self.console.print(f"[bold {COLOR_PRIMARY}]Deletion Summary:[/bold {COLOR_PRIMARY}]")
        self.console.print(f"[{COLOR_SUCCESS}]Deleted rooms:[/{COLOR_SUCCESS}] {len(deleted)}")
        self.console.print(f"[{COLOR_ERROR}]Failed deletion attempts:[/{COLOR_ERROR}] {len(failed)}")
        self.console.print("=" * 100 + "\n")
    
    def _display_results(self, user_name: str, user_email: str, admin_rooms: list):
        """Zeigt die Ergebnisse in einer Tabelle an"""
        self.console.print("\n" + "=" * 100)
        self.console.print(f"[bold {COLOR_PRIMARY}]Room Admin Report[/bold {COLOR_PRIMARY}]")
        self.console.print("=" * 100)
        self.console.print(f"Username:  {user_name}")
        self.console.print(f"Email:     {user_email}")
        self.console.print(f"Date:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.console.print(f"API-URL:   {self.dracoon.client.base_url}")
        self.console.print("=" * 100 + "\n")
        
        if not admin_rooms:
            self.console.print(f"[{COLOR_SUCCESS}]User is not registered as last admin in any room.[/{COLOR_SUCCESS}]")
            return
        
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("Room-ID", style=COLOR_DIM, width=10)
        table.add_column("Room Name", width=40)
        table.add_column("Path", width=40)
        
        for room in admin_rooms:
            table.add_row(str(room['id']), room['name'], room.get('parentPath', '/'))
        
        self.console.print(table)
        
        self.console.print(f"\n[bold {COLOR_ERROR}]⚠  Note:[/bold {COLOR_ERROR}]")
        self.console.print("The user cannot be deleted as long as they are the last Room-Admin in these rooms.")
        self.console.print("Solution according to DRACOON: Delete room OR make another user admin first.")
    
    def _export_csv(self, user_name: str, user_email: str, admin_rooms: list):
        """Exportiert die Ergebnisse als CSV"""
        exports_dir = "exports"
        if not os.path.exists(exports_dir):
            os.makedirs(exports_dir)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        safe_username = "".join(c for c in user_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_username = safe_username.replace(' ', '_')
        filename = f"{safe_username}_last_admin_rooms_{timestamp}.csv"
        filepath = os.path.join(exports_dir, filename)
        
        header_rows = [
            ["Room Admin Report - Last Admin Rights"],
            ["Username", user_name],
            ["Email", user_email],
            ["Datum", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["API-URL", self.dracoon.client.base_url],
            [],
            ["Room-ID", "Room Name", "Path"]
        ]
        
        room_rows = [[room['id'], room['name'], room.get('parentPath', '/')] for room in admin_rooms]
        
        try:
            import csv
            with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(header_rows)
                writer.writerows(room_rows)
            
            self.console.print(f"\n[{COLOR_SUCCESS}]✓ CSV exported to:[/{COLOR_SUCCESS}] [{COLOR_PRIMARY}]{filepath}[/{COLOR_PRIMARY}]")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]✗ Error during CSV export: {str(e)}[/{COLOR_ERROR}]")


def main(dracoon: DRACOON):
    """Entry Point für das Modul"""
    report = RoomAdminReport(dracoon)
    return report.run()

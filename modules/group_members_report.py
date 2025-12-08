#!/usr/bin/env python3
"""
Dracoon Pyclient - List Group Members
Zeigt alle Members einer Group an und exportiert optional als CSV
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime
import os

from dracoon import DRACOON

from lib import (
    show_header, pause,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_DIM, TABLE_BOX
)


class GroupMembersReport:
    def __init__(self, dracoon: DRACOON):
        self.dracoon = dracoon
        self.console = Console()
        self.all_groups = []
    
    async def run(self):
        """Hauptfunktion des Moduls"""
        try:
            self.console.clear()
            show_header(self.console, "Dracoon Pyclient - List Group Members")
            
            self.console.print(f"[bold {COLOR_PRIMARY}]This module lists all members of a group.[/bold {COLOR_PRIMARY}]")
            self.console.print(f"[{COLOR_DIM}]Optional with CSV export.[/{COLOR_DIM}]\n")
            
            self.console.print(f"[{COLOR_WARNING}]Loading groups...[/{COLOR_WARNING}]")
            groups_response = await self.dracoon.groups.get_groups()
            self.all_groups = groups_response.items
            self.console.print(f"[{COLOR_SUCCESS}]✓ {len(self.all_groups)} groups loaded[/{COLOR_SUCCESS}]\n")
            
            pause(self.console)
            
            while True:
                self.console.clear()
                show_header(self.console, "Dracoon Pyclient - List Group Members")
                
                selected_group = await self._select_group()
                
                if not selected_group:
                    self.console.print(f"[{COLOR_WARNING}]No selection made.[/{COLOR_WARNING}]")
                    pause(self.console)
                    if not Confirm.ask("\nCheck another group?"):
                        break
                    continue
                
                group_name = selected_group.name
                group_id = selected_group.id
                
                self.console.print(f"\n[bold {COLOR_PRIMARY}]Selected Group:[/bold {COLOR_PRIMARY}]")
                self.console.print(f"  Name: [{COLOR_PRIMARY}]{group_name}[/{COLOR_PRIMARY}]")
                self.console.print(f"  Group-ID: [{COLOR_PRIMARY}]{group_id}[/{COLOR_PRIMARY}]\n")
                
                self.console.print(f"[{COLOR_WARNING}]Loading group members...[/{COLOR_WARNING}]")
                self.console.print(f"[{COLOR_DIM}]This may take some time for large groups...[/{COLOR_DIM}]\n")
                
                members = await self._get_all_group_members(group_id)
                
                if not members:
                    self.console.print(f"\n[{COLOR_WARNING}]Group '{group_name}' has no members.[/{COLOR_WARNING}]\n")
                else:
                    self._display_results(group_name, members)
                    
                    if Confirm.ask("\nExport as CSV?"):
                        self._export_csv(group_name, members)
                
                if not Confirm.ask("\nCheck another group?"):
                    break
            
            self.console.print(f"\n[{COLOR_PRIMARY}]Back to main menu...[/{COLOR_PRIMARY}]\n")
            
        except KeyboardInterrupt:
            self.console.print(f"\n\n[{COLOR_WARNING}]Cancelled by user[/{COLOR_WARNING}]\n")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Error: {str(e)}[/{COLOR_ERROR}]\n")
            pause(self.console)
    
    async def _select_group(self):
        """Groupnauswahl mit Suche"""
        self.console.print(f"[bold {COLOR_PRIMARY}]Group auswählen[/bold {COLOR_PRIMARY}]\n")
        
        search = Prompt.ask(f"[{COLOR_PRIMARY}]Suche nach Group (Enter für alle)[/{COLOR_PRIMARY}]", default="")
        
        filtered_groups = [g for g in self.all_groups if search.lower() in g.name.lower()]
        
        if not filtered_groups:
            self.console.print(f"[{COLOR_ERROR}]Keine Groupn gefunden![/{COLOR_ERROR}]\n")
            pause(self.console)
            return None
        
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("#", style=COLOR_DIM, width=6)
        table.add_column("Groupn-ID", width=12)
        table.add_column("Name", width=50)
        table.add_column("Members", justify="right", width=12)
        
        for idx, group in enumerate(filtered_groups, 1):
            table.add_row(
                str(idx),
                str(group.id),
                group.name,
                str(group.cntUsers if group.cntUsers else 0)
            )
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(f"[{COLOR_PRIMARY}]Wähle Group (Nummer) oder 's' für neue Suche[/{COLOR_PRIMARY}]", default="1")
        
        if choice.lower() == 's':
            return await self._select_group()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(filtered_groups):
                return filtered_groups[idx]
            else:
                self.console.print(f"[{COLOR_ERROR}]Invalid selection![/{COLOR_ERROR}]\n")
                pause(self.console)
                return None
        except ValueError:
            self.console.print(f"[{COLOR_ERROR}]Invalid input![/{COLOR_ERROR}]\n")
            pause(self.console)
            return None
    
    async def _get_all_group_members(self, group_id: int) -> list:
        """Holt alle Members einer Group (mit Pagination)"""
        all_members = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(f"[{COLOR_PRIMARY}]Lade Members...[/{COLOR_PRIMARY}]", total=None)
            
            group_filter = "isMember:eq:true"
            
            members_response = await self.dracoon.groups.get_group_users(
                group_id=group_id,
                filter=group_filter
            )
            
            all_members.extend(members_response.items)
            total = members_response.range.total
            
            if total > 500:
                progress.update(task, total=total, completed=len(all_members))
                
                for offset in range(500, total, 500):
                    members_response = await self.dracoon.groups.get_group_users(
                        group_id=group_id,
                        filter=group_filter,
                        offset=offset
                    )
                    all_members.extend(members_response.items)
                    progress.update(task, completed=len(all_members))
            else:
                progress.update(task, completed=True)
        
        self.console.print(f"[{COLOR_SUCCESS}]✓ {len(all_members)} Members geladen[/{COLOR_SUCCESS}]\n")
        
        return all_members
    
    def _display_results(self, group_name: str, members: list):
        """Zeigt die Members in einer Tabelle an"""
        self.console.print("\n" + "=" * 100)
        self.console.print(f"[bold {COLOR_PRIMARY}]Groupnmitglieder Report[/bold {COLOR_PRIMARY}]")
        self.console.print("=" * 100)
        self.console.print(f"Group:     {group_name}")
        self.console.print(f"Members: {len(members)}")
        self.console.print(f"Date:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.console.print(f"API-URL:    {self.dracoon.client.base_url}")
        self.console.print("=" * 100 + "\n")
        
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("User-ID", style=COLOR_DIM, width=10)
        table.add_column("Username", width=30)
        table.add_column("Name", width=30)
        table.add_column("Email", width=35)
        
        display_count = min(50, len(members))
        
        for member in members[:display_count]:
            if hasattr(member, 'userInfo') and member.userInfo:
                user_info = member.userInfo
                name = f"{getattr(user_info, 'firstName', '')} {getattr(user_info, 'lastName', '')}".strip()
                
                table.add_row(
                    str(user_info.id),
                    getattr(user_info, 'userName', ''),
                    name if name else '-',
                    getattr(user_info, 'email', '')
                )
        
        self.console.print(table)
        
        if len(members) > display_count:
            self.console.print(f"\n[{COLOR_WARNING}]⚠  Note: Only the first {display_count} of {len(members)} Membersn werden angezeigt.[/{COLOR_WARNING}]")
            self.console.print(f"[{COLOR_WARNING}]For the complete list please export CSV.[/{COLOR_WARNING}]")
        
        self.console.print()
    
    def _export_csv(self, group_name: str, members: list):
        """Exportiert die Members als CSV"""
        exports_dir = "exports"
        if not os.path.exists(exports_dir):
            os.makedirs(exports_dir)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        safe_groupname = "".join(c for c in group_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_groupname = safe_groupname.replace(' ', '_')
        filename = f"Group_{safe_groupname}_{timestamp}.csv"
        filepath = os.path.join(exports_dir, filename)
        
        header_rows = [
            ["Groupnmitglieder Report"],
            ["Group", group_name],
            ["Anzahl Members", str(len(members))],
            ["Datum", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["API-URL", self.dracoon.client.base_url],
            [],
            ["User-ID", "Username", "First Name", "Last Name", "Email"]
        ]
        
        member_rows = []
        for member in members:
            if hasattr(member, 'userInfo') and member.userInfo:
                user_info = member.userInfo
                member_rows.append([
                    str(user_info.id),
                    getattr(user_info, 'userName', ''),
                    getattr(user_info, 'firstName', ''),
                    getattr(user_info, 'lastName', ''),
                    getattr(user_info, 'email', '')
                ])
        
        try:
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(header_rows)
                writer.writerows(member_rows)
            
            self.console.print(f"\n[{COLOR_SUCCESS}]✓ CSV exported to:[/{COLOR_SUCCESS}] [{COLOR_PRIMARY}]{filepath}[/{COLOR_PRIMARY}]")
            self.console.print(f"[{COLOR_SUCCESS}]✓ {len(member_rows)} Members exportiert[/{COLOR_SUCCESS}]")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]✗ Error during CSV export: {str(e)}[/{COLOR_ERROR}]")


def main(dracoon: DRACOON):
    """Entry Point für das Modul"""
    report = GroupMembersReport(dracoon)
    return report.run()

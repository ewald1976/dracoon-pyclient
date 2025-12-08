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
        """Main function of the module"""
        try:
            self.console.clear()
            show_header(self.console, "Dracoon Pyclient - User-to-Group Manager")
            await self._load_data()
            pause(self.console)
            
            while True:
                if not await self._select_group():
                    continue
                
                users_to_add = await self._select_users()
                if not users_to_add:
                    continue
                
                await self._add_users(users_to_add)
                
                if not Confirm.ask("\nAdd more users?"):
                    break
            
            self.console.print(f"\n[{COLOR_PRIMARY}]Back to main menu...[/{COLOR_PRIMARY}]\n")
            
        except KeyboardInterrupt:
            self.console.print(f"\n\n[{COLOR_WARNING}]Cancelled by user[/{COLOR_WARNING}]\n")
        except Exception as e:
            self.console.print(f"\n[{COLOR_ERROR}]Error: {str(e)}[/{COLOR_ERROR}]\n")
            pause(self.console)
    
    async def _load_data(self):
        """Loads groups and users"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task1 = progress.add_task(f"[{COLOR_PRIMARY}]Loading groups...[/{COLOR_PRIMARY}]", total=None)
            groups_response = await self.dracoon.groups.get_groups()
            self.all_groups = groups_response.items
            progress.update(task1, completed=True)
            
            task2 = progress.add_task(f"[{COLOR_PRIMARY}]Loading users...[/{COLOR_PRIMARY}]", total=None)
            users_response = await self.dracoon.users.get_users()
            self.all_users = users_response.items
            progress.update(task2, completed=True)
        
        self.console.print(f"[{COLOR_SUCCESS}]✓ {len(self.all_groups)} groups loaded[/{COLOR_SUCCESS}]")
        self.console.print(f"[{COLOR_SUCCESS}]✓ {len(self.all_users)} users loaded[/{COLOR_SUCCESS}]\n")
    
    async def _select_group(self):
        """Group selection"""
        self.console.clear()
        show_header(self.console, "Dracoon Pyclient - User-to-Group Manager")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Select group[/bold {COLOR_PRIMARY}]\n")
        
        search = Prompt.ask(f"[{COLOR_PRIMARY}]Search for group (Enter for all)[/{COLOR_PRIMARY}]", default="")
        
        filtered_groups = [g for g in self.all_groups if search.lower() in g.name.lower()]
        
        if not filtered_groups:
            self.console.print(f"[{COLOR_ERROR}]No groups found![/{COLOR_ERROR}]\n")
            pause(self.console)
            return await self._select_group()
        
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("#", style=COLOR_DIM, width=6)
        table.add_column("Group-ID", width=12)
        table.add_column("Name", width=50)
        table.add_column("Members", justify="right", width=12)
        
        for idx, group in enumerate(filtered_groups, 1):
            cnt = getattr(group, 'cntUsers', 0)
            table.add_row(str(idx), str(group.id), group.name, str(cnt if cnt else 0))
        
        self.console.print(table)
        self.console.print()
        
        choice = Prompt.ask(f"[{COLOR_PRIMARY}]Select group (number)[/{COLOR_PRIMARY}]", default="1")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(filtered_groups):
                self.selected_group = filtered_groups[idx]
                
                self.console.print(f"\n[{COLOR_WARNING}]Loading group members...[/{COLOR_WARNING}]")
                members_response = await self.dracoon.groups.get_group_users(group_id=self.selected_group.id)
                self.group_members = members_response.items
                self.console.print(f"[{COLOR_SUCCESS}]✓ {len(self.group_members)} members in group[/{COLOR_SUCCESS}]\n")
                
                return True
            else:
                self.console.print(f"[{COLOR_ERROR}]Invalid selection![/{COLOR_ERROR}]\n")
                pause(self.console)
                return await self._select_group()
        except ValueError:
            self.console.print(f"[{COLOR_ERROR}]Invalid input![/{COLOR_ERROR}]\n")
            pause(self.console)
            return await self._select_group()
    
    async def _select_users(self):
        """User selection"""
        self.console.clear()
        show_header(self.console, "Dracoon Pyclient - User-to-Group Manager")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Select users for group '[{COLOR_PRIMARY}]{self.selected_group.name}[/{COLOR_PRIMARY}]'[/bold {COLOR_PRIMARY}]\n")
        
        member_ids = {
            getattr(m, 'userInfo', getattr(m, 'id', None)).id 
            for m in self.group_members 
            if getattr(m, 'userInfo', None) or getattr(m, 'id', None)
        }
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Options:[/bold {COLOR_PRIMARY}]")
        self.console.print(f"  [{COLOR_PRIMARY}]1[/{COLOR_PRIMARY}] - Add all users (skip already existing)")
        self.console.print(f"  [{COLOR_PRIMARY}]2[/{COLOR_PRIMARY}] - Select individual users")
        self.console.print(f"  [{COLOR_PRIMARY}]3[/{COLOR_PRIMARY}] - Choose different group\n")
        
        choice = Prompt.ask("Selection", default="1")
        
        if choice == "1":
            # All users not yet in the group
            users_to_add = [u for u in self.all_users if u.id not in member_ids]
        elif choice == "2":
            # Select individual users
            users_to_add = await self._select_individual_users(member_ids)
            if not users_to_add:
                return await self._select_users()
        elif choice == "3":
            return await self._select_group()
        else:
            self.console.print(f"[{COLOR_ERROR}]Invalid selection![/{COLOR_ERROR}]\n")
            pause(self.console)
            return await self._select_users()
        
        # Filter again (safety) - users already members will be skipped
        users_to_add = [u for u in users_to_add if u.id not in member_ids]
        
        if not users_to_add:
            self.console.print(f"\n[{COLOR_WARNING}]All selected users are already in the group![/{COLOR_WARNING}]\n")
            pause(self.console)
            return await self._select_users()
        
        return users_to_add
    
    async def _select_individual_users(self, member_ids: set) -> list:
        """Allows selection of individual users"""
        self.console.clear()
        show_header(self.console, "Dracoon Pyclient - User-to-Group Manager")
        
        self.console.print(f"[bold {COLOR_PRIMARY}]Select individual users for group '[{COLOR_PRIMARY}]{self.selected_group.name}[/{COLOR_PRIMARY}]'[/bold {COLOR_PRIMARY}]\n")
        
        # Filter users not yet in the group
        available_users = [u for u in self.all_users if u.id not in member_ids]
        
        if not available_users:
            self.console.print(f"[{COLOR_WARNING}]All users are already in the group![/{COLOR_WARNING}]")
            pause(self.console)
            return []
        
        self.console.print(f"[{COLOR_PRIMARY}]Search for users[/{COLOR_PRIMARY}]")
        search = Prompt.ask(f"[{COLOR_PRIMARY}]Name or email (Enter for list)[/{COLOR_PRIMARY}]", default="")
        
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
            self.console.print(f"[{COLOR_ERROR}]No matching users found![/{COLOR_ERROR}]")
            pause(self.console)
            return []
        
        # Show users in table
        table = Table(show_header=True, header_style=f"bold {COLOR_PRIMARY}", box=TABLE_BOX)
        table.add_column("#", style=COLOR_DIM, width=6)
        table.add_column("Name", width=30)
        table.add_column("Email", width=40)
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
            self.console.print(f"\n[{COLOR_WARNING}]Note: {len(filtered_users) - 20} additional users not shown.[/{COLOR_WARNING}]")
        
        self.console.print()
        self.console.print(f"[{COLOR_PRIMARY}]Select users:[/{COLOR_PRIMARY}]")
        self.console.print(f"  - Single number: e.g. '5'")
        self.console.print(f"  - Multiple numbers: e.g. '1,3,5'")
        self.console.print(f"  - Range: e.g. '1-5'")
        self.console.print(f"  - Combined: e.g. '1,3,5-8'")
        self.console.print(f"  - 's' for new search\n")
        
        choice = Prompt.ask("Selection")
        
        if choice.lower() == 's':
            return await self._select_individual_users(member_ids)
        
        try:
            selected_indices = set()
            parts = choice.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range
                    start, end = part.split('-')
                    selected_indices.update(range(int(start), int(end) + 1))
                else:
                    # Single number
                    selected_indices.add(int(part))
            
            selected_users = []
            for idx in selected_indices:
                if 1 <= idx <= len(display_users):
                    selected_users.append(display_users[idx - 1])
            
            if not selected_users:
                self.console.print(f"[{COLOR_ERROR}]No valid users selected![/{COLOR_ERROR}]")
                pause(self.console)
                return []
            
            # Confirmation
            self.console.print(f"\n[{COLOR_SUCCESS}]{len(selected_users)} users selected:[/{COLOR_SUCCESS}]")
            for user in selected_users:
                first_name = getattr(user, 'firstName', '')
                last_name = getattr(user, 'lastName', '')
                name = f"{first_name} {last_name}".strip()
                self.console.print(f"  - {name} ({getattr(user, 'email', '')})")
            
            self.console.print()
            if Confirm.ask("Add these users?"):
                return selected_users
            else:
                return await self._select_individual_users(member_ids)
            
        except (ValueError, IndexError):
            self.console.print(f"[{COLOR_ERROR}]Invalid input![/{COLOR_ERROR}]")
            pause(self.console)
            return await self._select_individual_users(member_ids)
    
    async def _add_users(self, users_to_add):
        """Adds users to the group"""
        self.console.print(f"\n[bold {COLOR_PRIMARY}]Summary:[/bold {COLOR_PRIMARY}]")
        self.console.print(f"  Group: [{COLOR_PRIMARY}]{self.selected_group.name}[/{COLOR_PRIMARY}]")
        self.console.print(f"  Users: [{COLOR_PRIMARY}]{len(users_to_add)}[/{COLOR_PRIMARY}]\n")
        
        if not Confirm.ask("Add users now?"):
            return
        
        success_count = 0
        failed_count = 0
        failed_users = []  # List of failed users
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                f"[{COLOR_PRIMARY}]Adding {len(users_to_add)} users individually...[/{COLOR_PRIMARY}]",
                total=len(users_to_add)
            )
            
            # Add each user individually
            for user in users_to_add:
                # Suppress SDK log outputs
                import sys
                import io
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                try:
                    await self.dracoon.groups.add_group_users(
                        group_id=self.selected_group.id,
                        user_list=[user.id],
                        raise_on_err=True  # So we catch real API errors
                    )
                    # If we get here, it was successful
                    success_count += 1
                        
                except Exception as e:
                    error_msg = str(e)
                    # Ignore only Pydantic errors (user was still added)
                    if "validation error" in error_msg.lower():
                        success_count += 1
                    else:
                        # Real error
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
        
        # Output result
        self.console.print(f"\n[{COLOR_SUCCESS}]✓ {success_count} of {len(users_to_add)} users successfully added![/{COLOR_SUCCESS}]")
        
        if failed_count > 0:
            self.console.print(f"[{COLOR_ERROR}]✗ {failed_count} users could not be added:[/{COLOR_ERROR}]\n")
            
            # Show failed users in table
            from rich.table import Table
            table = Table(show_header=True, header_style=f"bold {COLOR_ERROR}", box=TABLE_BOX)
            table.add_column("Name", width=30)
            table.add_column("Email", width=35)
            table.add_column("User-ID", style=COLOR_DIM, width=10)
            
            for failed_user in failed_users:
                table.add_row(
                    failed_user['name'],
                    failed_user['email'],
                    str(failed_user['id'])
                )
            
            self.console.print(table)
            self.console.print(f"\n[{COLOR_DIM}]Note: These users may be guest users or have special permissions.[/{COLOR_DIM}]")
        
        self.console.print()
        pause(self.console)


def main(dracoon: DRACOON):
    """Entry Point für das Modul"""
    manager = UserToGroupManager(dracoon)
    return manager.run()
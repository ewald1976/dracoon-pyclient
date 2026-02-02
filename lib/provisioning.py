"""
Dracoon Pyclient - Provisioning API Client
Zugriff auf Multi-Tenant/Reseller Provisioning API
"""

import httpx
from typing import List, Dict, Optional
from rich.console import Console


class ProvisioningClient:
    """Client für die Dracoon Provisioning API (Multi-Tenant)"""
    
    def __init__(self, base_url: str, service_token: str, debug: bool = False):
        """
        Initialisiert den Provisioning Client
        
        Args:
            base_url: Basis-URL der Dracoon Instanz
            service_token: X-SDS-Service-Token für Provisioning
            debug: Debug-Modus für detaillierte Ausgaben
        """
        self.base_url = base_url.rstrip('/')
        self.service_token = service_token
        self.debug = debug
        self.headers = {
            'X-SDS-Service-Token': service_token,
            'Content-Type': 'application/json'
        }
    
    def _debug_print(self, message: str):
        """Debug-Ausgabe wenn Debug-Modus aktiv"""
        if self.debug:
            console = Console()
            console.print(f"[dim][DEBUG] {message}[/dim]")
    
    async def get_customers(self, offset: int = 0, limit: int = 500, 
                           filter_str: Optional[str] = None) -> Dict:
        """
        Holt alle Kunden vom Tenant
        
        Args:
            offset: Startposition für Pagination
            limit: Anzahl der Ergebnisse (max 500)
            filter_str: Optional - Filter String (z.B. "companyName:cn:Test")
        
        Returns:
            Dictionary mit Kunden-Liste und Range-Informationen
        """
        url = f"{self.base_url}/api/v4/provisioning/customers"
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if filter_str:
            params['filter'] = filter_str
        
        self._debug_print(f"GET {url} (offset={offset}, limit={limit})")
        
        # Längeres Timeout (2 Minuten) für große Instanzen
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                self._debug_print(f"Response: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                self._debug_print(f"Received {len(data.get('items', []))} customers")
                return data
            except httpx.TimeoutException:
                raise Exception(f"Request timeout after 120 seconds. The server might be overloaded or the API is slow.")
            except httpx.HTTPStatusError as e:
                raise Exception(f"HTTP Error {e.response.status_code}: {e.response.text}")
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")
    
    async def get_all_customers(self, filter_str: Optional[str] = None) -> List[Dict]:
        """
        Holt ALLE Kunden (mit automatischer Pagination)
        
        Args:
            filter_str: Optional - Filter String
        
        Returns:
            Liste aller Kunden
        """
        all_customers = []
        offset = 0
        limit = 500
        
        while True:
            self._debug_print(f"Fetching customers page (offset={offset})")
            result = await self.get_customers(offset=offset, limit=limit, filter_str=filter_str)
            
            customers = result.get('items', [])
            all_customers.extend(customers)
            
            # Prüfen ob es weitere Ergebnisse gibt
            total = result.get('range', {}).get('total', 0)
            self._debug_print(f"Total customers: {total}, fetched so far: {len(all_customers)}")
            
            if offset + limit >= total:
                break
            
            offset += limit
        
        return all_customers
    
    async def get_customer(self, customer_id: int) -> Dict:
        """
        Holt Details eines einzelnen Kunden
        
        Args:
            customer_id: ID des Kunden
        
        Returns:
            Kunden-Informationen
        """
        url = f"{self.base_url}/api/v4/provisioning/customers/{customer_id}"
        
        self._debug_print(f"GET {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_customer_users(self, customer_id: int, offset: int = 0, 
                                limit: int = 500, filter_str: Optional[str] = None) -> Dict:
        """
        Holt alle User eines Kunden
        
        Args:
            customer_id: ID des Kunden
            offset: Startposition für Pagination
            limit: Anzahl der Ergebnisse (max 500)
            filter_str: Optional - Filter String
        
        Returns:
            Dictionary mit User-Liste und Range-Informationen
        """
        url = f"{self.base_url}/api/v4/provisioning/customers/{customer_id}/users"
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if filter_str:
            params['filter'] = filter_str
        
        self._debug_print(f"GET {url} (offset={offset}, limit={limit})")
        
        # Längeres Timeout für User-Abfragen
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                self._debug_print(f"Response: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                self._debug_print(f"Received {len(data.get('items', []))} users")
                return data
            except httpx.TimeoutException:
                raise Exception(f"User request timeout for customer {customer_id}")
            except Exception as e:
                raise Exception(f"Failed to get users for customer {customer_id}: {str(e)}")
    
    async def get_all_customer_users(self, customer_id: int, 
                                    filter_str: Optional[str] = None) -> List[Dict]:
        """
        Holt ALLE User eines Kunden (mit automatischer Pagination)
        
        Args:
            customer_id: ID des Kunden
            filter_str: Optional - Filter String
        
        Returns:
            Liste aller User des Kunden
        """
        all_users = []
        offset = 0
        limit = 500
        
        while True:
            result = await self.get_customer_users(
                customer_id=customer_id, 
                offset=offset, 
                limit=limit, 
                filter_str=filter_str
            )
            
            users = result.get('items', [])
            all_users.extend(users)
            
            # Prüfen ob es weitere Ergebnisse gibt
            total = result.get('range', {}).get('total', 0)
            if offset + limit >= total:
                break
            
            offset += limit
        
        return all_users
    
    async def test_connection(self) -> bool:
        """
        Testet die Verbindung zur Provisioning API
        
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            self._debug_print("Testing connection...")
            await self.get_customers(limit=1)
            self._debug_print("Connection test successful")
            return True
        except Exception as e:
            self._debug_print(f"Connection test failed: {str(e)}")
            return False

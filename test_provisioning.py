#!/usr/bin/env python3
"""
Test script for Provisioning API Client
"""

import asyncio
from lib.provisioning import ProvisioningClient


async def test_provisioning():
    """Test the Provisioning API connection"""
    
    # Test credentials (replace with real ones)
    base_url = "https://demo.dracoon.com"
    service_token = "your_service_token_here"
    
    print("Initializing Provisioning Client...")
    client = ProvisioningClient(base_url, service_token)
    
    print("Testing connection...")
    if await client.test_connection():
        print("✓ Connection successful!")
        
        print("\nFetching customers...")
        customers = await client.get_all_customers()
        print(f"✓ Found {len(customers)} customers")
        
        if customers:
            print("\nFirst customer:")
            first = customers[0]
            print(f"  ID: {first.get('id')}")
            print(f"  Name: {first.get('companyName')}")
            
            print(f"\nFetching users for customer {first.get('id')}...")
            users = await client.get_all_customer_users(first.get('id'))
            print(f"✓ Found {len(users)} users")
            
            if users:
                print("\nFirst user:")
                user = users[0]
                print(f"  ID: {user.get('id')}")
                print(f"  Name: {user.get('firstName')} {user.get('lastName')}")
                print(f"  Email: {user.get('email')}")
    else:
        print("✗ Connection failed!")


if __name__ == "__main__":
    asyncio.run(test_provisioning())

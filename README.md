# Dracoon Pyclient

Python tool for the Dracoon API with console interface.

## Modules

- **Add Users to Group** - Bulk operation to add users to groups
- **Room Admin Report** - Shows where a user is the last room admin. Room can then be deleted directly.
- **List Group Members** - Lists all members of a group and optionally exports as CSV
- **Customer Email Export (Reseller)** - Export all email addresses from all customers in a multi-tenant environment

## Installation

```bash
git clone https://github.com/ewald1976/dracoon-pyclient.git
cd dracoon-pyclient

# Virtual Environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Dependencies
pip3 install -r requirements.txt
```

## Configuration

### Standard Modules (OAuth)

For modules 1-3, create an OAuth App in Dracoon:

1. Settings → Security → OAuth Apps → "Create New App"
2. Grant Type: `password`
3. Redirect URI: `http://localhost`
4. Note down Client-ID and Client-Secret

### Reseller Module (Provisioning API)

For the "Customer Email Export" module, you need a **X-SDS-Service-Token**:

1. Log in as Reseller/Tenant Administrator
2. Settings → Provisioning
3. Generate Service Token
4. Note down the token

### .env File

```bash
cp .env.example .env
nano .env  # Enter credentials
```

**Required entries for standard modules:**
```
DRACOON_BASE_URL=https://your-instance.dracoon.com
DRACOON_CLIENT_ID=your_client_id
DRACOON_CLIENT_SECRET=your_client_secret
DRACOON_USERNAME=your_username
DRACOON_PASSWORD=your_password
```

**Additional entry for Reseller module:**
```
DRACOON_SERVICE_TOKEN=your_service_token
```

**Required Permissions:**
- Modules 1-3: Admin permissions required
- Module 4: Reseller/Tenant Administrator with Provisioning access

## Usage

```bash
python3 dracoon-pyclient.py
```

### Windows

An executable version is available for Windows. If a .env file is used for configuration, it must be in the same directory as the EXE file.

## Multi-Tenant / Reseller Features

The **Customer Email Export** module is specifically designed for Reseller/Multi-Tenant environments:

- Uses the Provisioning API with Service Token authentication
- Iterates over all customers in the tenant
- Collects email addresses from all users across all customers
- Exports results to CSV
- No OAuth credentials needed for this module

This is particularly useful for:
- Mass communications to all users
- User audits across multiple customers
- Compliance reporting
- Data migration planning

## Common Errors

**401 Unauthorized** - Check credentials in `.env`, OAuth Grant Type must be `password`

**403 Forbidden** - User does not have the required permissions

**ModuleNotFoundError** - Run `pip3 install -r requirements.txt`

**Provisioning API Error** - Verify Service Token is valid and user has Provisioning access

## Disclaimer 

This tool was developed privately and has **no official connection to Dracoon GmbH**. Use at your own risk. The developer assumes no liability for any damage caused by the use of this tool.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

### Used Libraries

This project uses the official [DRACOON Python SDK](https://github.com/unbekanntes-pferd/dracoon-python-api), which is licensed under the Apache License 2.0.

#### DRACOON Python SDK
- **Repository:** https://github.com/unbekanntes-pferd/dracoon-python-api
- **License:** Apache License 2.0
- **Copyright:** © DRACOON Contributors

Other libraries used:
- **Rich** - MIT License
- **python-dotenv** - BSD-3-Clause License
- **httpx** - BSD-3-Clause License

A complete list of all dependencies can be found in `requirements.txt`.

## Author

[@ewald1976](https://github.com/ewald1976)

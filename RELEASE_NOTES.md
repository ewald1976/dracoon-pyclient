# Dracoon Pyclient v0.2.0 - English Release

## 🎉 What's New

Version 0.2.0 marks the complete translation of Dracoon Pyclient to English, making it accessible to international users while maintaining all the powerful features from previous versions.

## 📋 Summary of Changes

### User Interface Translation
All user-facing text has been professionally translated from German to English:

✅ **Main Application** (`dracoon-pyclient.py`)
- Welcome screen and main menu
- Connection messages
- Module descriptions
- God-Mode warnings

✅ **User-to-Group Manager** (`modules/user_to_group.py`)
- Group selection interface
- User selection (individual and bulk)
- Progress indicators
- Success/error messages

✅ **Room Admin Report** (`modules/room_admin_report.py`)
- User search and selection
- Room listing and analysis
- Deletion confirmations (with safety prompts)
- CSV export messages

✅ **List Group Members** (`modules/group_members_report.py`)
- Group search and selection
- Member listing and pagination
- CSV export functionality

✅ **Utility Functions** (`lib/utils.py`)
- Credential prompts
- User search interface
- Pause/continue messages

✅ **Documentation** (`README.md`)
- Complete rewrite in English
- Added God-Mode documentation
- Updated installation and usage instructions

## 🔄 Version Changes

- Version updated from `0.1.2` to `0.2.0`
- All functionality preserved from previous version
- No breaking changes
- Full backward compatibility with existing `.env` configurations

## 📦 What's Included

```
dracoon-pyclient-0.2.0-english/
├── dracoon-pyclient.py          # Main application
├── lib/
│   ├── __init__.py
│   └── utils.py                 # Utility functions
├── modules/
│   ├── user_to_group.py         # User-to-Group Manager
│   ├── room_admin_report.py     # Room Admin Report
│   └── group_members_report.py  # Group Members List
├── requirements.txt             # Python dependencies
├── README.md                    # English documentation
├── CHANGELOG.md                 # Version history
└── LICENSE                      # MIT License
```

## 🚀 Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the tool
python3 dracoon-pyclient.py

# Or with God-Mode (⚠️ use with caution!)
python3 dracoon-pyclient.py --god-mode
```

## ⚙️ Configuration

Create a `.env` file with your Dracoon credentials:

```env
DRACOON_BASE_URL=https://your-instance.dracoon.com
DRACOON_CLIENT_ID=your_client_id
DRACOON_CLIENT_SECRET=your_client_secret
DRACOON_USERNAME=your_username
DRACOON_PASSWORD=your_password
```

## 🔐 Required Permissions

- **Group Admin** - For User-to-Group operations
- **User Manager** - For Room Admin Report

## 📝 Notes

- All core functionality remains unchanged
- Existing configurations and scripts continue to work
- God-Mode feature preserved with updated warnings in English
- CSV exports maintain same format and structure

## 🎯 Next Steps

This version is ready for:
- GitHub release as v0.2.0
- Tag creation in repository
- Windows executable build (planned for future release)

## 👤 Maintained By

[@ewald1976](https://github.com/ewald1976)

---

**Important:** This is an unofficial tool with no affiliation to Dracoon GmbH. Use at your own risk.

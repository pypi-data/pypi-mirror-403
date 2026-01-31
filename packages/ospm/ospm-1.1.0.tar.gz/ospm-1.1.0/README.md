## Open source python password manager

### Installation

1. You need to have [python](https://python.org) 3.10+ installed
2. Run this command in your terminal: Linux, MacOS, etc: `pip3 install ospm` Windows: `pip install ospm`

### Usage
To start using the password manager, after installing it, run `ospm init` in your terminal. Or run `python -m ospm init` if the previous command doesn't work

### Commands

- `ospm init -v [VAULT]` - Initialises a new vault, you will be prompted to write your new master password (You can provide a name for your vault)
- `ospm add [NAME] [ACCOUNT] -p [PASSWORD] -n [NOTE]` - Adds a new entry to your vault, password is an optional argument and if not provided: ospm will generate one for you and copy to your clipboard
- `ospm delete -i [PASSWORD_ID]` - Opens a menu to choose which password you want to delete if you did not provide the password's id
- `ospm list` - Shows the list of all passwords
- `ospm modify -i [PASSWORD_ID]` - Opens a menu to choose which entry to modify if you did not provide the password's id
- `ospm gen [AMOUNT] -l [LENGTH]` - Generates a provided number of alphanumeric passwords with a set length (default length is configured in config), if the amount is 1 (or not provided) the password will be copied to clipboard
- `ospm changepass -v [VAULT]` - Changes the master password of a vault (By default it's the current vault) 
- `ospm config` - Opens menu to choose which parameter of config to modify (for now only one)
- `ospm info` - Shows locations of the config and vault files
- `ospm switch [VAULT]` - Switches to another vault (Will create one if it doesn't exist)

*In all lists you can navigate with Up and Down arrows and your mouse, to select an item press Enter. To quit a TUI (menu) press Ctrl+Q*
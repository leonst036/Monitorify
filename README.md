# Monitorify
### A terminal montioring tool for linux

- Features
- CPU monitoring 
- RAM monitoring
- Network monitoring
- Disk monitoring (I/O and storage capacity)
- Process monitoring
- Background daemon
- Customization menu (toggle widgets, set intervals, and change history window)
- Historical graphs
## Installation
### Using pipx
```bash
pipx install git+https://github.com/leonst036/Monitorify.git
```

### Using pip
```bash
pip install git+https://github.com/leonst036/Monitorify.git
```

### Using source
```bash
git clone https://github.com/leonst036/Monitorify.git
cd Monitorify
pip install . 
```

## Usage
```bash
monitorify
```

## Tech Stack

* **Language & TUI:** Python, Textual
* **Database:** SQLite
* **Target OS:** Linux

## Remote

To use Monitorify remotely over SSH on your server, you can set the following parameters:

- `--ip` – Set the target IP address.
- `--port` – Set the SSH port.
- `--username` – Set the username for the remote host.
- `--password` – Set the password for the SSH server.
- `--key_filename` – Set the path to an SSH key *(optional)*.
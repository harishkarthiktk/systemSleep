# systemSleep

A cross-platform system sleep utility supporting Windows, macOS, and Linux with both CLI and GUI interfaces.

## Features

- **CLI Scripts**: Command-line tools for scheduling system sleep with configurable delays
- **GUI Applications**: Visual interfaces with countdown timers and progress bars
- **Sleep Prevention**: Prevent system from sleeping while performing important tasks
- **Multi-Cycle Support**: Automatically resume sleep cycles after system wakes
- **Configuration Management**: Centralized config file with CLI overrides
- **Comprehensive Logging**: Track all sleep operations with timestamps

## Platform Support

| Platform | Status | Interface | Notes |
|----------|--------|-----------|-------|
| **Windows 10/11** | ✅ Supported | CLI + GUI | Uses `Rundll32.exe Powrprof.dll,SetSuspendState` |
| **macOS** | ✅ Supported | CLI | Uses `caffeinate` for sleep prevention |
| **Linux (systemd)** | ✅ Supported | CLI + GUI | Fedora, Ubuntu, Debian, Arch, openSUSE, RHEL |

## Requirements

- **Python 3.10+**
- **Windows**: Admin privileges recommended, hibernation enabled
- **Linux**: Systemd-based distribution
- **All platforms**: Built-in Python modules only (no external dependencies except optional `requests` for macOS)

## Installation

```bash
# Clone or download the repository
cd systemSleep

# No additional dependencies required for Windows/Linux
# For macOS with exchange rate monitoring:
pip install requests
```

## Usage

### Windows

#### CLI Script
```bash
# Interactive mode
python systemSleep.py

# With command-line arguments
python systemSleep.py --delay 10 --wake-delay 3 --timeout 20 --log-file sleep.log

# Silent immediate sleep (rename to .pyw and double-click)
python systemSleep.pyw

# Show help
python systemSleep.py --help
```

#### GUI Application
```bash
# Modern GUI with settings
python sleep_gui_new.pyw

# Legacy GUI
python sleep_gui.pyw
```

**Windows Setup**:
```powershell
# Enable hibernation (required for full functionality)
powercfg -h on
```

### macOS

#### Exchange Rate Monitor with Sleep Prevention
```bash
# Monitor USD→INR exchange rates while preventing system sleep
python macDontSleep.py

# With custom settings
python macDontSleep.py --api-url "https://your-api.com" --interval 120

# Show help
python macDontSleep.py --help
```

### Linux

#### CLI Script
```bash
# Interactive sleep mode
python linuxSleep.py

# Sleep with arguments
python linuxSleep.py --mode sleep --sleep-type suspend --delay 10

# Prevent system sleep
python linuxSleep.py --mode prevent --prevent-reason "Long download"

# Show help
python linuxSleep.py --help
```

#### GUI Application
```bash
# Modern GUI with mode selector and settings
python linuxSleep_gui.pyw
```

**Linux Setup** (Optional - for non-root sleep without password):

Create `/etc/polkit-1/rules.d/85-suspend.rules`:
```bash
sudo nano /etc/polkit-1/rules.d/85-suspend.rules
```

Add the following content:
```javascript
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.login1.suspend" ||
        action.id == "org.freedesktop.login1.hibernate" ||
        action.id == "org.freedesktop.login1.hybrid-sleep") {
        if (subject.isInGroup("wheel")) {
            return polkit.Result.YES;
        }
    }
});
```

Then restart polkit:
```bash
sudo systemctl restart polkit
```

## Configuration

All scripts load settings from `config.json` with the following priority:
1. Command-line arguments (CLI scripts only)
2. Values from `config.json`
3. Hardcoded defaults

### Example Configuration
```json
{
  "linuxSleep": {
    "log_file": "linux_sleep.log",
    "sleep_command_timeout": 15,
    "wake_delay_minutes": 5,
    "default_delay_minutes": 0,
    "default_sleep_type": "suspend"
  },
  "linuxSleep_gui": {
    "enable_cycling": true,
    "default_sleep_type": "suspend"
  }
}
```

## Architecture

### Core Files

- **systemSleep.py** - Windows CLI sleep scheduler
- **sleep_gui.pyw** - Windows legacy GUI
- **sleep_gui_new.pyw** - Windows modern GUI
- **macDontSleep.py** - macOS exchange rate monitor with sleep prevention
- **linuxSleep.py** - Linux CLI sleep/prevention scheduler
- **linuxSleep_gui.pyw** - Linux modern GUI
- **linux_sleep_helpers.py** - Shared Linux utilities
- **config_loader.py** - Configuration management
- **config.json** - Configuration file

## Platform-Specific Details

### Windows
- **Sleep Command**: `Rundll32.exe Powrprof.dll,SetSuspendState Sleep`
- **Hibernation**: Must be enabled with `powercfg -h on`
- **Logging**: File-based logging to `sleep.log`
- **Multi-Cycle**: 5-minute wait after wake-up before next sleep

### macOS
- **Sleep Prevention**: Uses `caffeinate -i` subprocess
- **Exchange Rate API**: Fetches USD→INR rates from `https://open.er-api.com/v6/latest/USD`
- **Dependencies**: Requires `requests` module
- **Signal Handling**: Graceful Ctrl+C shutdown

### Linux
- **Sleep Types**: Suspend (RAM), Hibernate (disk), Hybrid-sleep (both)
- **Sleep Command**: `systemctl suspend|hibernate|hybrid-sleep`
- **Sleep Prevention**: `systemd-inhibit --what=sleep`
- **Permission Check**: Uses `systemctl --dry-run` to verify permissions
- **Logging**: File-based logging to `linux_sleep.log`
- **Supported Distributions**: Fedora, RHEL, Ubuntu, Debian, Arch, openSUSE (any systemd-based)

## Logging

Check operation logs for debugging and monitoring:

```bash
# Windows
cat sleep.log
tail -f sleep.log

# Linux
cat linux_sleep.log
tail -f linux_sleep.log
```

## Troubleshooting

### Windows
- **"Admin rights required"**: Run Command Prompt or PowerShell as Administrator
- **"Hibernation not enabled"**: Execute `powercfg -h on` in PowerShell
- **Sleep command times out**: Check if system is unresponsive

### Linux
- **"Systemd not detected"**: Ensure you're running a systemd-based distribution
- **Permission denied**: Run with sudo or configure polkit rules (see setup above)
- **"systemd-inhibit not found"**: Install systemd package (`sudo dnf install systemd` on Fedora)

### macOS
- **"requests module not found"**: Install with `pip install requests`
- **Exchange rate fetch fails**: Check internet connection, API may be temporarily unavailable

## Development Notes

All scripts follow consistent patterns:
- **Platform Detection**: Scripts check their target platform and exit gracefully on others
- **Error Handling**: Subprocess timeouts, permission errors, and network failures handled appropriately
- **Logging**: All operations logged with timestamps for debugging
- **Configuration**: Three-tier priority system (CLI args > config > defaults)
- **Threading**: GUI applications use daemon threads for non-blocking operations

For detailed architecture notes, see [CLAUDE.md](CLAUDE.md).

## License

See LICENSE file for details.

## Contributing

Improvements and cross-platform enhancements welcome!

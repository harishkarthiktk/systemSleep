# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

systemSleep is a cross-platform system sleep utility with multiple interfaces:
- **CLI scripts** for Windows, macOS, and Linux sleep management
- **GUI applications** (tkinter-based) for Windows and Linux with visual timer and controls
- **Sleep prevention tool** for macOS that prevents system sleep while monitoring exchange rates

The project supports Windows 10+, macOS, and Linux (systemd-based). Python 3.10+ is required.

## Architecture

### Core Components

1. **windows_sleep.py** - Windows CLI sleep script
   - Uses `Rundll32.exe Powrprof.dll,SetSuspendState` for sleep commands
   - Supports both immediate sleep and delayed countdown
   - Implements multi-cycle sleep behavior (5-minute gap between cycles after wake)
   - Logs all operations to `sleep.log`
   - Can run as `.pyw` for silent/immediate execution

2. **windows_sleep_gui.pyw** - Windows GUI application
   - Tkinter-based interface with countdown display
   - Takes user input for delay time before sleep
   - Implements threading for non-blocking countdown
   - Multi-cycle loop: after system wakes, resets to 5-minute wait
   - Tooltip helper class for UI hints
   - Has deprecated `delayed_sleep()` function (marked for deletion)

3. **macos_prevent_sleep.py** - macOS sleep prevention with exchange rate monitor
   - Uses `caffeinate -i` to prevent system sleep
   - Fetches USD→INR exchange rates every 5 minutes from `https://open.er-api.com/v6/latest/USD`
   - Comprehensive error handling for network failures, timeouts, and JSON parsing
   - Signal handler for graceful Ctrl+C shutdown

4. **config_loader.py** - Shared configuration module
   - Simple function-based loader (no classes, per project style)
   - `load_config()` - Loads JSON with graceful error handling
   - `get_script_config(script_name)` - Gets config section for specific script
   - `get_setting(script_name, key, default)` - Gets single setting with fallback
   - Silent failure: Returns empty dict if config missing/invalid, scripts use defaults

5. **linux_sleep.py** - Linux CLI sleep/prevention script
   - Uses `systemctl suspend/hibernate/hybrid-sleep` for sleep commands
   - Two modes: sleep (scheduler) and prevent (systemd-inhibit)
   - Supports three sleep types: suspend, hibernate, hybrid-sleep
   - Permission checking via `systemctl --dry-run`
   - Multi-cycle sleep behavior (5-minute gap between cycles after wake)
   - Logs all operations to `linux_sleep.log`
   - Signal handler for graceful Ctrl+C shutdown in prevent mode

6. **linux_sleep_gui.pyw** - Linux GUI application
   - Tkinter-based interface with mode selector (sleep/prevent radio buttons)
   - Dynamic UI: shows different controls based on selected mode
     - Sleep mode: sleep type dropdown, delay input (spinbox 0-1440 minutes)
     - Prevent mode: reason text entry for sleep prevention
   - Countdown display with color-coded progress bar (black → orange → green/purple)
   - Status label with color-coded messages for user feedback
   - Settings modal with:
     - Sleep cycling options (enable/disable, wake delay adjustment 1-60 minutes)
     - Default sleep type selector (suspend/hibernate/hybrid-sleep)
     - Permission checker button for current sleep type
     - About section with application info and features
   - Thread-based non-blocking operations for smooth UI
   - Graceful cleanup of sleep prevention process on cancel/exit
   - Cross-platform compatible fonts (TkDefaultFont for Linux/Windows/macOS)
   - Follows windows_sleep_gui.pyw pattern with Linux-specific enhancements

7. **linux_sleep_helpers.py** - Shared Linux utilities
   - Function-based module (no classes, like config_loader.py)
   - `check_linux_environment()` - Verify Linux + systemd
   - `check_sleep_permissions()` - Dry-run permission check
   - `get_sleep_command()` - Build systemctl command
   - `execute_sleep()` - Execute with error handling

8. **config.json** - Configuration file (now actively used)
   - Script-specific sections: `windows_sleep`, `macos_prevent_sleep`, `windows_sleep_gui`, `linux_sleep`, `linux_sleep_gui`
   - Essential settings only (minimal, not comprehensive):
     - `sleep_command_timeout`: Subprocess timeout (15s default)
     - `wake_delay_minutes`: Delay after wake-up before next cycle (5 min default)
     - `default_delay_minutes`: Initial input field value
     - `default_sleep_type`: Default sleep type for Linux (suspend/hibernate/hybrid-sleep)
     - `api_url`: API endpoint for exchange rates
     - `api_timeout`: API request timeout (10s default)
     - `fetch_interval_seconds`: Exchange rate fetch frequency (300s default)
     - `enable_cycling`: Enable multi-cycle mode (windows_sleep_gui, linux_sleep_gui only)

## Platform-Specific Details

### Windows
- Sleep command: `Rundll32.exe Powrprof.dll,SetSuspendState Sleep`
- Requires admin privileges
- Hibernate must be enabled: `powercfg -h on` (PowerShell)
- Tested on Windows 10 and 11; likely works on 8/8.1; mixed results on Windows 7

### macOS
- Uses native `caffeinate` command (available on all modern macOS)
- Requires `requests` module for HTTP calls
- Exchange rate API is third-party; monitor gracefully handles API failures

### Linux/Fedora
- Sleep commands: `systemctl suspend|hibernate|hybrid-sleep`
- Sleep prevention: `systemd-inhibit --what=sleep --who=AppName --why=Reason <command>`
- Requires systemd (checks `/run/systemd/system`)
- Permission checking via `systemctl --dry-run` before actual sleep
- Tested on Fedora, Ubuntu, Debian, Arch, openSUSE, RHEL (all systemd-based distributions)
- Polkit configuration recommended for non-root sleep without password prompt

## Key Design Patterns

- **Configuration Management**: Centralized config loading via `config_loader.py` module
  - All scripts load config from `config.json` on startup
  - CLI scripts (windows_sleep.py, macos_prevent_sleep.py) accept command-line args to override config
  - Priority: CLI args > config.json > hardcoded defaults

- **Logging**: Windows CLI uses file-based logging to configurable path with timestamps

- **Threading**: GUI uses daemon threads to prevent blocking UI during countdown

- **Error handling**:
  - Subprocess: Catches both `TimeoutExpired` and `CalledProcessError`
  - Network: Specific exception handling for timeouts, connection errors, HTTP errors, JSON parsing
  - Config: Silent failure with sensible defaults if config missing/invalid

- **Signal handling**: macOS script uses signal handlers for graceful Ctrl+C shutdown

- **Input validation**: Both CLI and GUI validate integer inputs; argparse provides type checking for CLI

- **Timeout protection**: All subprocess sleep commands have 15-second timeout to prevent indefinite hangs

- **GUI recovery**: GUI controls automatically re-enable when sleep_loop exits (error or completion)

## Common Development Tasks

### Running the scripts

```bash
# Windows CLI - interactive mode with config defaults
python windows_sleep.py

# Windows CLI - with CLI arguments (override config)
python windows_sleep.py --delay 10 --wake-delay 3 --timeout 20 --log-file custom.log

# Windows CLI - silent immediate sleep (rename .py to .pyw and double-click)
python windows_sleep.pyw

# Windows GUI (legacy)
python sleep_gui.pyw

# Windows GUI (modern with settings)
python windows_sleep_gui.pyw

# macOS exchange rate monitor with config defaults
python macos_prevent_sleep.py

# macOS - with CLI arguments (override config)
python macos_prevent_sleep.py --api-url "https://api.example.com" --interval 120

# Linux CLI - sleep mode (interactive)
python linux_sleep.py

# Linux CLI - sleep mode with arguments
python linux_sleep.py --mode sleep --sleep-type suspend --delay 10

# Linux CLI - prevent mode
python linux_sleep.py --mode prevent --prevent-reason "Long download"

# Linux GUI
python linux_sleep_gui.pyw
```

### CLI Usage

All CLI scripts support `--help`:
```bash
python windows_sleep.py --help
python macos_prevent_sleep.py --help
python linux_sleep.py --help
```

### Checking logs
```bash
# View Windows sleep log
cat sleep.log
tail -f sleep.log  # follow new entries

# View Linux sleep log
cat linux_sleep.log
tail -f linux_sleep.log  # follow new entries
```

### Testing sleep commands manually
```bash
# Windows - test sleep without full script
python -m subprocess.run(['Rundll32.exe', 'Powrprof.dll,SetSuspendState', 'Sleep'])

# macOS - test caffeinate
caffeinate -i &  # start in background
kill %1  # stop

# Linux - test sleep commands
systemctl suspend --dry-run  # check permission without sleeping
systemctl suspend  # put system to sleep
systemctl hibernate  # hibernate
systemctl hybrid-sleep  # hybrid sleep

# Linux - test sleep prevention
systemd-inhibit --what=sleep --who=TestApp --why="Testing" sleep 30
```

## Dependencies

The `.gitignore` ignores all `.txt` files, so requirements must be installed directly or inferred:
- Windows scripts: Built-in modules only (`subprocess`, `logging`, `time`, `threading`, `tkinter`, `argparse`, `json`)
- macOS script: Requires `requests` module (error message guides user to install)
- Linux scripts: Built-in modules only (`subprocess`, `logging`, `time`, `signal`, `threading`, `tkinter`, `argparse`, `platform`, `os`, `sys`)
- All scripts: `config_loader.py` module available locally

## Configuration

All scripts use `config_loader.py` to load settings from `config.json`. Priority order:
1. CLI arguments (windows_sleep.py, macos_prevent_sleep.py only)
2. Values from `config.json` script-specific section
3. Hardcoded defaults in source code

Scripts work without config.json present - all settings have sensible defaults.

**CLI argument examples:**
- `windows_sleep.py`: `--delay`, `--wake-delay`, `--timeout`, `--log-file`, `--config`
- `macos_prevent_sleep.py`: `--api-url`, `--api-timeout`, `--interval`, `--config`
- `linux_sleep.py`: `--mode`, `--sleep-type`, `--delay`, `--wake-delay`, `--timeout`, `--log-file`, `--prevent-reason`, `--config`

## Bug Fixes & Improvements (Recent)

### Critical Fixes (Now Implemented)
1. **Subprocess Timeout Protection** - All sleep commands have 15-second timeout
   - Prevents indefinite hangs if Rundll32.exe becomes unresponsive
   - Catches `TimeoutExpired` exception with appropriate error message

2. **GUI Error Recovery** - Controls re-enable after errors
   - sleep_gui.pyw now properly re-enables button/entry after sleep_loop exits
   - Fixes bug where GUI became permanently stuck after error

3. **Config Loading** - Centralized configuration system
   - All scripts now load from common `config.json`
   - CLI override support for power users
   - Graceful fallback to hardcoded defaults

## Linux Implementation Details

### Design Decisions
- **Two-in-one CLI**: `linux_sleep.py` combines both sleep scheduling and sleep prevention modes (`--mode sleep|prevent`) rather than separate scripts
- **Shared helpers**: `linux_sleep_helpers.py` extracted as function-based module for code reuse between CLI and GUI (follows `config_loader.py` pattern)
- **Permission checking**: Uses `systemctl --dry-run` to detect permission issues before attempting actual sleep (prevents authentication dialogs)
- **Sleep prevention method**: Uses `systemd-inhibit` long-running subprocess pattern (similar to macOS `caffeinate` approach)
- **GUI font compatibility**: Uses `TkDefaultFont` instead of Windows-specific fonts for cross-platform rendering
- **Settings window sizing**: Increased height (480px) to ensure all content including About section is visible and readable

### Cross-Distribution Compatibility
- Targets systemd-based distributions only (Fedora, RHEL, Ubuntu, Debian, Arch, openSUSE)
- No OpenRC or sysvinit support (keeps implementation clean and maintainable)
- Gracefully exits with error message if systemd not detected
- Standard systemctl commands work identically across all supported distributions

## Notes for Future Development

- GUI has deprecated `delayed_sleep()` function in sleep_gui.pyw - remove after verification that `sleep_loop()` is stable
- Consider adding logging to macos_prevent_sleep.py (currently prints to stdout only)
- Windows scripts could be unified into single codebase with conditional logic
- macOS script's exchange rate feature is orthogonal to sleep prevention; could split if expanding functionality
- Consider adding platform detection checks and admin privilege detection for Windows
- Linux: Consider adding desktop notifications via `notify-send` for sleep/wake events
- Linux: Could add systemd service for auto-start on login
- Cross-platform: Could extract shared countdown_timer and error handling patterns into common module

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

systemSleep is a cross-platform system sleep utility with multiple interfaces:
- **CLI scripts** for Windows and macOS sleep management
- **GUI application** (tkinter-based) for Windows with visual timer and controls
- **Exchange rate monitor** for macOS that prevents system sleep while fetching data

The project primarily targets Windows 10+, with a secondary macOS monitoring tool. Python 3.10+ is required.

## Architecture

### Core Components

1. **systemSleep.py** - Windows CLI sleep script
   - Uses `Rundll32.exe Powrprof.dll,SetSuspendState` for sleep commands
   - Supports both immediate sleep and delayed countdown
   - Implements multi-cycle sleep behavior (5-minute gap between cycles after wake)
   - Logs all operations to `sleep.log`
   - Can run as `.pyw` for silent/immediate execution

2. **sleep_gui.pyw** - Windows GUI application
   - Tkinter-based interface with countdown display
   - Takes user input for delay time before sleep
   - Implements threading for non-blocking countdown
   - Multi-cycle loop: after system wakes, resets to 5-minute wait
   - Tooltip helper class for UI hints
   - Has deprecated `delayed_sleep()` function (marked for deletion)

3. **macDontSleep.py** - macOS exchange rate monitor
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

5. **config.json** - Configuration file (now actively used)
   - Script-specific sections: `systemSleep`, `macDontSleep`, `sleep_gui`, `sleep_gui_new`
   - Essential settings only (minimal, not comprehensive):
     - `sleep_command_timeout`: Subprocess timeout (15s default)
     - `wake_delay_minutes`: Delay after wake-up before next cycle (5 min default)
     - `default_delay_minutes`: Initial input field value
     - `api_url`: API endpoint for exchange rates
     - `api_timeout`: API request timeout (10s default)
     - `fetch_interval_seconds`: Exchange rate fetch frequency (300s default)
     - `enable_cycling`: Enable multi-cycle mode (sleep_gui_new only)

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

## Key Design Patterns

- **Configuration Management**: Centralized config loading via `config_loader.py` module
  - All scripts load config from `config.json` on startup
  - CLI scripts (systemSleep.py, macDontSleep.py) accept command-line args to override config
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
python systemSleep.py

# Windows CLI - with CLI arguments (override config)
python systemSleep.py --delay 10 --wake-delay 3 --timeout 20 --log-file custom.log

# Windows CLI - silent immediate sleep (rename .py to .pyw and double-click)
python systemSleep.pyw

# Windows GUI (legacy)
python sleep_gui.pyw

# Windows GUI (modern with settings)
python sleep_gui_new.pyw

# macOS exchange rate monitor with config defaults
python macDontSleep.py

# macOS - with CLI arguments (override config)
python macDontSleep.py --api-url "https://api.example.com" --interval 120
```

### CLI Usage

All CLI scripts support `--help`:
```bash
python systemSleep.py --help
python macDontSleep.py --help
```

### Checking logs
```bash
# View Windows sleep log
cat sleep.log
tail -f sleep.log  # follow new entries
```

### Testing sleep commands manually
```bash
# Windows - test sleep without full script
python -m subprocess.run(['Rundll32.exe', 'Powrprof.dll,SetSuspendState', 'Sleep'])

# macOS - test caffeinate
caffeinate -i &  # start in background
kill %1  # stop
```

## Dependencies

The `.gitignore` ignores all `.txt` files, so requirements must be installed directly or inferred:
- Windows scripts: Built-in modules only (`subprocess`, `logging`, `time`, `threading`, `tkinter`, `argparse`, `json`)
- macOS script: Requires `requests` module (error message guides user to install)
- All scripts: `config_loader.py` module available locally

## Configuration

All scripts use `config_loader.py` to load settings from `config.json`. Priority order:
1. CLI arguments (systemSleep.py, macDontSleep.py only)
2. Values from `config.json` script-specific section
3. Hardcoded defaults in source code

Scripts work without config.json present - all settings have sensible defaults.

**CLI argument examples:**
- `systemSleep.py`: `--delay`, `--wake-delay`, `--timeout`, `--log-file`, `--config`
- `macDontSleep.py`: `--api-url`, `--api-timeout`, `--interval`, `--config`

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

## Notes for Future Development

- GUI has deprecated `delayed_sleep()` function in sleep_gui.pyw - remove after verification that `sleep_loop()` is stable
- Consider adding logging to macDontSleep.py (currently prints to stdout only)
- Windows scripts could be unified into single codebase with conditional logic
- macOS script's exchange rate feature is orthogonal to sleep prevention; could split if expanding functionality
- Consider adding platform detection checks and admin privilege detection for Windows

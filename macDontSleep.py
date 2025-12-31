#!/usr/bin/env python3
"""
Exchange Rate Monitor with macOS Sleep Prevention
Fetches USD to INR exchange rate every 5 minutes while preventing system sleep
"""

import subprocess
import sys
import time
import requests
import signal
import argparse
from datetime import datetime

import config_loader

# Global variable to track caffeinate process
caffeinate_process = None

def start_sleep_prevention():
    """Start caffeinate to prevent macOS from sleeping"""
    global caffeinate_process
    if sys.platform == 'darwin':
        try:
            caffeinate_process = subprocess.Popen(['caffeinate', '-i'])
            print("✓ Sleep prevention activated (caffeinate running)")
        except FileNotFoundError:
            print("⚠ Warning: caffeinate not found (not running on macOS?)")
        except Exception as e:
            print(f"⚠ Warning: Could not start sleep prevention: {e}")
    else:
        print("⚠ Not running on macOS - sleep prevention unavailable")

def stop_sleep_prevention():
    """Stop caffeinate process"""
    global caffeinate_process
    if caffeinate_process:
        try:
            caffeinate_process.terminate()
            caffeinate_process.wait(timeout=2)
            print("✓ Sleep prevention deactivated")
        except Exception as e:
            print(f"⚠ Warning: Error stopping sleep prevention: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Interrupt received, shutting down...")
    stop_sleep_prevention()
    print("👋 Goodbye!")
    sys.exit(0)

def fetch_exchange_rate(api_url, api_timeout):
    """
    Fetch USD to INR exchange rate from API
    Returns: (success: bool, rate: float, error_msg: str)
    """
    try:
        response = requests.get(api_url, timeout=api_timeout)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        # Validate response structure
        if data.get("result") != "success":
            return False, None, "API returned non-success result"
        
        # Extract INR rate
        rates = data.get("rates", {})
        inr_rate = rates.get("INR")
        
        if inr_rate is None:
            return False, None, "INR rate not found in response"
        
        return True, inr_rate, None
        
    except requests.exceptions.Timeout:
        return False, None, f"Request timed out after {api_timeout} seconds"
    except requests.exceptions.ConnectionError:
        return False, None, "Network connection error"
    except requests.exceptions.HTTPError as e:
        return False, None, f"HTTP error: {e}"
    except requests.exceptions.RequestException as e:
        return False, None, f"Request error: {e}"
    except ValueError as e:
        return False, None, f"JSON parsing error: {e}"
    except Exception as e:
        return False, None, f"Unexpected error: {e}"

def display_exchange_rate(rate, timestamp):
    """Display the exchange rate in a formatted way"""
    print(f"\n{'='*50}")
    print(f"⏰ Time: {timestamp}")
    print(f"💱 USD → INR Exchange Rate: ₹{rate:.4f}")
    print(f"{'='*50}")

def main():
    """Main program loop"""
    # Load config
    config = config_loader.get_script_config("macDontSleep")

    # Setup CLI argument parsing
    parser = argparse.ArgumentParser(description="USD to INR Exchange Rate Monitor with macOS Sleep Prevention")
    parser.add_argument("--api-url",
                       help="API URL for exchange rates")
    parser.add_argument("--api-timeout", type=int,
                       help="API request timeout in seconds")
    parser.add_argument("--interval", "-i", type=int,
                       help="Fetch interval in seconds")
    parser.add_argument("--config", default="config.json",
                       help="Path to config file")
    args = parser.parse_args()

    # Merge config with CLI args
    api_url = args.api_url or config.get("api_url", "https://open.er-api.com/v6/latest/USD")
    api_timeout = args.api_timeout or config.get("api_timeout", 10)
    fetch_interval = args.interval or config.get("fetch_interval_seconds", 300)

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print("="*60)
    print("🌍 USD to INR Exchange Rate Monitor")
    print("="*60)
    print("📊 Fetching exchange rate every 5 minutes")
    print("⌨️  Press Ctrl+C to exit")
    print("="*60)
    
    # Start sleep prevention
    start_sleep_prevention()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n[Iteration {iteration}] Fetching data at {timestamp}...")

            success, rate, error = fetch_exchange_rate(api_url, api_timeout)

            if success:
                display_exchange_rate(rate, timestamp)
            else:
                print(f"\n❌ Error fetching exchange rate: {error}")
                print(f"   Will retry in {fetch_interval // 60} minutes...")

            # Wait configured interval
            print(f"\n⏳ Waiting {fetch_interval // 60} minutes until next fetch...")
            time.sleep(fetch_interval)
            
    except KeyboardInterrupt:
        # This should be caught by signal_handler, but just in case
        print("\n\n🛑 Keyboard interrupt detected")
        stop_sleep_prevention()
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        stop_sleep_prevention()
        sys.exit(1)
    finally:
        # Ensure cleanup happens
        stop_sleep_prevention()

if __name__ == "__main__":
    # Check if requests module is available
    try:
        import requests
    except ImportError:
        print("❌ Error: 'requests' module not found")
        print("📦 Install it with: pip install requests")
        sys.exit(1)
    
    main()


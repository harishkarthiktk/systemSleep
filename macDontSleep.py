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
from datetime import datetime

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

def fetch_exchange_rate():
    """
    Fetch USD to INR exchange rate from API
    Returns: (success: bool, rate: float, error_msg: str)
    """
    url = "https://open.er-api.com/v6/latest/USD"
    
    try:
        response = requests.get(url, timeout=10)
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
        return False, None, "Request timed out after 10 seconds"
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
            
            success, rate, error = fetch_exchange_rate()
            
            if success:
                display_exchange_rate(rate, timestamp)
            else:
                print(f"\n❌ Error fetching exchange rate: {error}")
                print("   Will retry in 5 minutes...")
            
            # Wait 5 minutes (300 seconds)
            print(f"\n⏳ Waiting 5 minutes until next fetch...")
            time.sleep(300)
            
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


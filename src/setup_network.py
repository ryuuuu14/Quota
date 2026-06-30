import os
import sys
import socket
import subprocess
import ctypes
import datetime
import shutil

# Ensure data/logs directory exists
LOG_DIR = os.path.join("data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "network_setup.log")

def log(level, msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}\n"
    print(f"[{level}] {msg}")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Failed to write to log file: {e}")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    if is_admin():
        return True
    
    log("INFO", "Requesting administrator privilege elevation...")
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    
    # Run using ShellExecuteW with "runas" verb
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    if int(ret) > 32:
        log("INFO", "Elevation accepted by user.")
        sys.exit(0)
    else:
        log("ERROR", f"Elevation request denied (code {ret}). Network setup requires administrator privileges.")
        return False

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external IP to find local outgoing interface
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def clean_legacy_hosts_file():
    hosts_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "drivers", "etc", "hosts")
    if not os.path.exists(hosts_path):
        return False
    try:
        with open(hosts_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        new_lines = []
        removed_any = False
        for line in lines:
            if "giochuan" in line.lower():
                removed_any = True
                continue
            new_lines.append(line)
            
        if removed_any:
            # Clean trailing blank lines
            while new_lines and new_lines[-1].strip() == "":
                new_lines.pop()
            new_lines.append("\n")
            
            with open(hosts_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            log("INFO", "Cleaned up legacy 'giochuan' domain mappings from hosts file.")
        return True
    except Exception as e:
        log("WARNING", f"Could not modify hosts file (non-critical): {e}")
        return False

def clean_legacy_portproxy():
    try:
        # Delete port proxy rule on port 80 if it exists
        cmd = 'netsh interface portproxy delete v4tov4 listenport=80 listenaddress=0.0.0.0'
        subprocess.run(cmd, shell=True, capture_output=True)
        log("INFO", "Ensured legacy port proxy rule on port 80 is removed.")
        return True
    except Exception as e:
        log("WARNING", f"Could not clean port proxy (non-critical): {e}")
        return False

def configure_firewall(remove=False):
    try:
        # Clean up legacy port 80 rule
        delete_old_cmd = 'netsh advfirewall firewall delete rule name="Quota App Port 80"'
        subprocess.run(delete_old_cmd, shell=True, capture_output=True)
        
        # Always delete the port 1111 rule first to prevent duplicate entries
        delete_cmd = 'netsh advfirewall firewall delete rule name="Quota App Port 1111"'
        subprocess.run(delete_cmd, shell=True, capture_output=True)
        
        if remove:
            log("INFO", "Firewall inbound rule 'Quota App Port 1111' removed.")
            return True
            
        add_cmd = 'netsh advfirewall firewall add rule name="Quota App Port 1111" dir=in action=allow protocol=TCP localport=1111'
        log("INFO", "Adding firewall inbound rule for TCP port 1111...")
        res = subprocess.run(add_cmd, shell=True, capture_output=True, text=True)
        
        if res.returncode == 0:
            log("INFO", "Firewall rule configured successfully for port 1111.")
            return True
        else:
            log("ERROR", f"Firewall command failed: {res.stderr.strip()}")
            return False
    except Exception as e:
        log("ERROR", f"Error during firewall configuration: {e}")
        return False

def main():
    teardown = "--teardown" in sys.argv
    
    if teardown:
        log("INFO", "Starting teardown configuration...")
        if not run_as_admin():
            sys.exit(1)
        clean_legacy_hosts_file()
        clean_legacy_portproxy()
        configure_firewall(remove=True)
        log("INFO", "Teardown complete. Restored original configuration.")
        return

    log("INFO", "Starting network environment configuration...")
    
    if not run_as_admin():
        sys.exit(1)
        
    lan_ip = get_lan_ip()
    log("INFO", f"Detected Server LAN IP: {lan_ip}")
    
    clean_legacy_hosts_file()
    clean_legacy_portproxy()
    f_ok = configure_firewall()
    
    if f_ok:
        log("INFO", "All network configurations successfully applied!")
        log("INFO", f"Unified Server URL: http://{lan_ip}:1111")
    else:
        log("ERROR", "Some network configurations failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

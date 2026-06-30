import os
import sys
import socket
import subprocess
import urllib.request

LOG_DIR = os.path.join("data", "logs")
SETUP_LOG = os.path.join(LOG_DIR, "network_setup.log")

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
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

def check_service_http(url):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False

def check_port_bound(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect((ip, port))
        return True
    except Exception:
        return False
    finally:
        s.close()

def get_last_lines(filepath, count=5):
    if not os.path.exists(filepath):
        return ["Log file does not exist yet."]
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [line.strip() for line in lines[-count:]]
    except Exception as e:
        return [f"Error reading log file: {e}"]

def main():
    lan_ip = get_lan_ip()
    hostname = socket.gethostname()
    
    print("==========================================================")
    print("   Quota System - Offline Network Diagnostics Console")
    print("==========================================================")
    print(f"Server Name:  {hostname}")
    print(f"LAN IP:       {lan_ip}")
    print("----------------------------------------------------------")
    
    # 1. Check Firewall Inbound TCP 1111
    fw_res = subprocess.run("netsh advfirewall firewall show rule name=\"Quota App Port 1111\"", shell=True, capture_output=True, text=True)
    has_fw = "Quota App Port 1111" in fw_res.stdout
    print(f"Firewall Rule (TCP 1111):     [{'OK' if has_fw else 'MISSING'}]")
    
    # 2. Check Services
    streamlit_running = check_port_bound("127.0.0.1", 1111)
    print(f"Streamlit service (:1111):    [{'RUNNING' if streamlit_running else 'STOPPED'}]")
    
    # 3. Check Endpoint Accessibility
    http_local_base = check_service_http("http://127.0.0.1:1111")
    http_lan = check_service_http(f"http://{lan_ip}:1111")
    
    print(f"Access Local (127.0.0.1:1111): [{'SUCCESS' if http_local_base else 'FAILED'}]")
    print(f"Access Server IP ({lan_ip}:1111): [{'SUCCESS' if http_lan else 'FAILED'}]")
    
    # 4. Recent Setup Logs
    print("----------------------------------------------------------")
    print("   Recent Network Setup Audit Logs (Last 5)")
    print("----------------------------------------------------------")
    for line in get_last_lines(SETUP_LOG, 5):
        print(f"  {line}")
            
    print("==========================================================")

if __name__ == "__main__":
    main()

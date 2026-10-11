#!/usr/bin/env python3
"""
Technicolor DJA0230 Timor-Leste 4G/LTE Carrier Setup Tool
Part of Sagedral-Router Toolkit
"""

import sys
import hashlib
import paramiko
import paramiko.kex_group14 as kg14
from cryptography.hazmat.primitives import hashes

class KexGroup14SHA1(kg14.KexGroup14SHA256):
    name = 'diffie-hellman-group14-sha1'
    hash_algo = hashlib.sha1

paramiko.Transport._kex_info['diffie-hellman-group14-sha1'] = KexGroup14SHA1
paramiko.Transport._preferred_kex = ('diffie-hellman-group14-sha1',) + paramiko.Transport._preferred_kex
paramiko.Transport._key_info['ssh-rsa'] = paramiko.RSAKey
paramiko.Transport._preferred_keys = ('ssh-rsa',) + paramiko.Transport._preferred_keys
paramiko.RSAKey.HASHES['ssh-rsa'] = hashes.SHA1

CARRIERS = {
    "1": ("Telemor", "m-internet"),
    "2": ("Timor Telecom", "internet"),
    "3": ("Telkomcel Timor-Leste", "telkomcel")
}

def connect_ssh(ip, user="root", pwd="root"):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=pwd, timeout=8)
    return client

def configure_carrier(client, carrier_name, apn):
    print(f"[*] Konfigura operadór {carrier_name} ho APN '{apn}'...")
    
    script = f"""
# 1. Hamate WanSensing (atu 4G LTE lakan kedas sein kabu WAN/DSL)
uci set wansensing.global.enable='0'
uci commit wansensing
/etc/init.d/wansensing stop 2>/dev/null
/etc/init.d/wansensing disable 2>/dev/null

# 2. Hamate CWMP auto update Telstra
uci set cwmpd.cwmpd_config.state=0
uci commit cwmpd
/etc/init.d/cwmpd stop 2>/dev/null
/etc/init.d/cwmpd disable 2>/dev/null

# 3. Konfigura modem mobel & APN
uci set network.wwan.apn='{apn}'
uci set network.wwan.enabled='1'
uci set network.wwan.auto='1'
uci set network.wwan.proto='dhcp'
uci commit network

# 4. Konfigura mobiled / LTE band auto selection
uci set mobiled.device_0.enabled='1'
uci set mobiled.device_0.radio='auto'
uci set mobiled.device_0.network='lte'
uci set mobiled.device_0.apn='{apn}'
uci commit mobiled 2>/dev/null

# 5. Reinicia servisu rede
/etc/init.d/network restart
/etc/init.d/mobiled restart 2>/dev/null
sync
"""
    stdin, stdout, stderr = client.exec_command(script)
    stdout.read()
    print(f"[✔] Operadór {carrier_name} ho APN '{apn}' susesu konfigura!")

def check_carrier_status(client):
    cmd = """
echo "=== WWAN STATUS ==="
ifconfig wwan0 2>/dev/null || ifconfig eth5 2>/dev/null
echo "=== APN CONFIG ==="
uci get network.wwan.apn 2>/dev/null
echo "=== WAN IP ==="
uci get network.wwan.ipaddr 2>/dev/null || ip addr show wwan0 2>/dev/null | grep 'inet '
"""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='ignore'))

def main():
    print("================================================================")
    print("  TECHNICOLOR DJA0230 4G/LTE CARRIER CONFIGURATION (TETUN)")
    print("================================================================")
    
    ip = input("Hatama IP Modem [default: 192.168.0.1]: ").strip() or "192.168.0.1"
    user = input("Username SSH [default: root]: ").strip() or "root"
    pwd = input("Password SSH [default: root]: ").strip() or "root"

    try:
        client = connect_ssh(ip, user, pwd)
        print(f"[✔] Susesu halo ligasaun SSH ba {ip}!")
    except Exception as e:
        print(f"[-] Falha liga ba SSH: {e}")
        sys.exit(1)

    print("\nOpsaun Operadór Timor-Leste:")
    print(" 1. Telemor (APN: m-internet)")
    print(" 2. Timor Telecom (APN: internet)")
    print(" 3. Telkomcel Timor-Leste (APN: telkomcel)")
    print(" 4. Manual / Custom APN")
    
    choice = input("\nFiel operadór [1-4, default 1]: ").strip() or "1"
    if choice in CARRIERS:
        c_name, c_apn = CARRIERS[choice]
    elif choice == "4":
        c_name = "Custom"
        c_apn = input("Hatama APN: ").strip()
    else:
        c_name, c_apn = CARRIERS["1"]

    configure_carrier(client, c_name, c_apn)
    print("\n[*] Verifika estatutu rede LTE...")
    check_carrier_status(client)
    client.close()

if __name__ == "__main__":
    main()

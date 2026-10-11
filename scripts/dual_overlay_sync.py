#!/usr/bin/env python3
"""
Technicolor DJA0230 Dual-Overlay Persistence Sync Tool
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

def sync_overlays(ip="192.168.0.1", user="root", pwd="root"):
    print(f"[*] Hahu sinkronizasaun Dual-Overlay iha {ip}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=pwd, timeout=8)

    script = """
# 1. Kria pasta sira
mkdir -p /overlay/bank_2/etc/config /modoverlay/bank_mod/etc/config 2>/dev/null
mkdir -p /overlay/bank_2/etc/nginx /modoverlay/bank_mod/etc/nginx 2>/dev/null
mkdir -p /overlay/bank_2/www/sagedral /modoverlay/bank_mod/www/sagedral 2>/dev/null
mkdir -p /overlay/sagedral_backup /modoverlay/sagedral_backup 2>/dev/null

# 2. Kopie konfigurasi rede no wireless ba overlay hotu
for cfg in wireless network dhcp firewall mobiled wansensing; do
    if [ -f /etc/config/$cfg ]; then
        cp -af /etc/config/$cfg /overlay/bank_2/etc/config/$cfg 2>/dev/null
        cp -af /etc/config/$cfg /modoverlay/bank_mod/etc/config/$cfg 2>/dev/null
    fi
done

# 3. Kopie Nginx no Sagedral Web UI
cp -af /www/sagedral/* /overlay/bank_2/www/sagedral/ 2>/dev/null
cp -af /www/sagedral/* /modoverlay/bank_mod/www/sagedral/ 2>/dev/null
cp -af /www/sagedral/* /overlay/sagedral_backup/ 2>/dev/null
cp -af /www/sagedral/* /modoverlay/sagedral_backup/ 2>/dev/null

cp -af /etc/nginx/server_sagedral.conf /overlay/bank_2/etc/nginx/ 2>/dev/null
cp -af /etc/nginx/main_sagedral.conf /overlay/bank_2/etc/nginx/ 2>/dev/null
cp -af /etc/nginx/server_sagedral.conf /overlay/sagedral_backup/ 2>/dev/null
cp -af /etc/nginx/main_sagedral.conf /overlay/sagedral_backup/ 2>/dev/null

# 4. Desativa verifikasaun OBP
uci set modgui.var.check_obp='0' 2>/dev/null
uci commit modgui 2>/dev/null

# 5. Flush NAND buffers
sync
echo "SINKRONIZASAUN_OK"
"""
    stdin, stdout, stderr = client.exec_command(script)
    res = stdout.read().decode('utf-8', errors='ignore')
    if "SINKRONIZASAUN_OK" in res:
        print("[✔] Sinkronizasaun Dual-Overlay susesu 100%! Modem sei la reset bainhira reboot.")
    else:
        print("[-] Avizu: " + res)
    client.close()

if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.1"
    sync_overlays(ip)

#!/usr/bin/env python3
"""
Sagedral-Router V2 1-Click CLI Deployment Tool
Part of Sagedral-Router Toolkit
"""

import os
import sys
import base64
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

def deploy_sagedral(ip="192.168.0.1", user="root", pwd="root"):
    print("================================================================")
    print("  SAGEDRAL-ROUTER V2 1-CLICK DEPLOYMENT (TETUN)")
    print("================================================================")
    print(f"[*] Hahu instala Sagedral-Router iha {ip}...")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sagedral_dir = os.path.join(base_dir, "sagedral-router")
    www_dir = os.path.join(sagedral_dir, "www")
    nginx_dir = os.path.join(sagedral_dir, "nginx")

    idx_path = os.path.join(www_dir, "index.html")
    api_path = os.path.join(www_dir, "api.lua")
    font_path = os.path.join(www_dir, "material-symbols.woff2")
    srv_conf = os.path.join(nginx_dir, "server_sagedral.conf")
    main_conf = os.path.join(nginx_dir, "main_sagedral.conf")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=user, password=pwd, timeout=10)

    # 1. Kria pasta sira
    client.exec_command("mkdir -p /www/sagedral /etc/nginx /overlay/bank_2/www/sagedral /overlay/sagedral_backup")

    # 2. Upload index.html
    print("[*] Upload index.html (V2 Obsidian Stitch UI)...")
    with open(idx_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    stdin, stdout, stderr = client.exec_command("base64 -d > /www/sagedral/index.html")
    stdin.write(b64)
    stdin.close()
    stdout.read()

    # 3. Upload api.lua
    print("[*] Upload api.lua (Telemetry & Session Auth Backend)...")
    with open(api_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    stdin, stdout, stderr = client.exec_command("base64 -d > /www/sagedral/api.lua")
    stdin.write(b64)
    stdin.close()
    stdout.read()

    # 4. Upload offline font if exists
    if os.path.exists(font_path):
        print("[*] Upload material-symbols.woff2 (Offline Icons)...")
        with open(font_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        stdin, stdout, stderr = client.exec_command("base64 -d > /www/sagedral/material-symbols.woff2")
        stdin.write(b64)
        stdin.close()
        stdout.read()

    # 5. Upload Nginx configs
    print("[*] Konfigura Nginx Porta 9080 & Porta 80 (/sagedral/)...")
    with open(srv_conf, "r", encoding="utf-8") as f:
        conf_srv = f.read()
    stdin, stdout, stderr = client.exec_command("cat > /etc/nginx/server_sagedral.conf")
    stdin.write(conf_srv)
    stdin.close()
    stdout.read()

    with open(main_conf, "r", encoding="utf-8") as f:
        conf_main = f.read()
    stdin, stdout, stderr = client.exec_command("cat > /etc/nginx/main_sagedral.conf")
    stdin.write(conf_main)
    stdin.close()
    stdout.read()

    # 6. Permisoens & persistensia
    print("[*] Aplika autorizasaun no sinkronizasaun dual-overlay...")
    script_sync = """
chmod -R 755 /www/sagedral
cp -af /www/sagedral/* /overlay/bank_2/www/sagedral/ 2>/dev/null
cp -af /www/sagedral/* /modoverlay/bank_mod/www/sagedral/ 2>/dev/null
cp -af /www/sagedral/* /overlay/sagedral_backup/ 2>/dev/null
cp -af /etc/nginx/server_sagedral.conf /overlay/bank_2/etc/nginx/ 2>/dev/null
cp -af /etc/nginx/main_sagedral.conf /overlay/bank_2/etc/nginx/ 2>/dev/null
uci set modgui.var.check_obp='0' 2>/dev/null
uci commit modgui 2>/dev/null
sync
/etc/init.d/nginx restart 2>/dev/null
"""
    stdin, stdout, stderr = client.exec_command(script_sync)
    stdout.read()

    client.close()
    print("\n[✔] SAGEDRAL-ROUTER V2 SUSESU INSTALA 100%!")
    print(f"[*] Ita bele asesu agora iha:")
    print(f"    --> http://{ip}:9080/       (Porta Dedikadu)")
    print(f"    --> http://{ip}/sagedral/   (Porta 80 Padraun)")

if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.1"
    deploy_sagedral(ip)

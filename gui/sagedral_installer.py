#!/usr/bin/env python3
"""
Sagedral-Router 1-Click Installer & Carrier Manager (GUI)
Part of Sagedral-Router Toolkit
Tetun Language Interface
"""

import os
import sys
import time
import base64
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import paramiko
import paramiko.kex_group14 as kg14
from cryptography.hazmat.primitives import hashes

# Paramiko legacy crypto compatibility for Homeware OpenWrt
class KexGroup14SHA1(kg14.KexGroup14SHA256):
    name = 'diffie-hellman-group14-sha1'
    hash_algo = hashlib.sha1

paramiko.Transport._kex_info['diffie-hellman-group14-sha1'] = KexGroup14SHA1
paramiko.Transport._preferred_kex = ('diffie-hellman-group14-sha1',) + paramiko.Transport._preferred_kex
paramiko.Transport._key_info['ssh-rsa'] = paramiko.RSAKey
paramiko.Transport._preferred_keys = ('ssh-rsa',) + paramiko.Transport._preferred_keys
paramiko.RSAKey.HASHES['ssh-rsa'] = hashes.SHA1

DARK_BG = "#0f172a"
PANEL_BG = "#1e293b"
CARD_BG = "#111827"
ACCENT_CYAN = "#38bdf8"
ACCENT_GREEN = "#4ade80"
TEXT_COLOR = "#f8fafc"
TEXT_MUTED = "#94a3b8"

class SagedralInstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sagedral-Router V2 - 1-Click Installer & Carrier Suite")
        self.geometry("860x680")
        self.configure(bg=DARK_BG)
        self.resizable(True, True)

        self.ssh_client = None
        self.is_connected = False

        self._create_widgets()

    def _create_widgets(self):
        # Header Banner
        header = tk.Frame(self, bg=CARD_BG, height=75, padx=20, pady=12)
        header.pack(fill="x", side="top")

        t_box = tk.Frame(header, bg=CARD_BG)
        t_box.pack(side="left")
        tk.Label(t_box, text="SAGEDRAL-ROUTER V2 NOC", font=("Segoe UI", 15, "bold"), fg=ACCENT_GREEN, bg=CARD_BG).pack(anchor="w")
        tk.Label(t_box, text="Instalador Automátiku & Konfiguradór 4G LTE Timor-Leste (DJA0230)", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")

        # Top Connection Bar
        conn_bar = tk.Frame(self, bg=PANEL_BG, padx=15, pady=10)
        conn_bar.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(conn_bar, text="IP Modem:", font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG).grid(row=0, column=0, padx=4)
        self.entry_ip = tk.Entry(conn_bar, font=("Consolas", 10), width=14, bg="#0f172a", fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        self.entry_ip.insert(0, "192.168.0.1")
        self.entry_ip.grid(row=0, column=1, padx=4)

        tk.Label(conn_bar, text="User:", font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG).grid(row=0, column=2, padx=4)
        self.entry_user = tk.Entry(conn_bar, font=("Consolas", 10), width=8, bg="#0f172a", fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        self.entry_user.insert(0, "root")
        self.entry_user.grid(row=0, column=3, padx=4)

        tk.Label(conn_bar, text="Password:", font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG).grid(row=0, column=4, padx=4)
        self.entry_pwd = tk.Entry(conn_bar, font=("Consolas", 10), width=10, show="*", bg="#0f172a", fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        self.entry_pwd.insert(0, "root")
        self.entry_pwd.grid(row=0, column=5, padx=4)

        self.btn_conn = tk.Button(conn_bar, text="Koneka SSH", font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="#ffffff", padx=12, command=self._toggle_ssh)
        self.btn_conn.grid(row=0, column=6, padx=8)

        self.lbl_conn_status = tk.Label(conn_bar, text="● Desconectadu", font=("Segoe UI", 9), fg="#f87171", bg=PANEL_BG)
        self.lbl_conn_status.grid(row=0, column=7, padx=8)

        # Tab Control
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL_BG, foreground=TEXT_COLOR, padding=[16, 7], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)

        self.tab_install = tk.Frame(notebook, bg=DARK_BG, padx=15, pady=15)
        self.tab_carrier = tk.Frame(notebook, bg=DARK_BG, padx=15, pady=15)
        self.tab_maint = tk.Frame(notebook, bg=DARK_BG, padx=15, pady=15)

        notebook.add(self.tab_install, text="1. Instala Sagedral-Router V2")
        notebook.add(self.tab_carrier, text="2. Konfigura SIM 4G LTE")
        notebook.add(self.tab_maint, text="3. Manutensaun & Reboot")

        self._build_install_tab()
        self._build_carrier_tab()
        self._build_maint_tab()

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _toggle_ssh(self):
        if self.is_connected:
            if self.ssh_client:
                self.ssh_client.close()
            self.is_connected = False
            self.btn_conn.config(text="Koneka SSH", bg="#2563eb")
            self.lbl_conn_status.config(text="● Desconectadu", fg="#f87171")
            self._log("[*] Desconectadu husi router.")
        else:
            ip = self.entry_ip.get().strip()
            user = self.entry_user.get().strip()
            pwd = self.entry_pwd.get().strip()
            self._log(f"[*] Halo ligasaun SSH ba {ip} ({user})...")

            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(ip, username=user, password=pwd, timeout=6)
                self.is_connected = True
                self.btn_conn.config(text="Hakotu SSH", bg="#dc2626")
                self.lbl_conn_status.config(text="● Conectadu (Root)", fg=ACCENT_GREEN)
                self._log(f"[✔] Ligasaun SSH susesu ba {ip}!")

                # Query router info
                stdin, stdout, stderr = self.ssh_client.exec_command("cat /proc/banktable/booted 2>/dev/null; uci get version.@version[0].marketing_version 2>/dev/null")
                res = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
                b_info = res[0] if len(res) > 0 else 'Unknown'
                v_info = res[1] if len(res) > 1 else 'Unknown'
                self._log(f"[*] Bank Ativu: {b_info} | Versaun Firmware: {v_info}")
            except Exception as e:
                self._log(f"[-] Erru ligasaun SSH: {e}")
                messagebox.showerror("Erru SSH", f"Labele halo ligasaun SSH: {e}")

    def _build_install_tab(self):
        desc = (
            "Fitur ne'e sei instala Sagedral-Router V2 ba router Technicolor ho kompletu:\n"
            "• Web UI Obsidian Stitch (Offline font & styling)\n"
            "• Lua Backend ho Autentikasaun Sesaun estritu & Kontrole Bandwidth\n"
            "• Konfigurasaun Nginx Ganda (Porta 9080 & Porta 80 /sagedral/)\n"
            "• Imunidade Total ba Reboot (Sinkronizasaun Dual-Overlay & Desativa OBP reset)"
        )
        tk.Label(self.tab_install, text=desc, font=("Segoe UI", 9), fg=TEXT_COLOR, bg=DARK_BG, justify="left").pack(anchor="w", pady=(0, 10))

        btn_box = tk.Frame(self.tab_install, bg=DARK_BG)
        btn_box.pack(fill="x", pady=6)

        self.btn_deploy = tk.Button(btn_box, text="🚀 HAHU INSTALA 1-CLICK SAGEDRAL-ROUTER", font=("Segoe UI", 11, "bold"), bg="#15803d", fg="#ffffff", padx=16, pady=8, command=self._start_deploy)
        self.btn_deploy.pack(side="left")

        # Console
        log_frame = tk.LabelFrame(self.tab_install, text="Progresu Instalasaun", font=("Segoe UI", 9, "bold"), fg=ACCENT_CYAN, bg=PANEL_BG, padx=8, pady=6)
        log_frame.pack(fill="both", expand=True, pady=10)

        self.log_text = tk.Text(log_frame, bg="#020617", fg="#38bdf8", font=("Consolas", 9), insertbackground=TEXT_COLOR)
        self.log_text.pack(fill="both", expand=True)

    def _start_deploy(self):
        if not self.is_connected or not self.ssh_client:
            messagebox.showwarning("Atensaun", "Favor halo ligasaun SSH uluk antes instala!")
            return

        threading.Thread(target=self._deploy_worker, daemon=True).start()

    def _deploy_worker(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sagedral_dir = os.path.join(base_dir, "sagedral-router")
        www_dir = os.path.join(sagedral_dir, "www")
        nginx_dir = os.path.join(sagedral_dir, "nginx")

        idx_path = os.path.join(www_dir, "index.html")
        api_path = os.path.join(www_dir, "api.lua")
        font_path = os.path.join(www_dir, "material-symbols.woff2")
        srv_conf = os.path.join(nginx_dir, "server_sagedral.conf")
        main_conf = os.path.join(nginx_dir, "main_sagedral.conf")

        self._log("\n[*] [1/6] Prepara pasta sira iha modem...")
        self.ssh_client.exec_command("mkdir -p /www/sagedral /etc/nginx /overlay/bank_2/www/sagedral /overlay/sagedral_backup")

        self._log("[*] [2/6] Upload index.html (UI V2)...")
        with open(idx_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        stdin, stdout, stderr = self.ssh_client.exec_command("base64 -d > /www/sagedral/index.html")
        stdin.write(b64); stdin.close(); stdout.read()

        self._log("[*] [3/6] Upload api.lua (Backend & Session Auth)...")
        with open(api_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        stdin, stdout, stderr = self.ssh_client.exec_command("base64 -d > /www/sagedral/api.lua")
        stdin.write(b64); stdin.close(); stdout.read()

        if os.path.exists(font_path):
            self._log("[*] [4/6] Upload material-symbols.woff2 (Offline Icons)...")
            with open(font_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
            stdin, stdout, stderr = self.ssh_client.exec_command("base64 -d > /www/sagedral/material-symbols.woff2")
            stdin.write(b64); stdin.close(); stdout.read()

        self._log("[*] [5/6] Konfigura Nginx Porta 9080 & Porta 80 (/sagedral/)...")
        with open(srv_conf, "r", encoding="utf-8") as f:
            c1 = f.read()
        stdin, stdout, stderr = self.ssh_client.exec_command("cat > /etc/nginx/server_sagedral.conf")
        stdin.write(c1); stdin.close(); stdout.read()

        with open(main_conf, "r", encoding="utf-8") as f:
            c2 = f.read()
        stdin, stdout, stderr = self.ssh_client.exec_command("cat > /etc/nginx/main_sagedral.conf")
        stdin.write(c2); stdin.close(); stdout.read()

        self._log("[*] [6/6] Aplika imunidade ba reboot (Dual-Overlay persistence)...")
        sync_cmd = """
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
        stdin, stdout, stderr = self.ssh_client.exec_command(sync_cmd)
        stdout.read()

        ip = self.entry_ip.get().strip()
        self._log(f"\n[✔] SAGEDRAL-ROUTER V2 SUSESU INSTALA 100%!")
        self._log(f"    --> Asesu Porta 9080: http://{ip}:9080/")
        self._log(f"    --> Asesu Porta 80:   http://{ip}/sagedral/")
        messagebox.showinfo("Susesu", f"Sagedral-Router V2 susesu instala!\nIta bele asesu iha http://{ip}:9080/ ka http://{ip}/sagedral/")

    def _build_carrier_tab(self):
        card = tk.LabelFrame(self.tab_carrier, text="Konfigurasaun SIM 4G LTE Timor-Leste", font=("Segoe UI", 10, "bold"), fg=ACCENT_CYAN, bg=PANEL_BG, padx=15, pady=12)
        card.pack(fill="x", pady=5)

        self.carrier_var = tk.StringVar(value="telemor")
        r1 = tk.Radiobutton(card, text="Telemor (APN: m-internet)", variable=self.carrier_var, value="telemor", bg=PANEL_BG, fg=TEXT_COLOR, selectcolor=CARD_BG, font=("Segoe UI", 9))
        r1.pack(anchor="w", pady=3)

        r2 = tk.Radiobutton(card, text="Timor Telecom (APN: internet)", variable=self.carrier_var, value="tt", bg=PANEL_BG, fg=TEXT_COLOR, selectcolor=CARD_BG, font=("Segoe UI", 9))
        r2.pack(anchor="w", pady=3)

        r3 = tk.Radiobutton(card, text="Telkomcel Timor-Leste (APN: telkomcel)", variable=self.carrier_var, value="telkomcel", bg=PANEL_BG, fg=TEXT_COLOR, selectcolor=CARD_BG, font=("Segoe UI", 9))
        r3.pack(anchor="w", pady=3)

        r4 = tk.Radiobutton(card, text="Custom APN:", variable=self.carrier_var, value="custom", bg=PANEL_BG, fg=TEXT_COLOR, selectcolor=CARD_BG, font=("Segoe UI", 9))
        r4.pack(anchor="w", pady=3)

        self.entry_custom_apn = tk.Entry(card, font=("Consolas", 9), bg="#0f172a", fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=25)
        self.entry_custom_apn.pack(anchor="w", padx=24, pady=2)

        btn_box = tk.Frame(card, bg=PANEL_BG)
        btn_box.pack(fill="x", pady=10)

        btn_apply = tk.Button(btn_box, text="⚡ APLIKA KONFIGURASAUN SIM", font=("Segoe UI", 10, "bold"), bg="#0284c7", fg="#ffffff", padx=14, pady=6, command=self._apply_carrier)
        btn_apply.pack(side="left")

        btn_check = tk.Button(btn_box, text="Verifika Sinais LTE", font=("Segoe UI", 9), bg="#475569", fg=TEXT_COLOR, padx=10, pady=6, command=self._check_lte_status)
        btn_check.pack(side="left", padx=10)

    def _apply_carrier(self):
        if not self.is_connected or not self.ssh_client:
            messagebox.showwarning("Atensaun", "Favor halo ligasaun SSH uluk!")
            return

        c = self.carrier_var.get()
        if c == "telemor": apn = "m-internet"; name = "Telemor"
        elif c == "tt": apn = "internet"; name = "Timor Telecom"
        elif c == "telkomcel": apn = "telkomcel"; name = "Telkomcel"
        else: apn = self.entry_custom_apn.get().strip() or "internet"; name = "Custom"

        self._log(f"\n[*] Aplika APN '{apn}' ba {name}...")
        script = f"""
uci set wansensing.global.enable='0'
uci commit wansensing
/etc/init.d/wansensing stop 2>/dev/null; /etc/init.d/wansensing disable 2>/dev/null

uci set cwmpd.cwmpd_config.state=0
uci commit cwmpd
/etc/init.d/cwmpd stop 2>/dev/null; /etc/init.d/cwmpd disable 2>/dev/null

uci set network.wwan.apn='{apn}'
uci set network.wwan.enabled='1'
uci set network.wwan.auto='1'
uci commit network

/etc/init.d/network restart
sync
"""
        self.ssh_client.exec_command(script)
        self._log(f"[✔] Konfigurasaun SIM ba {name} susesu aplika!")
        messagebox.showinfo("Susesu", f"Konfigurasaun APN '{apn}' susesu aplika!")

    def _check_lte_status(self):
        if not self.is_connected or not self.ssh_client:
            messagebox.showwarning("Atensaun", "Favor halo ligasaun SSH uluk!")
            return
        
        stdin, stdout, stderr = self.ssh_client.exec_command("uci get network.wwan.apn 2>/dev/null; ifconfig wwan0 2>/dev/null || ifconfig eth5 2>/dev/null")
        self._log("\n=== ESTATUTU REDE LTE ===")
        self._log(stdout.read().decode('utf-8', errors='ignore'))

    def _build_maint_tab(self):
        card = tk.LabelFrame(self.tab_maint, text="Operasaun Manutensaun & Reboot Seguru", font=("Segoe UI", 10, "bold"), fg=ACCENT_CYAN, bg=PANEL_BG, padx=15, pady=12)
        card.pack(fill="x", pady=5)

        info = "Bainhira reboot modem husi ne'e, sistema sei sinkroniza NAND flash 3x antes haruka /sbin/reboot hodi la lakon konfigurasaun."
        tk.Label(card, text=info, font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG, justify="left").pack(anchor="w", pady=5)

        btn_reboot = tk.Button(card, text="🔄 REBOOT MODEM SEGRU (COMMIT NAND)", font=("Segoe UI", 10, "bold"), bg="#dc2626", fg="#ffffff", padx=14, pady=6, command=self._safe_reboot)
        btn_reboot.pack(anchor="w", pady=8)

        btn_lock = tk.Button(card, text="🔒 Kunci Bank 1 (switchover)", font=("Segoe UI", 9), bg="#475569", fg=TEXT_COLOR, padx=10, pady=4, command=self._lock_bank)
        btn_lock.pack(anchor="w", pady=4)

    def _safe_reboot(self):
        if not self.is_connected or not self.ssh_client:
            messagebox.showwarning("Atensaun", "Favor halo ligasaun SSH uluk!")
            return
        if not messagebox.askyesno("Konfirmasaun", "Ita certu hakarak reboot modem agora? Konfigurasaun hotu sei salva seguru."):
            return

        self._log("\n[*] Salva konfigurasaun no haruka orden reboot...")
        script = """
for cfg in wireless network dhcp firewall mobiled; do
    cp -af /etc/config/$cfg /overlay/bank_2/etc/config/$cfg 2>/dev/null
    cp -af /etc/config/$cfg /modoverlay/bank_mod/etc/config/$cfg 2>/dev/null
done
sync; sync; sync
/sbin/reboot &
"""
        self.ssh_client.exec_command(script)
        self._log("[✔] Modem hahu reboot hela. Favor hein minutu 1-2...")
        self._toggle_ssh()

    def _lock_bank(self):
        if not self.is_connected or not self.ssh_client:
            messagebox.showwarning("Atensaun", "Favor halo ligasaun SSH uluk!")
            return
        self.ssh_client.exec_command("switchover 2>/dev/null")
        self._log("[✔] Komandu switchover haruka ona.")
        messagebox.showinfo("Susesu", "Komandu switchover susesu!")

if __name__ == "__main__":
    app = SagedralInstallerGUI()
    app.mainloop()

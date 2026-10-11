#!/usr/bin/env python3
"""
Technicolor DJA0230 Downgrade & Recovery Tool (GUI)
Part of Sagedral-Router Toolkit
Tetun Language Interface
"""

import os
import sys
import time
import socket
import struct
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

DARK_BG = "#131315"
PANEL_BG = "#1c1c1f"
ACCENT_GREEN = "#4edea3"
ACCENT_BLUE = "#64b5f6"
TEXT_COLOR = "#f1f1f1"
TEXT_MUTED = "#9e9e9e"

class DowngradeToolGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Technicolor DJA0230 - Downgrade & Recovery Tool")
        self.geometry("820x640")
        self.configure(bg=DARK_BG)
        self.resizable(True, True)

        self.server_thread = None
        self.is_server_running = False
        self.tftp_sock = None
        self.bootp_sock = None

        self._create_widgets()

    def _create_widgets(self):
        # Header Banner
        header = tk.Frame(self, bg=PANEL_BG, height=70, padx=20, pady=12)
        header.pack(fill="x", side="top")

        title_lbl = tk.Label(header, text="TECHNICOLOR DJA0230 FIRMWARE RECOVERY", font=("Segoe UI", 14, "bold"), fg=ACCENT_GREEN, bg=PANEL_BG)
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(header, text="Ferramenta Downgrade CFE BOOTP/TFTP & Bank Switcher ba Timor-Leste", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=PANEL_BG)
        sub_lbl.pack(anchor="w")

        # Tab Control
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL_BG, foreground=TEXT_COLOR, padding=[15, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", ACCENT_BLUE)], foreground=[("selected", "#000000")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # Tabs
        self.tab_flasher = tk.Frame(notebook, bg=DARK_BG, padx=15, pady=15)
        self.tab_bank = tk.Frame(notebook, bg=DARK_BG, padx=15, pady=15)
        self.tab_guide = tk.Frame(notebook, bg=DARK_BG, padx=15, pady=15)

        notebook.add(self.tab_flasher, text="1. CFE BOOTP/TFTP Flasher")
        notebook.add(self.tab_bank, text="2. Bank Switch (LED Biru)")
        notebook.add(self.tab_guide, text="3. Guia Root & Exploit")

        self._build_flasher_tab()
        self._build_bank_tab()
        self._build_guide_tab()

    def _build_flasher_tab(self):
        # Config Card
        card = tk.LabelFrame(self.tab_flasher, text="Konfigurasaun Rede & Firmware", font=("Segoe UI", 10, "bold"), fg=ACCENT_BLUE, bg=PANEL_BG, padx=15, pady=12)
        card.pack(fill="x", side="top", pady=5)

        # Host IP
        lbl_ip = tk.Label(card, text="IP PC Ethernet (Statiku):", font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG)
        lbl_ip.grid(row=0, column=0, sticky="w", pady=4)
        self.entry_ip = tk.Entry(card, font=("Consolas", 10), bg="#28282b", fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        self.entry_ip.insert(0, "192.168.1.100")
        self.entry_ip.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        # Client IP
        lbl_clip = tk.Label(card, text="IP Propostu ba Router:", font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG)
        lbl_clip.grid(row=0, column=2, sticky="w", pady=4)
        self.entry_clip = tk.Entry(card, font=("Consolas", 10), bg="#28282b", fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        self.entry_clip.insert(0, "192.168.1.101")
        self.entry_clip.grid(row=0, column=3, sticky="w", padx=10, pady=4)

        # Firmware File Picker
        lbl_fw = tk.Label(card, text="Arkivu Firmware (.rbi):", font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG)
        lbl_fw.grid(row=1, column=0, sticky="w", pady=8)
        
        self.entry_fw = tk.Entry(card, font=("Consolas", 9), bg="#28282b", fg=TEXT_COLOR, width=38, insertbackground=TEXT_COLOR)
        # Auto detect local firmware
        default_fw = ""
        for f in ["firmware.rbi", "vbnt-v_18.1.c.0549-MR17-RB.rbi", "f.rbi"]:
            if os.path.exists(f):
                default_fw = os.path.abspath(f)
                break
        self.entry_fw.insert(0, default_fw)
        self.entry_fw.grid(row=1, column=1, columnspan=2, sticky="w", padx=10, pady=8)

        btn_browse = tk.Button(card, text="Buka Arkivu...", font=("Segoe UI", 8), bg="#38383e", fg=TEXT_COLOR, command=self._browse_fw)
        btn_browse.grid(row=1, column=3, sticky="w", padx=5, pady=8)

        # Actions & Status
        btn_frame = tk.Frame(self.tab_flasher, bg=DARK_BG, pady=8)
        btn_frame.pack(fill="x")

        self.btn_start = tk.Button(btn_frame, text="▶ HAHU RECOVERY SERVER", font=("Segoe UI", 11, "bold"), bg="#1b5e20", fg="#ffffff", padx=18, pady=8, command=self._toggle_server)
        self.btn_start.pack(side="left", padx=5)

        self.lbl_server_status = tk.Label(btn_frame, text="● Server Paradu", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=DARK_BG)
        self.lbl_server_status.pack(side="left", padx=15)

        # Instruction strip
        inst_card = tk.Frame(self.tab_flasher, bg="#263238", padx=10, pady=8)
        inst_card.pack(fill="x", pady=6)
        inst_txt = "PASU FISIKU: 1. Koneka kabu LAN husi PC ba LAN 1 (amarelu) | 2. Hanehan & tahan metin botau RESET | 3. Lakan modem | 4. Kuandu transfer hahu, sobu RESET!"
        tk.Label(inst_card, text=inst_txt, font=("Segoe UI", 8), fg="#b0bec5", bg="#263238", wraplength=760, justify="left").pack(anchor="w")

        # Log Output Box
        log_frame = tk.LabelFrame(self.tab_flasher, text="Log Komunikasaun CFE", font=("Segoe UI", 9, "bold"), fg=TEXT_COLOR, bg=PANEL_BG, padx=8, pady=6)
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(log_frame, bg="#0d0d0f", fg="#a7f3d0", font=("Consolas", 9), insertbackground=TEXT_COLOR)
        self.log_text.pack(fill="both", expand=True)

    def _browse_fw(self):
        f = filedialog.askopenfilename(filetypes=[("RBI Firmware", "*.rbi"), ("All Files", "*.*")])
        if f:
            self.entry_fw.delete(0, tk.END)
            self.entry_fw.insert(0, f)

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _toggle_server(self):
        if self.is_server_running:
            self.is_server_running = False
            self.btn_start.config(text="▶ HAHU RECOVERY SERVER", bg="#1b5e20")
            self.lbl_server_status.config(text="● Server Paradu", fg=TEXT_MUTED)
            self._log("[*] Server hapara husi utilizador.")
        else:
            fw = self.entry_fw.get().strip()
            if not os.path.exists(fw):
                messagebox.showerror("Erru", "Arkivu firmware la hetan! Favor hili arkivu .rbi ne'ebe loos.")
                return

            self.is_server_running = True
            self.btn_start.config(text="⏹ HAPARA SERVER", bg="#b71c1c")
            self.lbl_server_status.config(text="● Server Ativu (Hein Router...)", fg=ACCENT_GREEN)
            self._log(f"[*] Hahu BOOTP & TFTP Server iha {self.entry_ip.get()} ba arkivu {os.path.basename(fw)}...")

            self.server_thread = threading.Thread(target=self._run_server_worker, args=(self.entry_ip.get(), self.entry_clip.get(), fw))
            self.server_thread.daemon = True
            self.server_thread.start()

    def _run_server_worker(self, server_ip, client_ip, fw_path):
        # 1. Start TFTP listener
        try:
            self.tftp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.tftp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tftp_sock.bind((server_ip, 69))
        except Exception as e:
            self._log(f"[-] Erru loke porta TFTP UDP 69: {e}")
            self.is_server_running = False
            return

        # 2. Start BOOTP listener
        try:
            self.bootp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.bootp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.bootp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.bootp_sock.bind((server_ip, 67))
        except Exception as e:
            self._log(f"[-] Erru loke porta BOOTP UDP 67: {e}")
            self.is_server_running = False
            return

        boot_file_name = os.path.basename(fw_path)
        self._log("[✔] Portas UDP 67 & 69 prontu. Hanehan RESET no lakan modem agora!")

        # Thread for TFTP handling
        def tftp_worker():
            while self.is_server_running:
                try:
                    data, addr = self.tftp_sock.recvfrom(1024)
                    if not data: continue
                    op = struct.unpack("!H", data[:2])[0]
                    if op == 1: # RRQ
                        fn = data[2:].split(b'\x00')[0].decode('ascii', errors='ignore')
                        self._log(f"\n[+] Pedidu TFTP Read simu husi {addr}: '{fn}'")
                        self._serve_tftp_file(addr, fw_path)
                except:
                    break

        t_tftp = threading.Thread(target=tftp_worker)
        t_tftp.daemon = True
        t_tftp.start()

        # BOOTP loop
        while self.is_server_running:
            try:
                data, addr = self.bootp_sock.recvfrom(1024)
                if len(data) >= 236 and data[0] == 1:
                    xid = data[4:8]
                    chaddr = data[28:44]
                    mac = ":".join(f"{b:02x}" for b in chaddr[:6])
                    self._log(f"[+] Pedidu BOOTP detetadu husi Router MAC: {mac}")

                    reply = bytearray(300)
                    reply[0] = 2; reply[1] = 1; reply[2] = 6
                    reply[4:8] = xid
                    reply[16:20] = socket.inet_aton(client_ip)
                    reply[20:24] = socket.inet_aton(server_ip)
                    reply[28:44] = chaddr
                    b_name = boot_file_name.encode('ascii')
                    reply[108:108+len(b_name)] = b_name
                    reply[236:240] = b'\x63\x82\x53\x63'
                    opts = (
                        b'\x35\x01\x05' +
                        b'\x01\x04\xff\xff\xff\x00' +
                        b'\x42' + bytes([len(server_ip)]) + server_ip.encode('ascii') +
                        b'\x43' + bytes([len(b_name)]) + b_name +
                        b'\xff'
                    )
                    reply[240:240+len(opts)] = opts
                    self.bootp_sock.sendto(reply, ('<broadcast>', 68))
                    self._log("[+] Balasan BOOTP haruka ona ba router! Hein transferensia...")
            except:
                break

    def _serve_tftp_file(self, client_addr, fw_path):
        tsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tsock.settimeout(4.0)
        try:
            with open(fw_path, "rb") as f:
                block_num = 1
                total = os.path.getsize(fw_path)
                sent = 0
                self._log(f"[*] Hahu transfere {total} bytes...")
                while True:
                    chunk = f.read(512)
                    pkt = struct.pack("!HH", 3, block_num) + chunk
                    retries = 3
                    acked = False
                    while retries > 0:
                        tsock.sendto(pkt, client_addr)
                        try:
                            ack, _ = tsock.recvfrom(1024)
                            if len(ack) >= 4:
                                op, b = struct.unpack("!HH", ack[:4])
                                if op == 4 and b == block_num:
                                    acked = True
                                    break
                        except socket.timeout:
                            retries -= 1
                    if not acked:
                        self._log(f"[-] Transfer timeout iha block {block_num}")
                        return
                    sent += len(chunk)
                    if block_num % 1000 == 0 or len(chunk) < 512:
                        pct = (sent / total) * 100
                        self._log(f"    --> Progresu: {pct:.1f}% ({sent}/{total} bytes)")
                    if len(chunk) < 512:
                        self._log("[✔] Firmware 100% susesu haruka ba router!")
                        self._log("[!] KETA HAMATE ROUTER! Hein minutu 5-7 to'o prosesu burn NAND remata.")
                        break
                    block_num = (block_num + 1) & 0xFFFF
        except Exception as e:
            self._log(f"[-] Erru TFTP: {e}")
        finally:
            tsock.close()

    def _build_bank_tab(self):
        card = tk.LabelFrame(self.tab_bank, text="Asistente Bank Switch (LED Biru Timing)", font=("Segoe UI", 10, "bold"), fg=ACCENT_BLUE, bg=PANEL_BG, padx=15, pady=12)
        card.pack(fill="both", expand=True, pady=5)

        info = (
            "DJA0230 sei boot husi Bank 1 (Firmware 18.1.c foun) bainhira Bank 2 falla 3x tuir malu (bootfail).\n"
            "Momento ne'ebe diak liu atu dada sai power maka bainhira naroman LED BIRU hahu kedip (segundu 8-12).\n"
            "Uza asistente ne'e hodi konta tempu ho fasil:"
        )
        tk.Label(card, text=info, font=("Segoe UI", 9), fg=TEXT_COLOR, bg=PANEL_BG, justify="left").pack(anchor="w", pady=5)

        self.lbl_cycle = tk.Label(card, text="Siklu: 1 husi 3", font=("Segoe UI", 14, "bold"), fg=ACCENT_GREEN, bg=PANEL_BG)
        self.lbl_cycle.pack(pady=10)

        self.lbl_timer = tk.Label(card, text="00s", font=("Consolas", 36, "bold"), fg=ACCENT_BLUE, bg=PANEL_BG)
        self.lbl_timer.pack(pady=5)

        self.lbl_action = tk.Label(card, text="Hanehan 'Hahu Timer' bainhira lakan modem...", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=PANEL_BG)
        self.lbl_action.pack(pady=8)

        btn_box = tk.Frame(card, bg=PANEL_BG)
        btn_box.pack(pady=10)

        self.btn_bank_timer = tk.Button(btn_box, text="⏱ HAHU TIMER SIKLU", font=("Segoe UI", 11, "bold"), bg="#0277bd", fg="#ffffff", padx=15, pady=6, command=self._start_bank_timer)
        self.btn_bank_timer.pack(side="left", padx=5)

        btn_reset_bank = tk.Button(btn_box, text="Reset Siklu", font=("Segoe UI", 9), bg="#424242", fg=TEXT_COLOR, command=self._reset_bank_state)
        btn_reset_bank.pack(side="left", padx=5)

        self.current_bank_cycle = 1
        self.is_timer_running = False

    def _start_bank_timer(self):
        if self.is_timer_running: return
        self.is_timer_running = True
        self.lbl_action.config(text="Modem lakan hela... Hein LED Biru kedip...", fg="#fff59d")
        
        def run_clock():
            for s in range(1, 16):
                if not self.is_timer_running: break
                self.lbl_timer.config(text=f"{s:02d}s")
                if s == 9:
                    self.lbl_action.config(text="⚡ LED BIRU KEDIP AGORA! DADA SAI KABU POWER!", fg="#ff5252")
                time.sleep(1)
            
            if self.is_timer_running:
                self.is_timer_running = False
                if self.current_bank_cycle < 3:
                    self.current_bank_cycle += 1
                    self.lbl_cycle.config(text=f"Siklu: {self.current_bank_cycle} husi 3")
                    self.lbl_action.config(text="Kabu power dada sai ona. Hatama fali no hanehan Hahu Timer!", fg=TEXT_COLOR)
                else:
                    self.lbl_cycle.config(text="Siklu: Kompletu!")
                    self.lbl_action.config(text="✔ SIKLU 3X KOMPLETU! Hatama power no husik modem lakan to'o remata!", fg=ACCENT_GREEN)

        threading.Thread(target=run_clock, daemon=True).start()

    def _reset_bank_state(self):
        self.is_timer_running = False
        self.current_bank_cycle = 1
        self.lbl_cycle.config(text="Siklu: 1 husi 3")
        self.lbl_timer.config(text="00s")
        self.lbl_action.config(text="Hanehan 'Hahu Timer' bainhira lakan modem...", fg=TEXT_MUTED)

    def _build_guide_tab(self):
        txt_box = tk.Text(self.tab_guide, bg=PANEL_BG, fg=TEXT_COLOR, font=("Segoe UI", 9), padx=15, pady=15, wrap="word")
        txt_box.pack(fill="both", expand=True)

        guide = """GUIA HETAN ASESU ROOT (TCH-EXPLOIT):
--------------------------------------------------
Bainhira modem lakan ona iha firmware 18.1.c (Bank 1):
1. Muda kabu LAN husi PC ba porta WAN MERAH iha kotuk modem.
2. Konfigura IP PC Ethernet ba: 58.162.0.1 (Subnet: 255.255.255.0).
3. Loke terminal no halai 'tch-exploit':
   --> tch-exploit.exe
4. Hein to'o hetan mensajen susesu no password root sai 'root'.
5. Muda fali kabu LAN ba porta LAN AMARELU.
6. Agora bele loke programa 'Sagedral Installer' hodi instala Sagedral-Router V2!
"""
        txt_box.insert(tk.END, guide)
        txt_box.config(state="disabled")

if __name__ == "__main__":
    app = DowngradeToolGUI()
    app.mainloop()
